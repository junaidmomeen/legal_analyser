"""
Retention Jobs Service

This module handles automated cleanup and retention policies for:
- Analysis cache entries
- Temporary uploaded files
- Export files
- Log files
- Database cleanup (if applicable)
"""

import asyncio
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import aiofiles
import aiofiles.os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RetentionConfig:
    """Configuration for retention policies"""

    # Analysis cache retention
    analysis_retention_hours: int = 24

    # File retention
    temp_file_retention_hours: int = 6
    export_file_retention_hours: int = 48

    # Log retention
    log_retention_days: int = 30

    # Cleanup intervals
    cleanup_interval_hours: int = 1
    export_cleanup_interval_hours: int = 4
    log_cleanup_interval_days: int = 1

    # Limits
    max_analysis_entries: int = 1000
    max_export_files: int = 500
    max_log_files: int = 100


class RetentionJobManager:
    """Manages all retention and cleanup jobs"""

    def __init__(self, config: Optional[RetentionConfig] = None):
        self.config = config or RetentionConfig()
        self.running = False
        self.tasks: List[asyncio.Task] = []

        # Paths
        self.temp_path = Path(os.getenv("TEMP_STORAGE_PATH", "temp_uploads"))
        self.exports_path = Path("exports")
        self.logs_path = Path("logs")

        # Ensure directories exist
        self.temp_path.mkdir(exist_ok=True)
        self.exports_path.mkdir(exist_ok=True)
        self.logs_path.mkdir(exist_ok=True)

    async def start(self):
        """Start all retention jobs"""
        if self.running:
            logger.warning("Retention jobs already running")
            return

        self.running = True
        logger.info("Starting retention jobs")

        # Start individual cleanup tasks
        self.tasks = [
            asyncio.create_task(self._analysis_cleanup_loop()),
            asyncio.create_task(self._file_cleanup_loop()),
            asyncio.create_task(self._export_cleanup_loop()),
            asyncio.create_task(self._log_cleanup_loop()),
            asyncio.create_task(self._health_check_loop()),
        ]

        logger.info(f"Started {len(self.tasks)} retention jobs")

    async def stop(self):
        """Stop all retention jobs"""
        if not self.running:
            return

        logger.info("Stopping retention jobs")
        self.running = False

        # Cancel all tasks
        for task in self.tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()

        logger.info("Retention jobs stopped")

    async def _analysis_cleanup_loop(self):
        """Clean up old analysis cache entries"""
        while self.running:
            try:
                await asyncio.sleep(self.config.cleanup_interval_hours * 3600)

                if hasattr(self, "analysis_cache") and hasattr(self, "analysis_lock"):
                    await self._cleanup_analysis_cache()
                else:
                    logger.debug("Analysis cache not available for cleanup")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Analysis cleanup loop error: {e}", exc_info=True)

    async def _file_cleanup_loop(self):
        """Clean up temporary files"""
        while self.running:
            try:
                await asyncio.sleep(self.config.cleanup_interval_hours * 3600)
                await self._cleanup_temp_files()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"File cleanup loop error: {e}", exc_info=True)

    async def _export_cleanup_loop(self):
        """Clean up export files"""
        while self.running:
            try:
                await asyncio.sleep(self.config.export_cleanup_interval_hours * 3600)
                await self._cleanup_export_files()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Export cleanup loop error: {e}", exc_info=True)

    async def _log_cleanup_loop(self):
        """Clean up old log files"""
        while self.running:
            try:
                await asyncio.sleep(self.config.log_cleanup_interval_days * 24 * 3600)
                await self._cleanup_log_files()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Log cleanup loop error: {e}", exc_info=True)

    async def _health_check_loop(self):
        """Health check for retention jobs"""
        while self.running:
            try:
                await asyncio.sleep(300)  # 5 minutes
                await self._health_check()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}", exc_info=True)

    async def _cleanup_analysis_cache(self):
        """Clean up old analysis cache entries"""
        if not hasattr(self, "analysis_cache") or not hasattr(self, "analysis_lock"):
            return

        cutoff_time = datetime.now() - timedelta(
            hours=self.config.analysis_retention_hours
        )
        cleanup_count = 0

        async with self.analysis_lock:
            # Create a copy to avoid race conditions
            for file_id, data in list(self.analysis_cache.items()):
                try:
                    if data.get("timestamp", datetime.min) < cutoff_time:
                        # Remove associated file
                        file_path = data.get("file_path")
                        if file_path:
                            await self._safe_remove_file(file_path)

                        # Remove from cache
                        del self.analysis_cache[file_id]
                        cleanup_count += 1

                except Exception as e:
                    logger.error(f"Error cleaning up analysis {file_id}: {e}")

        if cleanup_count > 0:
            logger.info(f"Analysis cache cleanup: {cleanup_count} entries removed")

    async def _cleanup_temp_files(self):
        """Clean up old temporary files"""
        cutoff_time = datetime.now() - timedelta(
            hours=self.config.temp_file_retention_hours
        )
        cleanup_count = 0

        try:
            for file_path in self.temp_path.iterdir():
                if file_path.is_file():
                    try:
                        stat = await aiofiles.os.stat(file_path)
                        file_time = datetime.fromtimestamp(stat.st_mtime)

                        if file_time < cutoff_time:
                            await self._safe_remove_file(file_path)
                            cleanup_count += 1

                    except Exception as e:
                        logger.error(f"Error cleaning up temp file {file_path}: {e}")

        except Exception as e:
            logger.error(f"Error during temp file cleanup: {e}")

        if cleanup_count > 0:
            logger.info(f"Temp file cleanup: {cleanup_count} files removed")

    async def _cleanup_export_files(self):
        """Clean up old export files"""
        cutoff_time = datetime.now() - timedelta(
            hours=self.config.export_file_retention_hours
        )
        cleanup_count = 0

        try:
            for file_path in self.exports_path.iterdir():
                if file_path.is_file():
                    try:
                        stat = await aiofiles.os.stat(file_path)
                        file_time = datetime.fromtimestamp(stat.st_mtime)

                        if file_time < cutoff_time:
                            await self._safe_remove_file(file_path)
                            cleanup_count += 1

                    except Exception as e:
                        logger.error(f"Error cleaning up export file {file_path}: {e}")

        except Exception as e:
            logger.error(f"Error during export file cleanup: {e}")

        if cleanup_count > 0:
            logger.info(f"Export file cleanup: {cleanup_count} files removed")

    async def _cleanup_log_files(self):
        """Clean up old log files"""
        cutoff_time = datetime.now() - timedelta(days=self.config.log_retention_days)
        cleanup_count = 0

        try:
            for file_path in self.logs_path.iterdir():
                if file_path.is_file() and file_path.suffix in [
                    ".log",
                    ".log.1",
                    ".log.2",
                ]:
                    try:
                        stat = await aiofiles.os.stat(file_path)
                        file_time = datetime.fromtimestamp(stat.st_mtime)

                        if file_time < cutoff_time:
                            await self._safe_remove_file(file_path)
                            cleanup_count += 1

                    except Exception as e:
                        logger.error(f"Error cleaning up log file {file_path}: {e}")

        except Exception as e:
            logger.error(f"Error during log file cleanup: {e}")

        if cleanup_count > 0:
            logger.info(f"Log file cleanup: {cleanup_count} files removed")

    async def _safe_remove_file(self, file_path: Path):
        """Safely remove a file"""
        try:
            await aiofiles.os.stat(file_path)
            await aiofiles.os.remove(file_path)
        except FileNotFoundError:
            pass  # File already removed
        except Exception as e:
            logger.error(f"Error removing file {file_path}: {e}")

    async def _health_check(self):
        """Perform health check on retention system"""
        try:
            # Check disk space
            temp_usage = await self._get_directory_size(self.temp_path)
            export_usage = await self._get_directory_size(self.exports_path)
            log_usage = await self._get_directory_size(self.logs_path)

            total_usage_mb = (temp_usage + export_usage + log_usage) / (1024 * 1024)

            if total_usage_mb > 1000:  # More than 1GB
                logger.warning(f"High disk usage detected: {total_usage_mb:.2f}MB")

            # Log periodic status
            logger.debug(
                f"Retention health check - Temp: {temp_usage / 1024:.1f}KB, "
                f"Exports: {export_usage / 1024:.1f}KB, Logs: {log_usage / 1024:.1f}KB"
            )

        except Exception as e:
            logger.error(f"Health check error: {e}")

    async def _get_directory_size(self, path: Path) -> int:
        """Get total size of directory in bytes"""
        total_size = 0
        try:
            for file_path in path.iterdir():
                if file_path.is_file():
                    stat = await aiofiles.os.stat(file_path)
                    total_size += stat.st_size
        except Exception:
            pass
        return total_size

    async def force_cleanup(self, cleanup_type: str = "all"):
        """Force immediate cleanup of specified type"""
        logger.info(f"Force cleanup requested: {cleanup_type}")

        try:
            if cleanup_type in ["all", "analysis"]:
                await self._cleanup_analysis_cache()

            if cleanup_type in ["all", "temp"]:
                await self._cleanup_temp_files()

            if cleanup_type in ["all", "export"]:
                await self._cleanup_export_files()

            if cleanup_type in ["all", "log"]:
                await self._cleanup_log_files()

        except Exception as e:
            logger.error(f"Force cleanup error: {e}")
            raise

    def get_status(self) -> Dict[str, Any]:
        """Get current status of retention jobs"""
        return {
            "running": self.running,
            "active_tasks": len(self.tasks),
            "config": {
                "analysis_retention_hours": self.config.analysis_retention_hours,
                "temp_file_retention_hours": self.config.temp_file_retention_hours,
                "export_file_retention_hours": self.config.export_file_retention_hours,
                "log_retention_days": self.config.log_retention_days,
                "cleanup_interval_hours": self.config.cleanup_interval_hours,
            },
            "paths": {
                "temp_path": str(self.temp_path),
                "exports_path": str(self.exports_path),
                "logs_path": str(self.logs_path),
            },
        }


# Global retention manager instance
retention_manager: Optional[RetentionJobManager] = None


def get_retention_manager() -> RetentionJobManager:
    """Get or create the global retention manager"""
    global retention_manager
    if retention_manager is None:
        retention_manager = RetentionJobManager()
    return retention_manager


async def start_retention_jobs():
    """Start the retention jobs"""
    manager = get_retention_manager()
    await manager.start()


async def stop_retention_jobs():
    """Stop the retention jobs"""
    manager = get_retention_manager()
    await manager.stop()
