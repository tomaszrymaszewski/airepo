# airepo

A Python CLI, deployed as a Docker container, for scraping and forking AI-generated GitHub repositories or generating realistic, complex Next.js projects with the Gemini Antigravity agent.

## Modes

- **`scrape`** — find GitHub repositories likely authored by AI coding tools (Claude, Cursor, Copilot, ChatGPT, etc.), filter them with Gemini, and fork the chosen ones as public repos to your GitHub profile. Defaults to Next.js projects that are ready to host on Vercel after filling in API keys.
- **`generate`** — interactively pick a random Next.js/Vercel project template or describe a custom project, generate a maximally complex, realistic multi-page app (login/signup, PostgreSQL, Prisma, OAuth, RBAC, CI/CD, Docker Compose, many pages) with the Gemini Antigravity agent, and push it as a new public GitHub repo.

## Configuration

On first run, the CLI prompts for required API keys and persists them to `~/.config/airepo/.env`. After that, you can run without passing the keys again by mounting the same config directory.

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key. Used by both `scrape` and `generate`. |
| `GITHUB_TOKEN` | Yes | GitHub personal access token with `repo` scope. |
| `GITHUB_USERNAME` | No | GitHub username. If omitted, the tool fetches it from the GitHub API. |
| `GEMINI_MODEL` | No | Gemini model name. Defaults to `gemini-flash-latest`. Used by `scrape`. |
| `GEMINI_AGENT` | No | Managed Gemini agent name. Defaults to `antigravity-preview-05-2026`. |

## Install and run locally

```bash
pip install -e .
airepo --scrape
airepo --generate
```

## Build and run with Docker

### First run (interactive, prompts for keys)

```bash
docker build -t airepo .

# generate mode (uses Antigravity by default)
docker run -it --rm \
  -v airepo-config:/root/.config/airepo \
  airepo --generate

# scrape mode
docker run -it --rm \
  -v airepo-config:/root/.config/airepo \
  airepo --scrape
```

After the first run, your keys are saved in the `airepo-config` Docker volume. You can run the same commands again without passing keys.

### Explicit env vars (overrides persisted config)

```bash
docker run -it --rm \
  -e GEMINI_API_KEY="$GEMINI_API_KEY" \
  -e GITHUB_TOKEN="$GITHUB_TOKEN" \
  -e GITHUB_USERNAME="$GITHUB_USERNAME" \
  airepo --generate
```

## How `scrape` works

1. Defaults to TypeScript + Next.js + Vercel search filters (you can edit the defaults).
2. Asks for AI tool indicators and how many repos you want.
3. Uses Gemini to generate GitHub search queries.
4. Searches GitHub and fetches README excerpts for the top candidates.
5. Uses Gemini to rank the repos most likely to be AI-generated.
6. Lists the repos with clickable links.
7. Lets you select which repos to fork as public repos to your account.
8. After forking, optionally clones each fork and prepares it for Vercel:
   - `.env.example` with placeholder keys
   - `vercel.json` for Next.js projects
   - `VERCEL_DEPLOY.md` with deployment steps

## How `generate` works

1. Asks whether you want a random Next.js/Vercel project, a specific template, or a custom prompt.
2. Asks how many projects/repos you want to generate.
3. For each project, sends the prompt to the Gemini Antigravity agent via the Interactions API (`agent=antigravity-preview-05-2026`, `environment=remote`).
4. The built-in templates ask for maximally complex, realistic multi-page apps with features that naturally map to common security categories (access control, auth, data exposure, SQLi, XSS, command injection, path traversal, SSRF, XXE, SSTI, misconfig, secrets, dependencies) without intentionally introducing vulnerabilities.
5. Parses the generated files from the response.
6. Ensures `.env.example`, `vercel.json`, `README.md`, and `SECURITY_WARNING.md` are present.
7. Creates a new public GitHub repo and pushes the generated project.
8. Repeats for the requested number of projects.

## Notes

- The GitHub token needs `repo` scope to fork, create, and push repos.
- The `.env.example` and generated files only contain placeholder values; no real API keys are committed.
- AI-generated code may contain bugs or security issues. Generated projects include a `SECURITY_WARNING.md`; review before deploying.
- Use the `--config-dir` flag to change where credentials are persisted.

