"""
Parallel Dispatcher - Manages concurrent worker streams
Located at: src/engine/dispatcher/ (per WIKI.md §2.2)
Primary Owner Agent: parallel-dispatcher

Manages concurrent worker streams within a single execution cycle.
All parallel threads are locked by default; enabled only when a 
Playbook step explicitly sets "concurrency": true.
"""

import threading
import queue
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class WorkerStatus(Enum):
    """Status of a worker thread"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class WorkerTask:
    """Represents a task to be executed by a worker"""
    task_id: str
    worker_id: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    status: WorkerStatus = WorkerStatus.IDLE
    result: Any = None
    error: Optional[str] = None
    completed_at: Optional[datetime] = None


@dataclass
class WorkerThread:
    """Represents a worker thread in the dispatcher pool"""
    worker_id: str
    thread: Optional[threading.Thread] = None
    status: WorkerStatus = WorkerStatus.IDLE
    current_task: Optional[WorkerTask] = None
    tasks_completed: int = 0
    last_active: Optional[datetime] = None


class ParallelDispatcher:
    """
    Parallel task dispatcher for managing concurrent worker streams.
    
    Responsibilities:
    - Manage a pool of worker threads
    - Dispatch tasks to available workers
    - Handle concurrency control based on playbook settings
    - Track worker status and task completion
    """
    
    def __init__(self, max_workers: int = 4, enable_parallel: bool = False):
        """
        Initialize the Parallel Dispatcher.
        
        Args:
            max_workers: Maximum number of concurrent worker threads
            enable_parallel: Whether parallel execution is enabled (default False per PROTOCOL.md)
        """
        self.max_workers = max_workers
        self.enable_parallel = enable_parallel
        self.workers: Dict[str, WorkerThread] = {}
        self.task_queue: queue.Queue = queue.Queue()
        self.result_queue: queue.Queue = queue.Queue()
        self._lock = threading.Lock()
        self._shutdown = False
        self._initialize_workers()
    
    def _initialize_workers(self) -> None:
        """Initialize the worker thread pool"""
        for i in range(self.max_workers):
            worker_id = f"worker-{i:03d}"
            worker = WorkerThread(worker_id=worker_id)
            self.workers[worker_id] = worker
    
    def start(self) -> bool:
        """
        Start all worker threads.
        
        Returns:
            True if started successfully, False if already running
        """
        if not self.enable_parallel:
            return False
        
        with self._lock:
            if any(w.thread is not None and w.thread.is_alive() for w in self.workers.values()):
                return False
            
            for worker in self.workers.values():
                worker.thread = threading.Thread(
                    target=self._worker_loop,
                    args=(worker,),
                    daemon=True
                )
                worker.thread.start()
                worker.status = WorkerStatus.IDLE
            
            return True
    
    def stop(self, timeout: float = 5.0) -> bool:
        """
        Stop all worker threads.
        
        Args:
            timeout: Maximum time to wait for workers to finish
            
        Returns:
            True if stopped successfully, False if timeout occurred
        """
        self._shutdown = True
        
        # Send stop signal to all workers
        for _ in self.workers:
            self.task_queue.put(None)
        
        # Wait for workers to finish
        success = True
        for worker in self.workers.values():
            if worker.thread and worker.thread.is_alive():
                worker.thread.join(timeout=timeout / len(self.workers))
                if worker.thread.is_alive():
                    success = False
        
        return success
    
    def _worker_loop(self, worker: WorkerThread) -> None:
        """
        Main loop for a worker thread.
        
        Args:
            worker: The worker thread instance
        """
        while not self._shutdown:
            try:
                task = self.task_queue.get(timeout=1.0)
                
                if task is None:
                    # Stop signal received
                    break
                
                # Execute the task
                worker.status = WorkerStatus.RUNNING
                worker.current_task = task
                worker.last_active = datetime.now()
                
                try:
                    result = task.func(*task.args, **task.kwargs)
                    task.result = result
                    task.status = WorkerStatus.COMPLETED
                    task.completed_at = datetime.now()
                    worker.tasks_completed += 1
                except Exception as e:
                    task.error = str(e)
                    task.status = WorkerStatus.FAILED
                    task.completed_at = datetime.now()
                
                # Put result in result queue
                self.result_queue.put(task)
                
            except queue.Empty:
                continue
            finally:
                worker.current_task = None
                worker.status = WorkerStatus.IDLE
                worker.last_active = datetime.now()
    
    def dispatch_task(
        self,
        task_id: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        worker_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Dispatch a task to a worker.
        
        Args:
            task_id: Unique identifier for the task
            func: Function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            worker_id: Specific worker to assign (optional)
            
        Returns:
            Assigned worker_id if successful, None if no workers available
        """
        if not self.enable_parallel:
            # Execute synchronously if parallel is disabled
            try:
                result = func(*args, **(kwargs or {}))
                self.result_queue.put(WorkerTask(
                    task_id=task_id,
                    worker_id="sync",
                    func=func,
                    args=args,
                    kwargs=kwargs or {},
                    status=WorkerStatus.COMPLETED,
                    result=result,
                    completed_at=datetime.now()
                ))
                return "sync"
            except Exception as e:
                self.result_queue.put(WorkerTask(
                    task_id=task_id,
                    worker_id="sync",
                    func=func,
                    args=args,
                    kwargs=kwargs or {},
                    status=WorkerStatus.FAILED,
                    error=str(e),
                    completed_at=datetime.now()
                ))
                return "sync"
        
        # Find an available worker
        with self._lock:
            if worker_id:
                worker = self.workers.get(worker_id)
                if worker and worker.status == WorkerStatus.IDLE:
                    pass
                else:
                    worker = None
            else:
                worker = next(
                    (w for w in self.workers.values() if w.status == WorkerStatus.IDLE),
                    None
                )
            
            if not worker:
                return None
            
            # Create and queue the task
            task = WorkerTask(
                task_id=task_id,
                worker_id=worker.worker_id,
                func=func,
                args=args,
                kwargs=kwargs or {}
            )
            
            worker.status = WorkerStatus.BLOCKED  # Temporarily blocked while queuing
            self.task_queue.put(task)
            
            return worker.worker_id
    
    def get_result(self, timeout: float = None) -> Optional[WorkerTask]:
        """
        Get a completed task result.
        
        Args:
            timeout: Maximum time to wait for a result
            
        Returns:
            Completed WorkerTask or None if timeout
        """
        try:
            return self.result_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_all_results(self) -> List[WorkerTask]:
        """Get all available completed results without blocking"""
        results = []
        while not self.result_queue.empty():
            results.append(self.result_queue.get_nowait())
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the dispatcher.
        
        Returns:
            Dictionary containing dispatcher status information
        """
        with self._lock:
            worker_statuses = {
                w.worker_id: {
                    "status": w.status.value,
                    "tasks_completed": w.tasks_completed,
                    "last_active": w.last_active.isoformat() if w.last_active else None
                }
                for w in self.workers.values()
            }
            
            return {
                "enabled": self.enable_parallel,
                "max_workers": self.max_workers,
                "active_workers": sum(1 for w in self.workers.values() if w.status == WorkerStatus.RUNNING),
                "idle_workers": sum(1 for w in self.workers.values() if w.status == WorkerStatus.IDLE),
                "queue_size": self.task_queue.qsize(),
                "results_pending": self.result_queue.qsize(),
                "workers": worker_statuses,
                "shutdown": self._shutdown
            }
    
    def enable_parallel_execution(self) -> bool:
        """Enable parallel execution mode"""
        if self.enable_parallel:
            return False
        self.enable_parallel = True
        return self.start()
    
    def disable_parallel_execution(self) -> bool:
        """Disable parallel execution mode"""
        if not self.enable_parallel:
            return False
        self.stop()
        self.enable_parallel = False
        return True


# Singleton instance
_dispatcher_instance: Optional[ParallelDispatcher] = None


def get_dispatcher(max_workers: int = 4, enable_parallel: bool = False) -> ParallelDispatcher:
    """Get or create the singleton dispatcher instance"""
    global _dispatcher_instance
    if _dispatcher_instance is None:
        _dispatcher_instance = ParallelDispatcher(max_workers, enable_parallel)
    return _dispatcher_instance
