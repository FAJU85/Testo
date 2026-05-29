"""
Internal Auditor - Scheduled sweep agent for detecting system drift
Located at: src/ops/audit/ (per WIKI.md §2.2)
Primary Owner Agent: internal-auditor

Detects "System Drift Exceptions" when manual developer commits bypass
the automated agent indexing loop. When drift is detected, locks all
active execution queues and initiates a full WIKI re-baseline.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class SystemDriftDetector:
    """Detects divergence between WIKI index and physical repository state"""
    
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)
        self.drift_log: List[Dict[str, Any]] = []
    
    def scan_directory(self, directory: Path) -> Dict[str, str]:
        """
        Scan a directory and calculate file hashes.
        
        Args:
            directory: Directory to scan
            
        Returns:
            Dictionary mapping file paths to their SHA256 hashes
        """
        file_hashes = {}
        for file_path in directory.rglob("*.py"):
            if "__pycache__" not in str(file_path):
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        rel_path = str(file_path.relative_to(self.workspace_root))
                        file_hashes[rel_path] = hashlib.sha256(content).hexdigest()
                except Exception as e:
                    continue
        return file_hashes
    
    def detect_drift(
        self,
        current_state: Dict[str, str],
        indexed_state: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Detect differences between current and indexed state.
        
        Args:
            current_state: Current file hashes
            indexed_state: Previously indexed file hashes
            
        Returns:
            List of drift events
        """
        drift_events = []
        
        # Check for modified files
        for file_path, current_hash in current_state.items():
            if file_path in indexed_state:
                if current_hash != indexed_state[file_path]:
                    drift_events.append({
                        "type": "MODIFIED",
                        "file": file_path,
                        "detected_at": datetime.now().isoformat(),
                        "severity": "MEDIUM"
                    })
            else:
                drift_events.append({
                    "type": "ADDED",
                    "file": file_path,
                    "detected_at": datetime.now().isoformat(),
                    "severity": "LOW"
                })
        
        # Check for deleted files
        for file_path in indexed_state:
            if file_path not in current_state:
                drift_events.append({
                    "type": "DELETED",
                    "file": file_path,
                    "detected_at": datetime.now().isoformat(),
                    "severity": "HIGH"
                })
        
        return drift_events


class InternalAuditor:
    """
    Internal Auditor agent for maintaining system integrity.
    
    Responsibilities:
    - Scheduled sweeps to detect System Drift Exceptions
    - Lock active execution queues when drift is detected
    - Initiate full WIKI re-baseline
    """
    
    def __init__(self, workspace_root: Optional[str] = None):
        """
        Initialize the Internal Auditor.
        
        Args:
            workspace_root: Root path of the workspace
        """
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        self.detector = SystemDriftDetector(str(self.workspace_root))
        self.last_audit: Optional[datetime] = None
        self.drift_exceptions: List[Dict[str, Any]] = []
        self.execution_queues_locked = False
    
    def perform_audit_sweep(self) -> Dict[str, Any]:
        """
        Perform a complete audit sweep of the workspace.
        
        Returns:
            Audit results including any detected drift
        """
        self.last_audit = datetime.now()
        
        # Scan current state
        current_state = self.detector.scan_directory(self.workspace_root / "src")
        
        # Load indexed state from WIKI or cache
        indexed_state = self._load_indexed_state()
        
        # Detect drift
        drift_events = self.detector.detect_drift(current_state, indexed_state)
        
        result = {
            "audit_timestamp": self.last_audit.isoformat(),
            "files_scanned": len(current_state),
            "drift_detected": len(drift_events) > 0,
            "drift_count": len(drift_events),
            "drift_events": drift_events
        }
        
        if drift_events:
            self.drift_exceptions.extend(drift_events)
            result["action_taken"] = self._handle_drift_exception(drift_events)
        else:
            result["action_taken"] = "none"
        
        return result
    
    def _load_indexed_state(self) -> Dict[str, str]:
        """Load the previously indexed state from disk"""
        index_file = self.workspace_root / ".wiki_index_cache.json"
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def _save_indexed_state(self, state: Dict[str, str]) -> None:
        """Save the current state as the new indexed baseline"""
        index_file = self.workspace_root / ".wiki_index_cache.json"
        with open(index_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def _handle_drift_exception(self, drift_events: List[Dict[str, Any]]) -> str:
        """
        Handle detected drift exceptions.
        
        Args:
            drift_events: List of detected drift events
            
        Returns:
            Description of action taken
        """
        # Lock execution queues
        self.execution_queues_locked = True
        
        # Determine severity
        high_severity = any(e.get("severity") == "HIGH" for e in drift_events)
        
        if high_severity:
            # Initiate full WIKI re-baseline
            return "CRITICAL: Execution queues locked. Full WIKI re-baseline initiated."
        else:
            return "WARNING: Execution queues locked. Incremental WIKI update required."
    
    def unlock_execution_queues(self) -> bool:
        """Unlock execution queues after drift resolution"""
        if not self.execution_queues_locked:
            return False
        self.execution_queues_locked = False
        return True
    
    def regenerate_wiki_baseline(self) -> Dict[str, Any]:
        """
        Regenerate the complete WIKI index from scratch.
        
        Returns:
            Result of the regeneration process
        """
        # Scan entire workspace
        new_index = self.detector.scan_directory(self.workspace_root / "src")
        
        # Save as new baseline
        self._save_indexed_state(new_index)
        
        # Clear drift exceptions
        self.drift_exceptions = []
        
        # Unlock queues
        self.unlock_execution_queues()
        
        return {
            "status": "completed",
            "files_indexed": len(new_index),
            "timestamp": datetime.now().isoformat()
        }


# Singleton instance
_auditor_instance: Optional[InternalAuditor] = None

def get_auditor(workspace_root: Optional[str] = None) -> InternalAuditor:
    """Get or create the singleton auditor instance"""
    global _auditor_instance
    if _auditor_instance is None:
        _auditor_instance = InternalAuditor(workspace_root)
    return _auditor_instance
