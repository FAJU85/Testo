"""
SDLC Orchestrator - Top-level lifecycle controller
Located at: src/engine/sdlc/ (per WIKI.md §2.2)
Primary Owner Agent: sdlc-orchestrator

Owns the execution lock, enforces atomic sync loops after every cycle,
and triggers the WIKI re-indexing pipeline.
"""

import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime


class ExecutionLock:
    """System-wide mutex for execution control"""
    
    def __init__(self):
        self._locked = False
        self._locked_at: Optional[datetime] = None
        self._owner: Optional[str] = None
    
    def acquire(self, owner: str) -> bool:
        """Acquire the execution lock"""
        if self._locked:
            return False
        self._locked = True
        self._locked_at = datetime.now()
        self._owner = owner
        return True
    
    def release(self) -> bool:
        """Release the execution lock"""
        if not self._locked:
            return False
        self._locked = False
        self._locked_at = None
        self._owner = None
        return True
    
    @property
    def is_locked(self) -> bool:
        return self._locked
    
    @property
    def owner(self) -> Optional[str]:
        return self._owner


class SDLCOrchestrator:
    """
    Top-level lifecycle controller for the Hermes Multi-Agent System.
    
    Responsibilities:
    - Owns the execution lock
    - Enforces atomic sync loops after every cycle
    - Triggers the WIKI re-indexing pipeline
    - Only agent authorized to free execution locks
    """
    
    def __init__(self, workspace_root: Optional[str] = None):
        """
        Initialize the SDLC Orchestrator.
        
        Args:
            workspace_root: Root path of the workspace. Defaults to current directory.
        """
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        self.execution_lock = ExecutionLock()
        self.current_cycle_id: Optional[str] = None
        self.mutation_log: List[Dict[str, Any]] = []
    
    def start_execution_cycle(self, task_id: str, agent_name: str) -> bool:
        """
        Start a new execution cycle.
        
        Args:
            task_id: Unique identifier for the task
            agent_name: Name of the agent requesting execution
            
        Returns:
            True if cycle started successfully, False if lock unavailable
        """
        if not self.execution_lock.acquire(agent_name):
            return False
        
        self.current_cycle_id = f"{task_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.mutation_log = []
        return True
    
    def log_mutation(self, file_path: str, action: str, details: Dict[str, Any]) -> None:
        """
        Log a file mutation during the execution cycle.
        
        Args:
            file_path: Path to the mutated file
            action: Type of action (CREATE, MODIFY, DELETE)
            details: Additional details about the mutation
        """
        self.mutation_log.append({
            "file": file_path,
            "action": action,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def complete_execution_cycle(self, success: bool) -> Dict[str, Any]:
        """
        Complete the execution cycle and trigger sync loop if successful.
        
        Args:
            success: Whether the cycle completed successfully
            
        Returns:
            Summary of the execution cycle
        """
        result = {
            "cycle_id": self.current_cycle_id,
            "success": success,
            "mutations_count": len(self.mutation_log),
            "mutations": self.mutation_log
        }
        
        if success and self.mutation_log:
            # Trigger WIKI re-indexing
            result["wiki_sync_triggered"] = True
            result["wiki_sync_result"] = self._trigger_wiki_sync()
        else:
            result["wiki_sync_triggered"] = False
        
        # Always release the lock
        self.execution_lock.release()
        self.current_cycle_id = None
        
        return result
    
    def _trigger_wiki_sync(self) -> Dict[str, Any]:
        """
        Trigger the WIKI re-indexing pipeline.
        
        Returns:
            Result of the sync operation
        """
        # This would integrate with changelog-writer and technical-writer agents
        # For now, return a placeholder response
        return {
            "status": "completed",
            "files_mutated": [m["file"] for m in self.mutation_log],
            "timestamp": datetime.now().isoformat()
        }
    
    def calculate_diff_hash(self, files_mutated: List[str]) -> str:
        """
        Calculate a hash of the diff for validation purposes.
        
        Args:
            files_mutated: List of mutated file paths
            
        Returns:
            SHA256 hash of the mutation list
        """
        mutation_str = json.dumps(sorted(files_mutated))
        return hashlib.sha256(mutation_str.encode()).hexdigest()
    
    def validate_approved_file_set(
        self,
        approved_files: List[str],
        mutated_files: List[str]
    ) -> Dict[str, Any]:
        """
        Validate that mutations stayed within the approved file set.
        
        Args:
            approved_files: List of approved file paths
            mutated_files: List of actually mutated file paths
            
        Returns:
            Validation result with any violations
        """
        approved_set = set(approved_files)
        mutated_set = set(mutated_files)
        
        violations = mutated_set - approved_set
        
        return {
            "valid": len(violations) == 0,
            "violations": list(violations),
            "approved_count": len(approved_set),
            "mutated_count": len(mutated_set)
        }


# Singleton instance
_orchestrator_instance: Optional[SDLCOrchestrator] = None

def get_orchestrator(workspace_root: Optional[str] = None) -> SDLCOrchestrator:
    """Get or create the singleton orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = SDLCOrchestrator(workspace_root)
    return _orchestrator_instance
