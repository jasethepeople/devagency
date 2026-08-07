"""
Lo-fi Girl Vibes Module — start/stop background music stream.

Provides ambient background music via mpv streaming to maintain
focus and creative flow during development sessions.
"""
import signal
import subprocess
from pathlib import Path
from typing import Optional

from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

# PID file to track running mpv instance
PID_FILE = Path.home() / ".devagency" / "lofi.pid"


class LofiPlayer:
    """Manages mpv background stream for lo-fi music."""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None

    def start(self, url: Optional[str] = None) -> bool:
        """
        Start the lo-fi stream with mpv.

        Args:
            url: Stream URL (defaults to official Lo-fi Girl)

        Returns:
            True if started successfully
        """
        if self.is_running():
            logger.info("Lo-fi stream already running")
            return True

        stream_url = url or Config.LOFI_URL
        try:
            self.process = subprocess.Popen(
                [
                    "mpv",
                    "--no-video",
                    "--loop=inf",
                    "--really-quiet",
                    stream_url,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            # Save PID
            PID_FILE.parent.mkdir(parents=True, exist_ok=True)
            PID_FILE.write_text(str(self.process.pid))
            logger.info(f"Lo-fi stream started (pid {self.process.pid})")
            return True
        except FileNotFoundError:
            logger.error("mpv not found. Install with: sudo apt install mpv")
            return False
        except Exception as e:
            logger.error(f"Failed to start lo-fi: {e}")
            return False

    def stop(self) -> bool:
        """
        Stop the running lo-fi stream.

        Returns:
            True if stopped successfully
        """
        if PID_FILE.exists():
            try:
                pid = int(PID_FILE.read_text().strip())
                import os
                os.kill(pid, signal.SIGTERM)
                logger.info(f"Sent SIGTERM to lo-fi process {pid}")
                PID_FILE.unlink()
                return True
            except ProcessLookupError:
                logger.warning("Lo-fi process not found, cleaning up")
                PID_FILE.unlink(missing_ok=True)
                return True
            except Exception as e:
                logger.error(f"Failed to stop lo-fi: {e}")
                return False
        else:
            logger.info("No lo-fi stream running")
            return True

    def is_running(self) -> bool:
        """Check if the lo-fi stream is currently active."""
        if not PID_FILE.exists():
            return False
        try:
            pid = int(PID_FILE.read_text().strip())
            import os
            os.kill(pid, 0)  # Check if process exists
            return True
        except (OSError, ValueError):
            PID_FILE.unlink(missing_ok=True)
            return False

    def toggle(self, url: Optional[str] = None) -> str:
        """Toggle lo-fi stream on/off."""
        if self.is_running():
            self.stop()
            return "off"
        else:
            self.start(url)
            return "on"
