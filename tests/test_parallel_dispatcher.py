"""
Test suite for Parallel Dispatcher
Tests worker thread management, task dispatching, and concurrency control
"""

import pytest
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from engine.dispatcher.parallel_dispatcher import (
    ParallelDispatcher,
    WorkerStatus,
    WorkerTask,
    get_dispatcher
)


def sample_task(x: int, y: int) -> int:
    """Sample task function for testing"""
    return x + y


def slow_task(seconds: float) -> str:
    """Task that takes time to complete"""
    time.sleep(seconds)
    return f"slept {seconds}s"


def failing_task() -> None:
    """Task that always fails"""
    raise ValueError("Intentional failure")


class TestWorkerStatus:
    """Test WorkerStatus enum"""
    
    def test_status_values(self):
        """Test that all status values exist"""
        assert WorkerStatus.IDLE.value == "idle"
        assert WorkerStatus.RUNNING.value == "running"
        assert WorkerStatus.COMPLETED.value == "completed"
        assert WorkerStatus.FAILED.value == "failed"
        assert WorkerStatus.BLOCKED.value == "blocked"


class TestParallelDispatcherDisabled:
    """Test dispatcher with parallel execution disabled (default)"""
    
    def test_create_dispatcher_disabled(self):
        """Test creating a disabled dispatcher"""
        dispatcher = ParallelDispatcher(enable_parallel=False)
        assert dispatcher.enable_parallel is False
        assert dispatcher.max_workers == 4
    
    def test_sync_execution(self):
        """Test synchronous task execution"""
        dispatcher = ParallelDispatcher(enable_parallel=False)
        worker_id = dispatcher.dispatch_task("task-001", sample_task, args=(2, 3))
        
        assert worker_id == "sync"
        
        result = dispatcher.get_result(timeout=1.0)
        assert result is not None
        assert result.status == WorkerStatus.COMPLETED
        assert result.result == 5
    
    def test_sync_execution_with_exception(self):
        """Test synchronous execution with exception handling"""
        dispatcher = ParallelDispatcher(enable_parallel=False)
        worker_id = dispatcher.dispatch_task("task-002", failing_task)
        
        assert worker_id == "sync"
        
        result = dispatcher.get_result(timeout=1.0)
        assert result is not None
        assert result.status == WorkerStatus.FAILED
        assert "Intentional failure" in result.error


class TestParallelDispatcherEnabled:
    """Test dispatcher with parallel execution enabled"""
    
    def test_create_dispatcher_enabled(self):
        """Test creating an enabled dispatcher"""
        dispatcher = ParallelDispatcher(max_workers=2, enable_parallel=True)
        assert dispatcher.enable_parallel is True
        assert dispatcher.max_workers == 2
    
    def test_start_dispatcher(self):
        """Test starting the dispatcher"""
        dispatcher = ParallelDispatcher(max_workers=2, enable_parallel=True)
        result = dispatcher.start()
        assert result is True
        
        status = dispatcher.get_status()
        assert status["enabled"] is True
        assert status["idle_workers"] == 2
    
    def test_cannot_start_twice(self):
        """Test that dispatcher cannot be started twice"""
        dispatcher = ParallelDispatcher(max_workers=2, enable_parallel=True)
        assert dispatcher.start() is True
        assert dispatcher.start() is False
    
    def test_dispatch_parallel_task(self):
        """Test dispatching a task to parallel workers"""
        dispatcher = ParallelDispatcher(max_workers=2, enable_parallel=True)
        dispatcher.start()
        
        worker_id = dispatcher.dispatch_task("task-001", sample_task, args=(5, 7))
        assert worker_id is not None
        assert worker_id.startswith("worker-")
        
        # Wait for task completion
        time.sleep(0.5)
        result = dispatcher.get_result(timeout=1.0)
        assert result is not None
        assert result.status == WorkerStatus.COMPLETED
        assert result.result == 12
        
        dispatcher.stop()
    
    def test_parallel_execution(self):
        """Test true parallel execution of multiple tasks"""
        dispatcher = ParallelDispatcher(max_workers=2, enable_parallel=True)
        dispatcher.start()
        
        start_time = time.time()
        
        # Dispatch two slow tasks that should run in parallel
        dispatcher.dispatch_task("task-001", slow_task, args=(0.3,))
        dispatcher.dispatch_task("task-002", slow_task, args=(0.3,))
        
        # Collect results
        results = []
        for _ in range(2):
            result = dispatcher.get_result(timeout=2.0)
            if result:
                results.append(result)
        
        elapsed = time.time() - start_time
        
        # If truly parallel, should take ~0.3s, not ~0.6s
        assert elapsed < 0.5, f"Tasks did not run in parallel: {elapsed}s"
        assert len(results) == 2
        assert all(r.status == WorkerStatus.COMPLETED for r in results)
        
        dispatcher.stop()
    
    def test_worker_exhaustion(self):
        """Test behavior when all workers are busy"""
        dispatcher = ParallelDispatcher(max_workers=1, enable_parallel=True)
        dispatcher.start()
        
        # Dispatch a slow task
        dispatcher.dispatch_task("task-001", slow_task, args=(0.5,))
        
        # Try to dispatch another task immediately - should return None
        worker_id = dispatcher.dispatch_task("task-002", sample_task, args=(1, 2))
        assert worker_id is None
        
        # Wait for first task to complete
        time.sleep(0.6)
        dispatcher.get_result()
        
        # Now should be able to dispatch
        worker_id = dispatcher.dispatch_task("task-003", sample_task, args=(3, 4))
        assert worker_id is not None
        
        dispatcher.stop()
    
    def test_stop_dispatcher(self):
        """Test stopping the dispatcher"""
        dispatcher = ParallelDispatcher(max_workers=2, enable_parallel=True)
        dispatcher.start()
        
        assert dispatcher.stop() is True
        
        status = dispatcher.get_status()
        assert status["shutdown"] is True


