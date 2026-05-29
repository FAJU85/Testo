"""
Test suite for Core State Engine
Tests the UserSessionContext and StateEngine classes
"""

import pytest
import json
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.state.session_model import UserSessionContext, StateManifest, StateEngine


class TestStateManifest:
    """Test StateManifest model"""
    
    def test_create_manifest(self):
        """Test creating a state manifest"""
        manifest = StateManifest(lastCommitHash="abc123")
        assert manifest.lastCommitHash == "abc123"
        assert manifest.pendingSync is False
    
    def test_manifest_with_pending_sync(self):
        """Test manifest with pending sync flag"""
        manifest = StateManifest(lastCommitHash="def456", pendingSync=True)
        assert manifest.pendingSync is True


class TestUserSessionContext:
    """Test UserSessionContext model"""
    
    def test_create_valid_session(self):
        """Test creating a valid session"""
        session = UserSessionContext(
            schemaVersion="1.0.0",
            userId="user-123",
            activeTrack="development",
            securityTier=1,
            stateManifest=StateManifest(lastCommitHash="abc123")
        )
        assert session.userId == "user-123"
        assert session.schemaVersion == "1.0.0"
        assert session.securityTier == 1
    
    def test_invalid_schema_version(self):
        """Test that invalid schema versions are rejected"""
        with pytest.raises(ValueError):
            UserSessionContext(
                schemaVersion="invalid",
                userId="user-123",
                activeTrack="dev",
                securityTier=1,
                stateManifest=StateManifest(lastCommitHash="abc")
            )
    
    def test_security_tier_bounds(self):
        """Test security tier validation"""
        # Valid tiers
        for tier in [1, 2, 3]:
            session = UserSessionContext(
                schemaVersion="1.0.0",
                userId="user-123",
                activeTrack="dev",
                securityTier=tier,
                stateManifest=StateManifest(lastCommitHash="abc")
            )
            assert session.securityTier == tier
        
        # Invalid tiers
        with pytest.raises(Exception):
            UserSessionContext(
                schemaVersion="1.0.0",
                userId="user-123",
                activeTrack="dev",
                securityTier=0,
                stateManifest=StateManifest(lastCommitHash="abc")
            )
        
        with pytest.raises(Exception):
            UserSessionContext(
                schemaVersion="1.0.0",
                userId="user-123",
                activeTrack="dev",
                securityTier=4,
                stateManifest=StateManifest(lastCommitHash="abc")
            )
    
    def test_session_serialization(self):
        """Test session can be serialized to dict"""
        session = UserSessionContext(
            schemaVersion="1.0.0",
            userId="user-123",
            activeTrack="testing",
            securityTier=2,
            stateManifest=StateManifest(lastCommitHash="xyz789", pendingSync=True)
        )
        session_dict = session.model_dump()
        assert session_dict["userId"] == "user-123"
        assert session_dict["stateManifest"]["pendingSync"] is True


class TestStateEngine:
    """Test StateEngine class"""
    
    def test_create_engine(self):
        """Test creating a state engine"""
        engine = StateEngine()
        assert engine is not None
    
    def test_create_session(self):
        """Test creating a session through engine"""
        engine = StateEngine()
        session = engine.create_session(
            user_id="test-user",
            active_track="integration",
            security_tier=1,
            initial_commit_hash="initial123"
        )
        assert session.userId == "test-user"
        assert session.schemaVersion == "1.0.0"
        assert session.stateManifest.lastCommitHash == "initial123"
    
    def test_update_commit_hash(self):
        """Test updating commit hash"""
        engine = StateEngine()
        session = engine.create_session(user_id="test", active_track="dev")
        updated = engine.update_commit_hash(session, "new-hash-456")
        assert updated.stateManifest.lastCommitHash == "new-hash-456"
        assert updated.stateManifest.pendingSync is False
    
    def test_mark_pending_sync(self):
        """Test marking session for sync"""
        engine = StateEngine()
        session = engine.create_session(user_id="test", active_track="dev")
        updated = engine.mark_pending_sync(session)
        assert updated.stateManifest.pendingSync is True
    
    def test_validate_session(self):
        """Test session validation"""
        engine = StateEngine()
        valid_data = {
            "schemaVersion": "1.0.0",
            "userId": "user-123",
            "activeTrack": "dev",
            "securityTier": 1,
            "stateManifest": {
                "lastCommitHash": "abc",
                "pendingSync": False
            }
        }
        assert engine.validate_session(valid_data) is True
        
        invalid_data = {"userId": "user-123"}  # Missing required fields
        with pytest.raises(ValueError):
            engine.validate_session(invalid_data)
    
    def test_calculate_state_hash(self):
        """Test state hash calculation"""
        engine = StateEngine()
        session1 = engine.create_session(user_id="test", active_track="dev")
        session2 = engine.create_session(user_id="test", active_track="dev")
        
        # Same sessions should have same hash
        hash1 = engine.calculate_state_hash(session1)
        hash2 = engine.calculate_state_hash(session2)
        assert hash1 == hash2
        
        # Different sessions should have different hash
        session3 = engine.create_session(user_id="different", active_track="dev")
        hash3 = engine.calculate_state_hash(session3)
        assert hash1 != hash3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
