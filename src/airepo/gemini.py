import json
import re

from google import genai
from google.genai import types

from airepo.config import Config


class GeminiClient:
    """Thin wrapper around the Google GenAI API for airepo tasks."""

    def __init__(self, config: Config):
        self.client = genai.Client(api_key=config.gemini_api_key)
        self.model = config.gemini_model

    def _generate(self, prompt: str, temperature: float = 0.2) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=temperature),
        )
        return response.text or ""

    def generate_text(self, prompt: str, temperature: float = 0.2) -> str:
        """Generate raw text from a prompt."""
        return self._generate(prompt, temperature)

    def run_agent(self, agent: str, prompt: str, timeout: int = 300) -> str:
        """Run a managed Gemini agent via the Interactions API.

        The agent is expected to return a text response containing the generated
        project files in the same `## File: path` markdown format.
        """
        interaction = self.client.interactions.create(
            agent=agent,
            input=prompt,
            environment="remote",
            timeout=timeout,
        )
        return interaction.output_text or ""

    def generate_search_queries(self, filters: dict) -> list[str]:
        """Ask Gemini for a list of GitHub search query strings."""
        prompt = f"""You are a GitHub search assistant. Given the user filters below, generate 3-5 effective GitHub search queries (as a JSON array of strings) to find small, self-contained repositories likely created with AI coding tools (Claude, Cursor, GitHub Copilot, ChatGPT, etc.).

Each query must be a single string using valid GitHub search syntax (e.g. "language:python", "stars:>5", "topic:nextjs", "created:>2024-01-01", "AI generated", etc.). Favor repos that look like small full-stack projects, demo apps, or starter templates.

Filters:
- Primary language: {filters.get('language') or 'any'}
- Tech stack / frameworks: {filters.get('stack') or 'any'}
- AI tool indicators: {filters.get('ai_indicators') or 'any'}
- Extra keywords / description: {filters.get('keywords') or 'none'}

Return ONLY a JSON array of strings, e.g.:
["stars:>10 language:python AI generated starter", "topic:nextjs topic:supabase AI built"]
"""
        text = self._generate(prompt)
        return _extract_json_array(text)

    def filter_ai_repos(self, repos: list[dict], count: int) -> list[dict]:
        """Ask Gemini to rank the repos most likely to be AI-generated."""
        if not repos:
            return []

        payload = []
        for r in repos:
            payload.append(
                {
                    "full_name": r["full_name"],
                    "html_url": r["html_url"],
                    "description": r.get("description") or "",
                    "language": r.get("language") or "",
                    "topics": r.get("topics") or [],
                    "readme_excerpt": (r.get("readme") or "")[:500],
                }
            )

        prompt = f"""You are a repository classifier. Given the list of GitHub repositories below, identify the top {count} repositories most likely to have been authored (fully or partly) by AI coding tools such as Claude, Cursor, GitHub Copilot, ChatGPT, etc.

For each repo, consider:
- README content mentioning AI tools, "AI-generated", "built with AI", etc.
- Description or topics suggesting AI involvement
- Small, self-contained project scope (good for forking and running)

Return ONLY a JSON array of up to {count} objects. Each object must have:
- full_name (string)
- html_url (string)
- description (string)
- reason (string, brief)

Input repositories:
{json.dumps(payload, indent=2)}
"""
        text = self._generate(prompt)
        results = _extract_json_array(text)
        return results[:count] if isinstance(results, list) else []


def _extract_json_array(text: str) -> list:
    """Extract a JSON array from Markdown code blocks or raw text."""
    if not text:
        return []

    # Extract from ```json ... ``` or ``` ... ``` blocks
    match = re.search(r"```(?:json)?\s*\n?(\[.*?\])\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)

    text = text.strip().strip("`")

    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass

    # Fallback: find the first [ ... ] span
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

    return []
