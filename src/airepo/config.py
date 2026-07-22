import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_AGENT = "antigravity-preview-05-2026"
DEFAULT_CONFIG_DIR = Path.home() / ".config" / "airepo"


@dataclass
class Config:
    gemini_api_key: str
    github_token: str
    github_username: str | None
    gemini_model: str = "gemini-flash-latest"
    gemini_agent: str = DEFAULT_AGENT


def _config_env_path(config_dir: Path) -> Path:
    return config_dir / ".env"


def _load_env_vars(config_dir: Path | None) -> dict:
    """Load env vars from the system, the optional config dir .env, and the current directory .env."""
    values = {
        "gemini_api_key": os.getenv("GEMINI_API_KEY", "").strip(),
        "github_token": os.getenv("GITHUB_TOKEN", "").strip(),
        "github_username": os.getenv("GITHUB_USERNAME", "").strip() or None,
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-flash-latest").strip(),
        "gemini_agent": os.getenv("GEMINI_AGENT", "").strip() or None,
    }

    # Config dir .env overrides nothing, fills missing values
    if config_dir:
        env_path = _config_env_path(config_dir)
        if env_path.exists():
            load_dotenv(env_path, override=False)
            for key, env_name in {
                "gemini_api_key": "GEMINI_API_KEY",
                "github_token": "GITHUB_TOKEN",
                "github_username": "GITHUB_USERNAME",
                "gemini_model": "GEMINI_MODEL",
                "gemini_agent": "GEMINI_AGENT",
            }.items():
                if not values[key]:
                    values[key] = os.getenv(env_name, "").strip() or None

    # CWD .env overrides everything
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        load_dotenv(cwd_env, override=True)
        values["gemini_api_key"] = os.getenv("GEMINI_API_KEY", "").strip()
        values["github_token"] = os.getenv("GITHUB_TOKEN", "").strip()
        values["github_username"] = os.getenv("GITHUB_USERNAME", "").strip() or None
        values["gemini_model"] = os.getenv("GEMINI_MODEL", "gemini-flash-latest").strip()
        values["gemini_agent"] = os.getenv("GEMINI_AGENT", "").strip() or None

    return values


def load_config(
    env_file: Path | str | None = None,
    config_dir: Path | str | None = None,
) -> Config:
    if env_file:
        load_dotenv(env_file, override=True)
        values = {
            "gemini_api_key": os.getenv("GEMINI_API_KEY", "").strip(),
            "github_token": os.getenv("GITHUB_TOKEN", "").strip(),
            "github_username": os.getenv("GITHUB_USERNAME", "").strip() or None,
            "gemini_model": os.getenv("GEMINI_MODEL", "gemini-flash-latest").strip(),
            "gemini_agent": os.getenv("GEMINI_AGENT", "").strip() or None,
        }
    else:
        config_dir = Path(config_dir) if config_dir else DEFAULT_CONFIG_DIR
        values = _load_env_vars(config_dir)

    if not values["gemini_api_key"]:
        raise ValueError("GEMINI_API_KEY environment variable is required.")
    if not values["github_token"]:
        raise ValueError("GITHUB_TOKEN environment variable is required.")

    return Config(
        gemini_api_key=values["gemini_api_key"],
        github_token=values["github_token"],
        github_username=values["github_username"],
        gemini_model=values["gemini_model"],
        gemini_agent=values["gemini_agent"] or DEFAULT_AGENT,
    )


def save_config(
    gemini_api_key: str,
    github_token: str,
    github_username: str | None,
    gemini_model: str | None,
    gemini_agent: str | None,
    config_dir: Path | str | None = None,
) -> Path:
    """Save the provided credentials to a .env file in the config directory."""
    config_dir = Path(config_dir) if config_dir else DEFAULT_CONFIG_DIR
    config_dir.mkdir(parents=True, exist_ok=True)
    env_path = _config_env_path(config_dir)

    lines = [
        f"GEMINI_API_KEY={gemini_api_key}",
        f"GITHUB_TOKEN={github_token}",
    ]
    if github_username:
        lines.append(f"GITHUB_USERNAME={github_username}")
    if gemini_model:
        lines.append(f"GEMINI_MODEL={gemini_model}")
    if gemini_agent:
        lines.append(f"GEMINI_AGENT={gemini_agent}")

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return env_path


def missing_required_keys(
    env_file: Path | str | None = None,
    config_dir: Path | str | None = None,
) -> list[str]:
    """Return a list of required env vars that are missing."""
    try:
        load_config(env_file=env_file, config_dir=config_dir)
        return []
    except ValueError as e:
        msg = str(e)
        missing = []
        if "GEMINI_API_KEY" in msg:
            missing.append("GEMINI_API_KEY")
        if "GITHUB_TOKEN" in msg:
            missing.append("GITHUB_TOKEN")
        return missing


def required_keys() -> list[str]:
    return ["GEMINI_API_KEY", "GITHUB_TOKEN"]
