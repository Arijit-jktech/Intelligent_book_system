"""
Background Task Queue
In-memory task queue for async operations like LLM calls.
"""

import uuid
import asyncio
import logging
from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Coroutine
from dataclasses import dataclass, asdict

from app.core.structured_logging import get_logger

logger = get_logger(__name__)


class TaskStatus(str, Enum):
    """Task execution states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BackgroundTask:
    """Represents a background task execution."""
    
    task_id: str
    task_type: str
    data: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize timestamps."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    async def execute(self, executor: Callable) -> None:
        """
        Execute the background task.
        
        Args:
            executor: Async function to execute task
        """
        try:
            self.status = TaskStatus.RUNNING
            self.started_at = datetime.utcnow()
            
            logger.info_with_context(
                f"Starting task {self.task_id} (type: {self.task_type})"
            )
            
            # Execute the task
            self.result = await executor(self.data)
            self.status = TaskStatus.COMPLETED
            
            logger.info_with_context(
                f"Task {self.task_id} completed successfully",
                task_id=self.task_id,
                task_type=self.task_type
            )
            
        except asyncio.CancelledError:
            self.status = TaskStatus.CANCELLED
            logger.warning_with_context(
                f"Task {self.task_id} was cancelled",
                task_id=self.task_id
            )
            
        except Exception as e:
            self.status = TaskStatus.FAILED
            self.error = str(e)
            
            logger.error_with_context(
                f"Task {self.task_id} failed: {str(e)[:200]}",
                task_id=self.task_id,
                task_type=self.task_type,
                error=str(e)[:200]
            )
        
        finally:
            self.completed_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        data = asdict(self)
        # Convert enums and datetimes to strings
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data


class BackgroundTaskQueue:
    """In-memory queue for background async tasks."""
    
    def __init__(self, max_tasks: int = 1000, cleanup_completed: bool = True):
        """
        Initialize task queue.
        
        Args:
            max_tasks: Maximum tasks to keep in memory
            cleanup_completed: Auto-cleanup completed tasks after period
        """
        self.tasks: Dict[str, BackgroundTask] = {}
        self.lock = asyncio.Lock()
        self.max_tasks = max_tasks
        self.cleanup_completed = cleanup_completed
        self.executors: Dict[str, Callable] = {}
    
    def register_executor(self, task_type: str, executor: Callable[[Dict[str, Any]], Coroutine]) -> None:
        """
        Register an executor function for a task type.
        
        Args:
            task_type: Type identifier for the task
            executor: Async function that takes data dict and returns result
        """
        if not asyncio.iscoroutinefunction(executor):
            raise ValueError(f"Executor must be async function, got {executor}")
        
        self.executors[task_type] = executor
        logger.info_with_context(
            f"Registered executor for task type: {task_type}"
        )
    
    async def submit(self, task_type: str, data: Dict[str, Any]) -> str:
        """
        Submit a background task.
        
        Args:
            task_type: Type of task to execute
            data: Data to pass to executor
        
        Returns:
            task_id for tracking
        
        Raises:
            ValueError: If task_type not registered
            RuntimeError: If queue is full
        """
        if task_type not in self.executors:
            raise ValueError(f"Unknown task type: {task_type}")
        
        if len(self.tasks) >= self.max_tasks:
            # Clean up old completed tasks
            await self._cleanup_old_tasks()
            
            if len(self.tasks) >= self.max_tasks:
                raise RuntimeError("Task queue is full")
        
        task_id = str(uuid.uuid4())
        task = BackgroundTask(task_id, task_type, data)
        
        async with self.lock:
            self.tasks[task_id] = task
        
        # Execute task in background (don't await)
        executor = self.executors[task_type]
        asyncio.create_task(task.execute(executor))
        
        logger.info_with_context(
            f"Task submitted: {task_id} (type: {task_type})"
        )
        
        return task_id
    
    async def get_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get task status and result.
        
        Args:
            task_id: ID of task to check
        
        Returns:
            Task status dict
        
        Raises:
            ValueError: If task not found
        """
        async with self.lock:
            if task_id not in self.tasks:
                raise ValueError(f"Task not found: {task_id}")
            task = self.tasks[task_id]
        
        return task.to_dict()
    
    async def cancel_task(self, task_id: str) -> None:
        """
        Cancel a pending or running task.
        
        Args:
            task_id: ID of task to cancel
        
        Raises:
            ValueError: If task not found
        """
        async with self.lock:
            if task_id not in self.tasks:
                raise ValueError(f"Task not found: {task_id}")
            
            task = self.tasks[task_id]
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                raise ValueError(f"Cannot cancel completed task: {task_id}")
            
            task.status = TaskStatus.CANCELLED
        
        logger.info_with_context(
            f"Task cancelled: {task_id}"
        )
    
    async def list_tasks(
        self, 
        status: Optional[TaskStatus] = None,
        task_type: Optional[str] = None,
        limit: int = 100
    ) -> list[Dict[str, Any]]:
        """
        List tasks with optional filtering.
        
        Args:
            status: Filter by status
            task_type: Filter by task type
            limit: Maximum tasks to return
        
        Returns:
            List of task dicts
        """
        async with self.lock:
            tasks = list(self.tasks.values())
        
        # Filter
        if status:
            tasks = [t for t in tasks if t.status == status]
        if task_type:
            tasks = [t for t in tasks if t.task_type == task_type]
        
        # Sort by created_at descending
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        # Limit
        tasks = tasks[:limit]
        
        return [t.to_dict() for t in tasks]
    
    async def _cleanup_old_tasks(self, max_age_seconds: int = 3600) -> None:
        """
        Remove old completed tasks to free memory.
        
        Args:
            max_age_seconds: Age in seconds before cleanup
        """
        now = datetime.utcnow()
        to_remove = []
        
        async with self.lock:
            for task_id, task in self.tasks.items():
                if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                    if task.completed_at:
                        age = (now - task.completed_at).total_seconds()
                        if age > max_age_seconds:
                            to_remove.append(task_id)
        
        if to_remove:
            async with self.lock:
                for task_id in to_remove:
                    del self.tasks[task_id]
            
            logger.info_with_context(
                f"Cleaned up {len(to_remove)} old tasks"
            )
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        async with self.lock:
            tasks = list(self.tasks.values())
        
        stats = {
            "total_tasks": len(tasks),
            "pending": sum(1 for t in tasks if t.status == TaskStatus.PENDING),
            "running": sum(1 for t in tasks if t.status == TaskStatus.RUNNING),
            "completed": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in tasks if t.status == TaskStatus.FAILED),
            "cancelled": sum(1 for t in tasks if t.status == TaskStatus.CANCELLED),
            "task_types": list(set(t.task_type for t in tasks)),
        }
        return stats


# Global task queue instance
_task_queue: Optional[BackgroundTaskQueue] = None


def get_task_queue() -> BackgroundTaskQueue:
    """Get or create global task queue."""
    global _task_queue
    if _task_queue is None:
        _task_queue = BackgroundTaskQueue()
    return _task_queue


def initialize_task_queue(queue: Optional[BackgroundTaskQueue] = None) -> BackgroundTaskQueue:
    """
    Initialize the global task queue.
    
    Args:
        queue: Optional custom queue instance
    
    Returns:
        The initialized queue
    """
    global _task_queue
    _task_queue = queue or BackgroundTaskQueue()
    return _task_queue


__all__ = [
    'TaskStatus',
    'BackgroundTask',
    'BackgroundTaskQueue',
    'get_task_queue',
    'initialize_task_queue',
]
