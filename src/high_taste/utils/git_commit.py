"""Utilities for fetching and parsing GitHub commit data."""

import os
import re

import httpx
from pydantic import BaseModel


class GitHubCommit(BaseModel):
    """GitHub commit data."""

    message: str
    diff: str
    url: str


def parse_github_url(url: str) -> tuple[str, str, str]:
    """Parse GitHub commit URL into owner, repo, commit_hash."""
    # Handle various GitHub URL formats
    patterns = [
        r"github\.com/([^/]+)/([^/]+)/commit/([a-f0-9]+)",
        r"github\.com/([^/]+)/([^/]+)/commits/([a-f0-9]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1), match.group(2), match.group(3)

    raise ValueError(f"Invalid GitHub commit URL: {url}")


async def fetch_commit_data(owner: str, repo: str, commit_hash: str) -> GitHubCommit:
    """Fetch commit data from GitHub API."""
    # Use GitHub API v3 for commit data
    base_url = "https://api.github.com"
    commit_url = f"{base_url}/repos/{owner}/{repo}/commits/{commit_hash}"

    headers = {}
    if github_token := os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"token {github_token}"

    async with httpx.AsyncClient() as client:
        # Fetch commit details
        response = await client.get(commit_url, headers=headers)
        response.raise_for_status()
        commit_data = response.json()

        # Fetch commit diff
        diff_response = await client.get(
            commit_url, headers={**headers, "Accept": "application/vnd.github.diff"}
        )
        diff_response.raise_for_status()

        return GitHubCommit(
            message=commit_data["commit"]["message"],
            diff=diff_response.text,
            url=f"https://github.com/{owner}/{repo}/commit/{commit_hash}",
        )
