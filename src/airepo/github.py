import base64

import requests


GITHUB_API = "https://api.github.com"


class GitHubClient:
    """Small GitHub API client for search, README fetch, and fork operations."""

    def __init__(self, token: str, username: str | None = None):
        self.token = token
        self.username = username
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    def _get(self, path: str, params: dict | None = None):
        url = f"{GITHUB_API}{path}"
        resp = self.session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, json: dict | None = None):
        url = f"{GITHUB_API}{path}"
        resp = self.session.post(url, json=json, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_user(self) -> dict:
        return self._get("/user")

    def search_repos(self, query: str, per_page: int = 100) -> list[dict]:
        data = self._get(
            "/search/repositories",
            params={
                "q": query,
                "sort": "updated",
                "order": "desc",
                "per_page": per_page,
            },
        )
        return data.get("items", [])

    def get_readme(self, owner: str, repo: str) -> str:
        try:
            data = self._get(f"/repos/{owner}/{repo}/readme")
            content = data.get("content", "")
            if data.get("encoding") == "base64":
                return base64.b64decode(content).decode("utf-8", errors="ignore")
            return content
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return ""
            raise

    def fork_repo(self, owner: str, repo: str, default_branch_only: bool = True) -> dict:
        return self._post(
            f"/repos/{owner}/{repo}/forks",
            json={"default_branch_only": default_branch_only},
        )

    def create_repo(self, name: str, description: str = "", private: bool = False) -> dict:
        """Create a new repository for the authenticated user."""
        return self._post(
            "/user/repos",
            json={
                "name": name,
                "description": description,
                "private": private,
                "auto_init": False,
            },
        )

    def authenticated_username(self) -> str:
        if self.username:
            return self.username
        return self.get_user()["login"]
