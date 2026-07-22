import os
import sys
from pathlib import Path

import click
import questionary
from dotenv import load_dotenv

from airepo import generate, scrape
from airepo.config import (
    DEFAULT_AGENT,
    DEFAULT_CONFIG_DIR,
    load_config,
    missing_required_keys,
    required_keys,
    save_config,
)


@click.command()
@click.option(
    "--mode",
    type=click.Choice(["scrape", "generate"], case_sensitive=False),
    required=False,
    help="Mode: scrape or generate.",
)
@click.option(
    "--scrape",
    "mode_scrape",
    is_flag=True,
    help="Shortcut for --mode scrape.",
)
@click.option(
    "--generate",
    "mode_generate",
    is_flag=True,
    help="Shortcut for --mode generate.",
)
@click.option(
    "--env-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to a .env file with API keys.",
)
@click.option(
    "--config-dir",
    type=click.Path(file_okay=False, path_type=Path),
    help="Directory to store persisted API keys. Defaults to ~/.config/airepo.",
)
def main(
    mode: str | None,
    mode_scrape: bool,
    mode_generate: bool,
    env_file: Path | None,
    config_dir: Path | None,
) -> None:
    """airepo: scrape and fork AI-generated repos, or generate new projects."""
    config_dir = config_dir or DEFAULT_CONFIG_DIR

    if mode_scrape and mode_generate:
        raise click.UsageError("Use either --scrape or --generate, not both.")
    if mode_scrape:
        mode = "scrape"
    elif mode_generate:
        mode = "generate"

    if not mode:
        raise click.UsageError("Missing required option: --mode (or --scrape / --generate).")

    # Try to load config; if keys are missing and we're interactive, prompt once and persist.
    config = _ensure_config(env_file, config_dir)

    mode = mode.lower()
    if mode == "scrape":
        scrape.run(config)
    elif mode == "generate":
        generate.run(config)
    else:
        click.echo(f"Unknown mode: {mode}", err=True)
        sys.exit(1)


def _ensure_config(env_file: Path | None, config_dir: Path):
    """Load config, prompting for missing keys on first interactive run."""
    try:
        return load_config(env_file=env_file, config_dir=config_dir)
    except ValueError as e:
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            click.echo(f"Error: {e}", err=True)
            click.echo(
                "Pass the required keys as environment variables or mount a persisted config directory.",
                err=True,
            )
            sys.exit(1)

        missing = _collect_missing_keys(env_file=env_file, config_dir=config_dir)
        if not missing:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)

        click.echo("🔐 Some API keys are missing. Let's set them up once and persist them.")
        prompted = _prompt_for_keys(missing)

        # Combine freshly prompted values with any keys already present in env/config
        values: dict[str, str] = {}
        for key in required_keys():
            if key in prompted:
                values[key] = prompted[key]
            else:
                existing = _get_existing_or_default(env_file, config_dir, key, "")
                if not existing:
                    click.echo(f"Error: {key} is required but could not be determined.", err=True)
                    sys.exit(1)
                values[key] = existing

        # Fill in optional defaults if not already set
        gemini_model = _get_existing_or_default(env_file, config_dir, "GEMINI_MODEL", "gemini-flash-latest")
        gemini_agent = _get_existing_or_default(env_file, config_dir, "GEMINI_AGENT", DEFAULT_AGENT)
        github_username = _get_existing_or_default(env_file, config_dir, "GITHUB_USERNAME", "")

        env_path = save_config(
            gemini_api_key=values["GEMINI_API_KEY"],
            github_token=values["GITHUB_TOKEN"],
            github_username=github_username or None,
            gemini_model=gemini_model,
            gemini_agent=gemini_agent,
            config_dir=config_dir,
        )
        click.echo(f"   ✅ Saved credentials to {env_path}")

        return load_config(env_file=env_file, config_dir=config_dir)


def _collect_missing_keys(env_file: Path | None, config_dir: Path) -> list[str]:
    """Check every required key against env vars and the persisted config dir."""
    if env_file:
        load_dotenv(env_file, override=True)
    load_dotenv(config_dir / ".env", override=False)

    missing = []
    for key in required_keys():
        if not os.getenv(key, "").strip():
            missing.append(key)
    return missing


def _prompt_for_keys(missing: list[str]) -> dict[str, str]:
    """Interactively prompt for missing required keys."""
    values: dict[str, str] = {}
    for key in missing:
        if key == "GEMINI_API_KEY":
            prompt = "Your Google Gemini API key"
        elif key == "GITHUB_TOKEN":
            prompt = "Your GitHub personal access token (repo scope)"
        else:
            prompt = key
        value = questionary.password(f"{prompt}:").ask()
        if not value:
            click.echo(f"Error: {key} is required.", err=True)
            sys.exit(1)
        values[key] = value.strip()
    return values


def _get_existing_or_default(
    env_file: Path | None,
    config_dir: Path,
    key: str,
    default: str,
) -> str:
    """Return an existing env value, a value from the persisted config, or the default."""
    if env_file:
        load_dotenv(env_file, override=True)
    load_dotenv(config_dir / ".env", override=False)
    return os.getenv(key, default).strip()


if __name__ == "__main__":
    main()
