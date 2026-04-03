from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GITHUB_API_ROOT = "https://api.github.com"
USER_AGENT = "rsasaki-hub/0.1"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def dump_yaml_like(data: Any) -> str:
    # JSON is valid YAML 1.2 and keeps the repo dependency-free.
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def github_request(url: str, token: str | None = None) -> Any:
    headers = {
        "Accept": "application/vnd.github+json, application/vnd.github.mercy-preview+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"GitHub API request failed for {url}: {exc.code} {detail}") from exc


def fetch_public_repos(owner: str, token: str | None = None) -> list[dict[str, Any]]:
    repos: list[dict[str, Any]] = []
    page = 1
    while True:
        query = urllib.parse.urlencode(
            {
                "per_page": 100,
                "page": page,
                "type": "public",
                "sort": "updated",
            }
        )
        url = f"{GITHUB_API_ROOT}/users/{owner}/repos?{query}"
        payload = github_request(url, token=token)
        if not payload:
            break

        for item in payload:
            if item.get("private"):
                continue
            repos.append(
                {
                    "name": item["name"],
                    "description": item.get("description") or "",
                    "topics": item.get("topics") or [],
                    "language": item.get("language"),
                    "clone_url": item["clone_url"],
                    "html_url": item["html_url"],
                    "default_branch": item.get("default_branch") or "main",
                }
            )
        page += 1
    return repos


def write_repo_registry(owner: str, repos: list[dict[str, Any]], output_path: Path) -> dict[str, Any]:
    payload = {
        "owner": owner,
        "synced_at": utc_now(),
        "repos": repos,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(dump_yaml_like(payload), encoding="utf-8")
    return payload


def sync_repo_checkout(repo: dict[str, Any], checkout_root: Path) -> Path:
    checkout_root.mkdir(parents=True, exist_ok=True)
    target = checkout_root / repo["name"]
    clone_url = repo["clone_url"]
    default_branch = repo.get("default_branch") or "main"

    if target.exists():
        subprocess.run(
            ["git", "-C", str(target), "remote", "set-url", "origin", clone_url],
            check=True,
            capture_output=True,
            text=True,
        )
        pull_cmd = ["git", "-C", str(target), "pull", "--ff-only", "origin", default_branch]
        subprocess.run(pull_cmd, check=True, capture_output=True, text=True)
        return target

    clone_cmd = [
        "git",
        "clone",
        "--depth",
        "1",
        "--filter=blob:none",
        "--single-branch",
        "--branch",
        default_branch,
        clone_url,
        str(target),
    ]
    subprocess.run(clone_cmd, check=True, capture_output=True, text=True)
    return target


def sync_owner(owner: str, registry_path: Path, token: str | None = None) -> dict[str, Any]:
    repos = fetch_public_repos(owner, token=token)
    return write_repo_registry(owner=owner, repos=repos, output_path=registry_path)


def github_token_from_env() -> str | None:
    for key in ("GITHUB_TOKEN", "GH_TOKEN"):
        value = os.getenv(key)
        if value:
            return value
    return None

