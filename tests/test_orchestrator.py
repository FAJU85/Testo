"""
Test suite for SDLC Orchestrator
Tests execution lock, mutation logging, and file set validation
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from engine.sdlc.orchestrator import ExecutionLock, SDLCOrchestrator, get_orchestrator


class TestExecutionLock:
    """Test ExecutionLock class"""
    
    def test_acquire_lock(self):
        """Test acquiring an unlocked lock"""
        lock = ExecutionLock()
        assert lock.acquire("agent-1") is True
        assert lock.is_locked is True
        assert lock.owner == "agent-1"
    
    def test_cannot_acquire_locked(self):
        """Test that a locked lock cannot be acquired"""
        lock = ExecutionLock()
        assert lock.acquire("agent-1") is True
        assert lock.acquire("agent-2") is False
        assert lock.owner == "agent-1"
    
    def test_release_lock(self):
        """Test releasing a lock"""
        lock = ExecutionLock()
        lock.acquire("agent-1")
        assert lock.release() is True
        assert lock.is_locked is False
        assert lock.owner is None
    
    def test_cannot_release_unlocked(self):
        """Test that an unlocked lock cannot be released"""
        lock = ExecutionLock()
        assert lock.release() is False


class TestSDLCOrchestrator:
    """Test SDLCOrchestrator class"""
    
    def test_create_orchestrator(self):
        """Test creating an orchestrator"""
        orch = SDLCOrchestrator()
        assert orch is not None
        assert orch.execution_lock is not None
    
    def test_start_execution_cycle(self):
        """Test starting an execution cycle"""
        orch = SDLCOrchestrator()
        result = orch.start_execution_cycle("task-001", "layer3-development")
        assert result is True
        assert orch.current_cycle_id is not None
        assert orch.execution_lock.is_locked is True
    
    def test_cannot_start_concurrent_cycles(self):
        """Test that concurrent cycles are prevented"""
        orch = SDLCOrchestrator()
        assert orch.start_execution_cycle("task-001", "agent-1") is True
        assert orch.start_execution_cycle("task-002", "agent-2") is False
    
    def test_log_mutation(self):
        """Test logging mutations"""
        orch = SDLCOrchestrator()
        orch.start_execution_cycle("task-001", "builder")
        orch.log_mutation("src/main.py", "MODIFY", {"lines_added": 10})
        assert len(orch.mutation_log) == 1
        assert orch.mutation_log[0]["file"] == "src/main.py"
        assert orch.mutation_log[0]["action"] == "MODIFY"
    
    def test_complete_cycle_success(self):
        """Test completing a successful cycle"""
        orch = SDLCOrchestrator()
        orch.start_execution_cycle("task-001", "builder")
        orch.log_mutation("src/main.py", "CREATE", {})
        
        result = orch.complete_execution_cycle(success=True)
        
        assert result["success"] is True
        assert result["mutations_count"] == 1
        assert result["wiki_sync_triggered"] is True
        assert orch.execution_lock.is_locked is False
        assert orch.current_cycle_id is None
    
    def test_complete_cycle_failure(self):
        """Test completing a failed cycle"""
        orch = SDLCOrchestrator()
        orch.start_execution_cycle("task-001", "builder")
        orch.log_mutation("src/main.py", "MODIFY", {})
        
        result = orch.complete_execution_cycle(success=False)
        
        assert result["success"] is False
        assert result["wiki_sync_triggered"] is False
        assert orch.execution_lock.is_locked is False
    
    def test_validate_approved_file_set_valid(self):
        """Test validation with valid mutations"""
        orch = SDLCOrchestrator()
        approved = ["src/main.py", "src/utils.py"]
        mutated = ["src/main.py"]
        
        result = orch.validate_approved_file_set(approved, mutated)
        
        assert result["valid"] is True
        assert len(result["violations"]) == 0
    
    def test_validate_approved_file_set_invalid(self):
        """Test validation with unauthorized mutations"""
        orch = SDLCOrchestrator()
        approved = ["src/main.py"]
        mutated = ["src/main.py", "src/unauthorized.py"]
        
        result = orch.validate_approved_file_set(approved, mutated)
        
        assert result["valid"] is False
        assert "src/unauthorized.py" in result["violations"]
    
    def test_calculate_diff_hash(self):
        """Test diff hash calculation"""
        orch = SDLCOrchestrator()
        files1 = ["src/a.py", "src/b.py"]
        files2 = ["src/a.py", "src/b.py"]
        files3 = ["src/c.py"]
        
        hash1 = orch.calculate_diff_hash(files1)
        hash2 = orch.calculate_diff_hash(files2)
        hash3 = orch.calculate_diff_hash(files3)
        
        assert hash1 == hash2  # Same files = same hash
        assert hash1 != hash3  # Different files = different hash
    
    def test_singleton_pattern(self):
        """Test the singleton pattern for orchestrator"""
        orch1 = get_orchestrator()
        orch2 = get_orchestrator()
        assert orch1 is orch2  # Should be same instance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
