import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import questionary

from airepo.config import Config
from airepo.gemini import GeminiClient
from airepo.github import GitHubClient


def _hyperlink(text: str, url: str) -> str:
    """Wrap text in an OSC 8 terminal hyperlink if stdout is a TTY."""
    if not sys.stdout.isatty():
        return text
    return f"\x1b]8;;{url}\x1b\\{text}\x1b]8;;\x1b\\"


def run(config: Config) -> None:
    if not sys.stdin.isatty():
        print(
            "⚠️  scrape mode requires an interactive terminal. "
            "Run with `docker run -it ...` or from a normal shell."
        )
        return

    print("🤖  airepo scrape mode")
    print("Answer a few questions to find AI-generated repos to fork.\n")

    language = questionary.text(
        "Primary language? (e.g. Python, TypeScript, Go; leave blank for any)",
        default="TypeScript",
    ).ask()
    stack = questionary.text(
        "Tech stack / frameworks? (e.g. Next.js, Supabase, FastAPI; leave blank for any)",
        default="Next.js",
    ).ask()
    ai_indicators = questionary.text(
        "AI tool indicators? (e.g. Claude, Cursor, Copilot; leave blank for any)"
    ).ask()
    keywords = questionary.text(
        "Extra keywords / description? (leave blank for none)",
        default="Vercel",
    ).ask()

    count_str = questionary.text(
        "How many repos do you want to find? (default 5)", default="5"
    ).ask()
    count = int(count_str) if count_str and count_str.strip().isdigit() else 5

    filters = {
        "language": language or "",
        "stack": stack or "",
        "ai_indicators": ai_indicators or "",
        "keywords": keywords or "",
    }

    gh = GitHubClient(config.github_token, config.github_username)
    gemini = GeminiClient(config)

    print("\n🔍 Generating GitHub search queries with Gemini...")
    queries = gemini.generate_search_queries(filters)
    if not queries:
        print("No search queries were generated. Exiting.")
        return

    print(f"   Queries: {queries}\n")

    print("🌐 Searching GitHub...")
    seen = set()
    candidates = []
    for query in queries:
        try:
            items = gh.search_repos(query, per_page=min(100, max(count * 5, 30)))
            for item in items:
                if item["full_name"] in seen:
                    continue
                seen.add(item["full_name"])
                candidates.append(item)
        except Exception as e:
            print(f"   Search failed for query '{query}': {e}")

    if not candidates:
        print("No repositories found. Try different filters.")
        return

    inspect_count = min(count * 3, len(candidates), 30)
    print(f"🔎 Inspecting READMEs for {inspect_count} candidates...")
    for item in candidates[:inspect_count]:
        owner, repo = item["full_name"].split("/", 1)
        try:
            item["readme"] = gh.get_readme(owner, repo)
        except Exception:
            item["readme"] = ""

    print("🧠 Filtering with Gemini for AI-generated repos...")
    chosen = gemini.filter_ai_repos(candidates[:inspect_count], count)
    if not chosen:
        print("No AI-generated repos were identified. Try different filters.")
        return

    print(f"\n📋 Found {len(chosen)} repo(s) that may be AI-generated:\n")
    for idx, repo in enumerate(chosen, start=1):
        print(f"  {idx}. {_hyperlink(repo['full_name'], repo['html_url'])}")
        print(f"     {repo['html_url']}")
        print(f"     {repo.get('description') or 'No description'}")
        print(f"     🤖 {repo.get('reason') or 'No reason given'}\n")

    print("   (Click a repo name above to open it in your browser.)\n")

    choices = [r["full_name"] for r in chosen]
    selected = questionary.checkbox(
        "Select repos to fork to your profile as public:", choices=choices
    ).ask()

    if not selected:
        print("No repos selected. Exiting.")
        return

    username = gh.authenticated_username()
    print(f"\n🔀 Forking selected repos to @{username}...\n")

    for full_name in selected:
        owner, repo = full_name.split("/", 1)
        try:
            fork = gh.fork_repo(owner, repo)
            new_url = fork["html_url"]
            print(f"   ✅ Forked {full_name} -> {new_url}")

            if questionary.confirm(
                f"   Prepare {repo} for Vercel deployment (add .env.example, vercel.json, deploy guide)?",
                default=True,
            ).ask():
                _prepare_fork(gh, username, repo, filters)
        except Exception as e:
            print(f"   ❌ Failed to fork {full_name}: {e}")

    print("\n🏁 Done.")


def _is_nextjs_project(repo_path: Path) -> bool:
    """Detect whether the cloned repo is a Next.js project."""
    package_json = repo_path / "package.json"
    if not package_json.exists():
        return False
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        return "next" in deps
    except Exception:
        return False


