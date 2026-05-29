"""
Hermes Multi-Agent System - Core State Engine
Manages user session state and context across all integration tracks.
"""

import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class StateManifest(BaseModel):
    """Represents the state manifest for a user session."""
    lastCommitHash: str
    pendingSync: bool = False


class UserSessionContext(BaseModel):
    """
    Core user session schema as defined in WIKI.md §3.1
    This is the absolute Pydantic/JSON layout mapping ctx.user_data
    """
    schemaVersion: str = Field(
        ...,
        description="Semantic version of this schema. Must be incremented on any structural change.",
        pattern=r"^\d+\.\d+\.\d+$"
    )
    userId: str
    activeTrack: str
    securityTier: int = Field(..., ge=1, le=3)
    stateManifest: StateManifest

    @classmethod
    def validate_semver(cls, v: str) -> str:
        """Validate that schemaVersion follows semver format."""
        import re
        if not re.match(r'^\d+\.\d+\.\d+$', v):
            raise ValueError("schemaVersion must be in semver format (e.g., 1.0.0)")
        return v

    model_config = {
        "json_schema_extra": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "UserSessionContext"
        }
    }


class StateEngine:
    """
    Core state engine for managing user sessions.
    Located at: src/core/state/ (per WIKI.md §2.2)
    Primary Owner Agent: database-expert
    """

    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize the state engine.
        
        Args:
            schema_path: Path to the JSON schema file. Defaults to src/core/schemas/state.json
        """
        self.schema_path = Path(schema_path) if schema_path else Path(__file__).parent.parent / "schemas" / "state.json"
        self._schema: Optional[Dict[str, Any]] = None
        self._load_schema()

    def _load_schema(self) -> None:
        """Load the JSON schema from disk."""
        try:
            with open(self.schema_path, 'r') as f:
                self._schema = json.load(f)
        except FileNotFoundError:
            raise RuntimeError(f"Schema file not found at {self.schema_path}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON in schema file: {e}")

    def create_session(
        self,
        user_id: str,
        active_track: str = "default",
        security_tier: int = 1,
        initial_commit_hash: str = ""
    ) -> UserSessionContext:
        """
        Create a new user session context.
        
        Args:
            user_id: Unique identifier for the user
            active_track: Current active track/module
            security_tier: Security tier level (1-3)
            initial_commit_hash: Initial git commit hash
            
        Returns:
            UserSessionContext instance
        """
        return UserSessionContext(
            schemaVersion="1.0.0",
            userId=user_id,
            activeTrack=active_track,
            securityTier=security_tier,
            stateManifest=StateManifest(
                lastCommitHash=initial_commit_hash,
                pendingSync=False
            )
        )

    def update_commit_hash(self, session: UserSessionContext, commit_hash: str) -> UserSessionContext:
        """
        Update the last commit hash in the state manifest.
        
        Args:
            session: Current user session
            commit_hash: New commit hash
            
        Returns:
            Updated UserSessionContext
        """
        session.stateManifest.lastCommitHash = commit_hash
        session.stateManifest.pendingSync = False
        return session

    def mark_pending_sync(self, session: UserSessionContext) -> UserSessionContext:
        """Mark the session as pending synchronization."""
        session.stateManifest.pendingSync = True
        return session

    def validate_session(self, session_data: Dict[str, Any]) -> bool:
        """
        Validate session data against the schema.
        
        Args:
            session_data: Dictionary containing session data
            
        Returns:
            True if valid, raises ValueError otherwise
        """
        try:
            UserSessionContext(**session_data)
            return True
        except Exception as e:
            raise ValueError(f"Session validation failed: {e}")

    def get_schema_version(self) -> str:
        """Get the current schema version."""
        return self._schema.get("properties", {}).get("schemaVersion", {}).get("default", "1.0.0")

    def calculate_state_hash(self, session: UserSessionContext) -> str:
        """
        Calculate a hash of the current state for integrity verification.
        
        Args:
            session: User session to hash
            
        Returns:
            SHA256 hash of the session state
        """
        state_dict = session.model_dump()
        state_str = json.dumps(state_dict, sort_keys=True)
        return hashlib.sha256(state_str.encode()).hexdigest()
