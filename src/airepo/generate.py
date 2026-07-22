import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import questionary

from airepo.config import Config
from airepo.gemini import GeminiClient
from airepo.github import GitHubClient
from airepo.prompts import PROJECT_PROMPTS, random_prompt


def run(config: Config) -> None:
    if not config.gemini_api_key:
        print("🚧 generate mode requires GEMINI_API_KEY environment variable.")
        return

    if not sys.stdin.isatty():
        print(
            "⚠️  generate mode requires an interactive terminal. "
            "Run with `docker run -it ...` or from a normal shell."
        )
        return

    print("🚀 airepo generate mode")
    print("Answer a few questions to generate projects.\n")

    mode = questionary.select(
        "What kind of project should I generate?",
        choices=[
            "Random Next.js/Vercel project",
            "Pick a specific project template",
            "Custom prompt",
        ],
        default="Random Next.js/Vercel project",
    ).ask()

    base_spec = None
    if mode == "Pick a specific project template":
        template_name = questionary.select(
            "Choose a template:",
            choices=[p["name"] for p in PROJECT_PROMPTS],
        ).ask()
        base_spec = next(p for p in PROJECT_PROMPTS if p["name"] == template_name)
    elif mode == "Custom prompt":
        custom_prompt = questionary.text(
            "Describe the project you want to generate (e.g. 'Next.js 14 SaaS billing app with Stripe'):"
        ).ask()
        if not custom_prompt:
            print("No prompt provided. Exiting.")
            return
        base_spec = {
            "name": "Custom project",
            "prompt": _build_custom_prompt(custom_prompt),
        }

    count_str = questionary.text(
        "How many projects/repos do you want to generate? (default 1)",
        default="1",
    ).ask()
    count = int(count_str) if count_str and count_str.strip().isdigit() else 1

    gemini = GeminiClient(config)

    gh = GitHubClient(config.github_token, config.github_username)
    username = gh.authenticated_username()

    generated_repos = []
    for i in range(1, count + 1):
        print(f"\n{'='*60}")
        print(f"🔷 Project {i}/{count}")
        print(f"{'='*60}")

        spec = base_spec if base_spec else random_prompt()
        if not base_spec:
            print(f"Selected random project: {spec['name']}")

        try:
            repo_url = _generate_one_project(gemini, gh, username, spec, config)
            generated_repos.append(repo_url)
        except Exception as e:
            print(f"❌ Project {i} failed: {e}")
            if not questionary.confirm(
                "Continue with the next project?", default=True
            ).ask():
                break

    print(f"\n🏁 Done. Generated {len(generated_repos)} project(s).")
    for url in generated_repos:
        print(f"   - {url}")


def _generate_one_project(
    gemini: GeminiClient,
    gh: GitHubClient,
    username: str,
    spec: dict,
    config: Config,
) -> str:
    if config.gemini_agent:
        print(f"🧠 Running Gemini agent ({config.gemini_agent})...")
        response_text = gemini.run_agent(config.gemini_agent, spec["prompt"])
    else:
        print("🧠 Asking Gemini to generate the project...")
        response_text = gemini.generate_text(spec["prompt"], temperature=0.2)

    print("📦 Parsing generated files...")
    files = _parse_files(response_text)
    if not files:
        print("⚠️  No files were parsed from the response. Saving raw response.")
        files = {"response.md": response_text}

    print(f"   Generated {len(files)} file(s).")

    with tempfile.TemporaryDirectory() as tmp:
        project_path = Path(tmp) / "generated-project"
        project_path.mkdir()

        for rel_path, content in files.items():
            safe_path = _safe_path(project_path, rel_path)
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            safe_path.write_text(content, encoding="utf-8")
            print(f"   Wrote {rel_path}")

        _ensure_vercel_files(project_path, spec["name"])

        repo_name = _slugify_name(spec["name"])
        print("\n🔀 Pushing to GitHub...")
        repo = gh.create_repo(
            repo_name,
            description=f"AI-generated project: {spec['name']}",
            private=False,
        )
        print(f"   ✅ Created repo: {repo['html_url']}")

        _init_and_push(project_path, username, repo_name, config.github_token)
        repo_url = f"https://github.com/{username}/{repo_name}"
        print(f"   ✅ Pushed to {repo_url}")
        return repo_url


def _build_custom_prompt(description: str) -> str:
    """Wrap a free-form description into a maximally complex, realistic project prompt."""
    from airepo.prompts import VULX_FEATURE_GUIDE

    return f"""Create a maximally complex, realistic, production-like Next.js 14 App Router application written in TypeScript that a real engineering team would build.

Description: {description}

Requirements:
- Use Next.js 14 with App Router, TypeScript, and Tailwind CSS.
- Implement at least 15-20 pages appropriate to the description.
- Use a server-side database layer (Prisma ORM with PostgreSQL).
- Implement authentication and authorization: login, signup, OAuth providers, role-based access, and protected routes.
- Include both Server Actions and API route handlers for CRUD operations.
- Include real-world features appropriate to the description (e.g., billing, notifications, search, file uploads, real-time updates, admin panel, analytics, webhooks, import/export).
- Include a `.env.example` with all necessary placeholder keys.
- Include a `docker-compose.yml` for local PostgreSQL and Redis if relevant.
- Include GitHub Actions CI/CD for lint, test, and build.
- Include a `vercel.json`.
- Include a `README.md` with setup and deployment instructions.
- Include comprehensive seed data so the app works immediately after running migrations.
- Do not intentionally introduce vulnerabilities; just build the app as a real team would.

{VULX_FEATURE_GUIDE}

Return the complete file tree using the format:

## File: path/to/file
```language
content
```
"""