def _build_env_example(stack: str, language: str, is_nextjs: bool) -> str:
    """Build a .env.example tailored to the detected stack."""
    lines = ["# Environment variables for this project"]
    lowered = (stack or "").lower() + " " + (language or "").lower()

    if is_nextjs or "next" in lowered or "react" in lowered:
        lines.extend(
            [
                "NEXT_PUBLIC_SITE_URL=http://localhost:3000",
                "NEXT_PUBLIC_API_URL=http://localhost:3000/api",
            ]
        )
        if "nextauth" in lowered or "auth" in lowered:
            lines.extend(
                [
                    "NEXTAUTH_URL=http://localhost:3000",
                    "NEXTAUTH_SECRET=generate-with-openssl-rand-base64-32",
                ]
            )
    if "supabase" in lowered:
        lines.extend(
            [
                "SUPABASE_URL=https://your-project.supabase.co",
                "SUPABASE_ANON_KEY=your-anon-key",
                "SUPABASE_SERVICE_ROLE_KEY=your-service-role-key",
            ]
        )
    if "openai" in lowered or "ai" in lowered or "gpt" in lowered:
        lines.append("OPENAI_API_KEY=sk-...")
    if "claude" in lowered or "anthropic" in lowered:
        lines.append("ANTHROPIC_API_KEY=sk-ant-...")
    if "firebase" in lowered:
        lines.append("FIREBASE_API_KEY=...")
    if "stripe" in lowered:
        lines.extend(
            [
                "STRIPE_SECRET_KEY=sk_test_...",
                "STRIPE_WEBHOOK_SECRET=whsec_...",
                "NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...",
            ]
        )
    if "db" in lowered or "postgres" in lowered or "mysql" in lowered or "prisma" in lowered or "drizzle" in lowered:
        lines.append("DATABASE_URL=postgresql://user:pass@localhost:5432/dbname")
    if "redis" in lowered:
        lines.append("REDIS_URL=redis://localhost:6379")
    if "resend" in lowered or "email" in lowered or "smtp" in lowered:
        lines.extend(
            [
                "RESEND_API_KEY=re_...",
                "SMTP_HOST=smtp.example.com",
                "SMTP_PORT=587",
                "SMTP_USER=you@example.com",
                "SMTP_PASS=your-password",
            ]
        )
    if "vercel" in lowered:
        lines.append("VERCEL_TOKEN=your-vercel-token")

    if len(lines) == 1:
        lines.append("API_KEY=your-api-key")
        lines.append("BASE_URL=http://localhost:3000")

    return "\n".join(lines) + "\n"


def _build_vercel_json() -> str:
    return "{\n  \"framework\": \"nextjs\",\n  \"buildCommand\": \"next build\",\n  \"installCommand\": \"npm install\"\n}\n"


def _build_vercel_deploy_readme(stack: str) -> str:
    return f"""# Deploy to Vercel

This project is ready to be deployed to Vercel.

## Steps

1. Install the Vercel CLI if you haven't already:
   ```bash
   npm i -g vercel
   ```

2. Log in to Vercel:
   ```bash
   vercel login
   ```

3. Copy `.env.example` to `.env.local` and fill in your real keys:
   ```bash
   cp .env.example .env.local
   ```

4. Deploy:
   ```bash
   vercel --prod
   ```

5. Add the environment variables from `.env.local` in the Vercel dashboard under
   **Project Settings > Environment Variables**.

Detected stack: {stack or "Next.js"}
"""


def _prepare_fork(gh: GitHubClient, owner: str, repo: str, filters: dict) -> None:
    """Clone the fork, add Vercel-ready files, commit, push, and clean up."""
    token = gh.token
    clone_url = f"https://{token}@github.com/{owner}/{repo}.git"
    stack = filters.get("stack", "")
    language = filters.get("language", "")

    with tempfile.TemporaryDirectory() as tmp:
        repo_path = Path(tmp) / repo
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", clone_url, str(repo_path)],
                check=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
            is_nextjs = _is_nextjs_project(repo_path)
            modified_files = []

            env_path = repo_path / ".env.example"
            if not env_path.exists():
                env_path.write_text(
                    _build_env_example(stack, language, is_nextjs), encoding="utf-8"
                )
                modified_files.append(".env.example")

            if is_nextjs:
                vercel_json = repo_path / "vercel.json"
                if not vercel_json.exists():
                    vercel_json.write_text(_build_vercel_json(), encoding="utf-8")
                    modified_files.append("vercel.json")

            deploy_md = repo_path / "VERCEL_DEPLOY.md"
            if not deploy_md.exists():
                deploy_md.write_text(_build_vercel_deploy_readme(stack), encoding="utf-8")
                modified_files.append("VERCEL_DEPLOY.md")

            if not modified_files:
                print(f"      Nothing to add to {owner}/{repo} (already prepared).")
                return

            git_env = {
                **os.environ,
                "GIT_AUTHOR_NAME": "airepo",
                "GIT_AUTHOR_EMAIL": "airepo@localhost",
                "GIT_COMMITTER_NAME": "airepo",
                "GIT_COMMITTER_EMAIL": "airepo@localhost",
            }
            subprocess.run(
                ["git", "-C", str(repo_path), "add", *modified_files],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "-C", str(repo_path), "commit", "-m", "chore: prepare for Vercel deployment"],
                check=True,
                capture_output=True,
                text=True,
                env=git_env,
            )
            subprocess.run(
                ["git", "-C", str(repo_path), "push", "origin", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            )
            print(f"      ✅ Prepared {owner}/{repo} for Vercel: {', '.join(modified_files)}")
        except subprocess.CalledProcessError as e:
            print(f"      ⚠️ Could not modify {owner}/{repo}: {e.stderr or e.stdout}")
        except Exception as e:
            print(f"      ⚠️ Could not modify {owner}/{repo}: {e}")
