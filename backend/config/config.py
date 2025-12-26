"""Application settings using Pydantic Settings."""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Emperor AI Assistant"
    debug: bool = False
    log_level: str = "INFO"

    # Paths
    project_root: Path = Path(__file__).parent.parent.parent
    data_dir: Path = Path(__file__).parent.parent.parent / "data"

    # Server
    host: str = "127.0.0.1"
    port: int = 8765

    # Claude Code Integration (Optional)
    claude_code_oauth_token: Optional[str] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._create_data_directories()

    def _create_data_directories(self) -> None:
        """Create required data directories if they don't exist."""
        directories = [
            self.data_dir,
            self.data_dir / "chroma",
            self.data_dir / "logs",
            self.data_dir / "whisper",
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# Singleton instance
settings = Settings()
