import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import patch
from datetime import datetime, timedelta

from services.retention_jobs import (
    RetentionJobManager,
    RetentionConfig,
    get_retention_manager,
)


@pytest.fixture
def temp_directories():
    """Create temporary directories for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "temp_uploads"
        exports_path = Path(temp_dir) / "exports"
        logs_path = Path(temp_dir) / "logs"

        temp_path.mkdir()
        exports_path.mkdir()
        logs_path.mkdir()

        yield temp_path, exports_path, logs_path


@pytest.fixture
def retention_config():
    """Create test retention configuration"""
    return RetentionConfig(
        analysis_retention_hours=1,
        temp_file_retention_hours=1,
        export_file_retention_hours=1,
        log_retention_days=1,
        cleanup_interval_hours=0.01,  # Very fast for testing
        export_cleanup_interval_hours=0.01,
        log_cleanup_interval_days=0.001,
    )


@pytest.fixture
def retention_manager(temp_directories, retention_config):
    """Create retention manager for testing"""
    temp_path, exports_path, logs_path = temp_directories

    # Mock the environment variables
    with patch.dict(
        os.environ,
        {
            "TEMP_STORAGE_PATH": str(temp_path),
        },
    ):
        manager = RetentionJobManager(retention_config)
        manager.exports_path = exports_path
        manager.logs_path = logs_path
        return manager


@pytest.mark.asyncio
async def test_retention_manager_initialization(retention_manager):
    """Test retention manager initialization"""
    assert retention_manager.running is False
    assert len(retention_manager.tasks) == 0
    assert retention_manager.config.analysis_retention_hours == 1


@pytest.mark.asyncio
async def test_start_stop_retention_jobs(retention_manager):
    """Test starting and stopping retention jobs"""
    # Start jobs
    await retention_manager.start()
    assert retention_manager.running is True
    assert len(retention_manager.tasks) == 5  # 5 different cleanup tasks

    # Stop jobs
    await retention_manager.stop()
    assert retention_manager.running is False
    assert len(retention_manager.tasks) == 0


@pytest.mark.asyncio
async def test_analysis_cache_cleanup(retention_manager, temp_directories):
    """Test analysis cache cleanup"""
    temp_path, _, _ = temp_directories

    # Mock analysis cache and lock
    retention_manager.analysis_cache = {
        "old_file": {
            "timestamp": datetime.now() - timedelta(hours=2),
            "file_path": str(temp_path / "old_file.pdf"),
        },
        "new_file": {
            "timestamp": datetime.now() - timedelta(minutes=30),
            "file_path": str(temp_path / "new_file.pdf"),
        },
    }
    retention_manager.analysis_lock = asyncio.Lock()

    # Create test files
    (temp_path / "old_file.pdf").write_text("test content")
    (temp_path / "new_file.pdf").write_text("test content")

    # Run cleanup
    await retention_manager._cleanup_analysis_cache()

    # Check that old file was removed from cache
    assert "old_file" not in retention_manager.analysis_cache
    assert "new_file" in retention_manager.analysis_cache


@pytest.mark.asyncio
async def test_temp_file_cleanup(retention_manager, temp_directories):
    """Test temporary file cleanup"""
    temp_path, _, _ = temp_directories

    # Create old and new files
    old_file = temp_path / "old_file.pdf"
    new_file = temp_path / "new_file.pdf"

    old_file.write_text("old content")
    new_file.write_text("new content")

    # Modify timestamps
    old_time = datetime.now() - timedelta(hours=2)
    new_time = datetime.now() - timedelta(minutes=30)

    os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))
    os.utime(new_file, (new_time.timestamp(), new_time.timestamp()))

    # Run cleanup
    await retention_manager._cleanup_temp_files()

    # Check that old file was removed
    assert not old_file.exists()
    assert new_file.exists()


@pytest.mark.asyncio
async def test_export_file_cleanup(retention_manager, temp_directories):
    """Test export file cleanup"""
    _, exports_path, _ = temp_directories

    # Create old and new export files
    old_file = exports_path / "old_export.json"
    new_file = exports_path / "new_export.json"

    old_file.write_text('{"old": "data"}')
    new_file.write_text('{"new": "data"}')

    # Modify timestamps
    old_time = datetime.now() - timedelta(hours=2)
    new_time = datetime.now() - timedelta(minutes=30)

    os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))
    os.utime(new_file, (new_time.timestamp(), new_time.timestamp()))

    # Run cleanup
    await retention_manager._cleanup_export_files()

    # Check that old file was removed
    assert not old_file.exists()
    assert new_file.exists()


@pytest.mark.asyncio
async def test_log_file_cleanup(retention_manager, temp_directories):
    """Test log file cleanup"""
    _, _, logs_path = temp_directories

    # Create old and new log files
    old_log = logs_path / "old.log"
    new_log = logs_path / "new.log"

    old_log.write_text("old log content")
    new_log.write_text("new log content")

    # Modify timestamps
    old_time = datetime.now() - timedelta(days=2)
    new_time = datetime.now() - timedelta(hours=12)

    os.utime(old_log, (old_time.timestamp(), old_time.timestamp()))
    os.utime(new_log, (new_time.timestamp(), new_time.timestamp()))

    # Run cleanup
    await retention_manager._cleanup_log_files()

    # Check that old file was removed
    assert not old_log.exists()
    assert new_log.exists()


@pytest.mark.asyncio
async def test_force_cleanup(retention_manager, temp_directories):
    """Test force cleanup functionality"""
    temp_path, exports_path, logs_path = temp_directories

    # Create test files
    (temp_path / "test_temp.pdf").write_text("temp content")
    (exports_path / "test_export.json").write_text('{"test": "data"}')
    (logs_path / "test.log").write_text("log content")

    # Mock analysis cache
    retention_manager.analysis_cache = {
        "test_file": {
            "timestamp": datetime.now() - timedelta(hours=2),
            "file_path": str(temp_path / "test_temp.pdf"),
        }
    }
    retention_manager.analysis_lock = asyncio.Lock()

    # Force cleanup
    await retention_manager.force_cleanup("all")

    # Verify files were processed (specific cleanup behavior depends on timestamps)
    # The important thing is that the method runs without error


@pytest.mark.asyncio
async def test_health_check(retention_manager, temp_directories):
    """Test health check functionality"""
    temp_path, exports_path, logs_path = temp_directories

    # Create some test files
    (temp_path / "test1.pdf").write_text("content")
    (exports_path / "test2.json").write_text('{"test": "data"}')
    (logs_path / "test3.log").write_text("log content")

    # Run health check
    await retention_manager._health_check()

    # Should complete without error


def test_get_status(retention_manager):
    """Test get status functionality"""
    status = retention_manager.get_status()

    assert "running" in status
    assert "active_tasks" in status
    assert "config" in status
    assert "paths" in status
    assert status["running"] is False
    assert status["active_tasks"] == 0


@pytest.mark.asyncio
async def test_safe_remove_file(retention_manager):
    """Test safe file removal"""
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
        tmp_file.write(b"test content")

    # Test removing existing file
    assert tmp_path.exists()
    await retention_manager._safe_remove_file(tmp_path)
    assert not tmp_path.exists()

    # Test removing non-existent file (should not raise error)
    await retention_manager._safe_remove_file(Path("non_existent_file"))


def test_get_retention_manager():
    """Test global retention manager getter"""
    # Reset global manager
    import services.retention_jobs

    services.retention_jobs.retention_manager = None

    manager1 = get_retention_manager()
    manager2 = get_retention_manager()

    # Should return the same instance
    assert manager1 is manager2