class TestDispatcherStatus:
    """Test dispatcher status reporting"""
    
    def test_get_status(self):
        """Test getting dispatcher status"""
        dispatcher = ParallelDispatcher(max_workers=3, enable_parallel=False)
        status = dispatcher.get_status()
        
        assert status["enabled"] is False
        assert status["max_workers"] == 3
        assert status["active_workers"] == 0
        # Workers are initialized but not running when parallel is disabled
        assert status["idle_workers"] == 3
    
    def test_status_after_tasks(self):
        """Test status after executing tasks"""
        dispatcher = ParallelDispatcher(enable_parallel=False)
        
        # Execute some tasks
        for i in range(5):
            dispatcher.dispatch_task(f"task-{i}", sample_task, args=(i, i))
            dispatcher.get_result()
        
        status = dispatcher.get_status()
        # Results are consumed immediately in sync mode
        assert status["results_pending"] == 0


class TestSingletonPattern:
    """Test singleton pattern for dispatcher"""
    
    def test_singleton_instance(self):
        """Test that get_dispatcher returns same instance"""
        # Reset singleton
        import engine.dispatcher.parallel_dispatcher as module
        module._dispatcher_instance = None
        
        disp1 = get_dispatcher()
        disp2 = get_dispatcher()
        assert disp1 is disp2
    
    def test_singleton_with_params(self):
        """Test singleton respects initial parameters"""
        import engine.dispatcher.parallel_dispatcher as module
        module._dispatcher_instance = None
        
        disp = get_dispatcher(max_workers=8)
        assert disp.max_workers == 8


class TestEnableDisableToggle:
    """Test enabling and disabling parallel execution"""
    
    def test_enable_parallel(self):
        """Test enabling parallel execution"""
        dispatcher = ParallelDispatcher(enable_parallel=False)
        assert dispatcher.enable_parallel is False
        
        result = dispatcher.enable_parallel_execution()
        # Enabling parallel execution returns True and starts the workers
        assert result is True
        assert dispatcher.enable_parallel is True
        
        # Clean up
        dispatcher.stop()
    
    def test_disable_parallel(self):
        """Test disabling parallel execution"""
        dispatcher = ParallelDispatcher(max_workers=2, enable_parallel=True)
        dispatcher.start()
        
        result = dispatcher.disable_parallel_execution()
        assert result is True
        assert dispatcher.enable_parallel is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