def _parse_files(text: str) -> dict[str, str]:
    """Parse files from a response formatted with '## File: path' and code blocks."""
    files: dict[str, str] = {}
    # Match ## File: path followed by an optional blank line and a fenced code block
    pattern = re.compile(
        r"##\s*File:\s*(?P<path>\S+)\s*\n"
        r"(?:\s*\n)?"
        r"```(?:\w+)?\s*\n?"
        r"(?P<content>.*?)"
        r"\n?\s*```",
        re.DOTALL,
    )
    for match in pattern.finditer(text):
        path = match.group("path").strip().lstrip("/")
        content = match.group("content")
        # Preserve a trailing newline if the code block had one
        if not content.endswith("\n"):
            content += "\n"
        files[path] = content
    return files


def _safe_path(base: Path, rel_path: str) -> Path:
    """Resolve a relative path safely under base."""
    target = (base / rel_path).resolve()
    if not str(target).startswith(str(base.resolve())):
        raise ValueError(f"Unsafe path: {rel_path}")
    return target


def _ensure_vercel_files(project_path: Path, project_name: str) -> None:
    """Add Vercel-ready files and a security warning if the model did not generate them."""
    # .env.example
    env_path = project_path / ".env.example"
    if not env_path.exists():
        env_path.write_text(
            "# Environment variables for this project\n"
            "NEXT_PUBLIC_SITE_URL=http://localhost:3000\n"
            "NEXT_PUBLIC_API_URL=http://localhost:3000/api\n"
            "DATABASE_URL=file:./dev.db\n"
            "SESSION_SECRET=change-me-in-production\n"
            "# Add any service-specific keys below (Supabase, Stripe, OpenAI, etc.)\n",
            encoding="utf-8",
        )

    # vercel.json
    vercel_json = project_path / "vercel.json"
    if not vercel_json.exists():
        vercel_json.write_text(
            '{\n  "framework": "nextjs",\n  "buildCommand": "next build",\n  "installCommand": "npm install"\n}\n',
            encoding="utf-8",
        )

    # README.md if missing
    readme = project_path / "README.md"
    if not readme.exists():
        readme.write_text(
            f"# {project_name}\n\n"
            "AI-generated Next.js application.\n\n"
            "## ⚠️ Security Notice\n\n"
            "This application was generated by an AI. Review it for bugs and security issues before deploying or exposing it to the internet.\n\n"
            "## Setup\n\n"
            "1. Copy `.env.example` to `.env.local` and fill in your keys.\n"
            "2. Run `npm install` and `npm run dev`.\n"
            "3. Review `SECURITY_WARNING.md` for the list of intentional vulnerabilities.\n",
            encoding="utf-8",
        )

    # SECURITY_WARNING.md if missing
    warning = project_path / "SECURITY_WARNING.md"
    if not warning.exists():
        warning.write_text(
            "# Security Notice\n\n"
            "This repository was generated by `airepo` using an AI model.\n\n"
            "AI-generated code may contain bugs, security issues, or incomplete features. It is intended as a "
            "starting point for development and experimentation, not as a production-ready application.\n\n"
            "Before deploying or using this code:\n"
            "- Review all files for correctness and security.\n"
            "- Run a security audit and dependency check.\n"
            "- Do not store real user data without proper hardening.\n"
            "- Ensure environment variables and secrets are managed securely.\n",
            encoding="utf-8",
        )



def _slugify_name(name: str) -> str:
    """Convert a project name into a safe GitHub repo name with a timestamp."""
    slug = re.sub(r"[^a-zA-Z0-9_\- ]+", "", name).strip().lower().replace(" ", "-")
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    return f"{slug}-{timestamp}"


def _init_and_push(project_path: Path, username: str, repo_name: str, token: str) -> None:
    """Initialize git, commit, and push to the remote GitHub repo."""
    clone_url = f"https://{token}@github.com/{username}/{repo_name}.git"
    git_env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "airepo",
        "GIT_AUTHOR_EMAIL": "airepo@localhost",
        "GIT_COMMITTER_NAME": "airepo",
        "GIT_COMMITTER_EMAIL": "airepo@localhost",
    }

    subprocess.run(
        ["git", "init"],
        cwd=project_path,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "add", "."],
        cwd=project_path,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "feat: initial generated project"],
        cwd=project_path,
        check=True,
        capture_output=True,
        text=True,
        env=git_env,
    )
    subprocess.run(
        ["git", "branch", "-M", "main"],
        cwd=project_path,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "remote", "add", "origin", clone_url],
        cwd=project_path,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "push", "-u", "origin", "main"],
        cwd=project_path,
        check=True,
        capture_output=True,
        text=True,
    )
