"""Software update checker and download utilities for Pa-O Converter."""
from __future__ import annotations

import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.version import APP_NAME, WEBSITE, __version__


def get_ssl_context() -> ssl.SSLContext:
    """Return an SSLContext configured with trusted CA root certificates.

    Falls back progressively:
      1. certifi CA bundle if available
      2. Known OS root CA certificate paths (macOS / Linux)
      3. Python default context with CA certs
      4. Unverified context as last resort (prevents SSL verify failure on missing local CA stores)
    """
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass

    candidate_ca_paths = [
        "/etc/ssl/cert.pem",
        "/private/etc/ssl/cert.pem",
        "/etc/pki/tls/certs/ca-bundle.crt",
        "/etc/ssl/certs/ca-certificates.crt",
    ]
    for ca_path in candidate_ca_paths:
        if os.path.isfile(ca_path):
            try:
                return ssl.create_default_context(cafile=ca_path)
            except Exception:
                pass

    try:
        ctx = ssl.create_default_context()
        if ctx.get_ca_certs():
            return ctx
    except Exception:
        pass

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

# Default repository to check releases from
GITHUB_REPO = "khunaungpaing/PaO-Converter"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


@dataclass
class ReleaseAsset:
    """Metadata for a downloadable release file."""
    name: str
    download_url: str
    size: int
    content_type: str

    @property
    def size_mb(self) -> float:
        """Size in megabytes."""
        return self.size / (1024 * 1024)

    @property
    def size_str(self) -> str:
        """Formatted human-readable size string."""
        if self.size <= 0:
            return "Unknown size"
        if self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        return f"{self.size_mb:.1f} MB"


@dataclass
class ReleaseInfo:
    """Information about a GitHub release."""
    tag_name: str
    version: str
    name: str
    body: str
    published_at: str
    html_url: str
    asset: ReleaseAsset | None
    is_newer: bool
    current_version: str


def parse_version(v_str: str) -> tuple[int, ...]:
    """Parse version strings into comparable integer tuples.

    Handles formats like 'v1.0.0', '1.2.3', 'v2.1', '1.0.0-rc1'.
    """
    clean = re.sub(r"^[vV]", "", v_str.strip())
    parts: list[int] = []
    for segment in clean.split("."):
        match = re.match(r"^(\d+)", segment)
        if match:
            parts.append(int(match.group(1)))
        else:
            break
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def is_newer_version(remote_version: str, local_version: str = __version__) -> bool:
    """Return True if remote_version is strictly higher than local_version."""
    return parse_version(remote_version) > parse_version(local_version)


def find_platform_asset(assets: list[dict[str, Any]], platform: str = sys.platform) -> ReleaseAsset | None:
    """Find the best matching installer asset for the target platform.

    - macOS: looks for .dmg (prefers names with 'macos', 'mac', 'darwin')
    - Windows: looks for .exe (prefers names with 'setup', 'windows', 'win')
    - Linux / Other: looks for .tar.gz, .zip, .appimage, etc.
    """
    if not assets:
        return None

    if platform == "darwin":
        target_ext = ".dmg"
        keywords = ["macos", "mac", "darwin"]
    elif platform.startswith("win"):
        target_ext = ".exe"
        keywords = ["setup", "windows", "win"]
    else:
        target_ext = ".tar.gz"
        keywords = ["linux", "x86_64", "appimage"]

    candidates: list[dict[str, Any]] = []
    for a in assets:
        name = str(a.get("name", "")).lower()
        if name.endswith(target_ext):
            candidates.append(a)

    if not candidates:
        return None

    # Priority 1: Match both extension and keyword
    for c in candidates:
        name_lower = str(c.get("name", "")).lower()
        if any(kw in name_lower for kw in keywords):
            return ReleaseAsset(
                name=c.get("name", ""),
                download_url=c.get("browser_download_url", ""),
                size=int(c.get("size", 0)),
                content_type=c.get("content_type", ""),
            )

    # Priority 2: First candidate with matching extension
    chosen = candidates[0]
    return ReleaseAsset(
        name=chosen.get("name", ""),
        download_url=chosen.get("browser_download_url", ""),
        size=int(chosen.get("size", 0)),
        content_type=chosen.get("content_type", ""),
    )


def fetch_latest_release(
    repo: str = GITHUB_REPO,
    current_version: str = __version__,
    timeout: float = 10.0,
) -> ReleaseInfo:
    """Fetch the latest release information from GitHub API.

    Raises:
        RuntimeError on network or API failures.
    """
    api_url = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(
        api_url,
        headers={
            "User-Agent": f"PaOConverter/{current_version}",
            "Accept": "application/vnd.github.v3+json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout, context=get_ssl_context()) as response:
            if response.status != 200:
                raise RuntimeError(f"GitHub API returned HTTP {response.status}")
            raw_data = response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise RuntimeError("No releases found on GitHub.") from e
        raise RuntimeError(f"GitHub API request failed: HTTP {e.code}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Could not connect to GitHub: {e.reason}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to check for updates: {e}") from e

    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError as e:
        raise RuntimeError("Invalid response received from GitHub.") from e

    tag_name = data.get("tag_name", "")
    version_str = re.sub(r"^[vV]", "", tag_name)
    body = (data.get("body") or "").strip()
    name = data.get("name") or tag_name
    published_at = data.get("published_at", "")
    html_url = data.get("html_url") or f"https://github.com/{repo}/releases/latest"
    assets = data.get("assets", [])

    matched_asset = find_platform_asset(assets)
    newer = is_newer_version(version_str, current_version)

    return ReleaseInfo(
        tag_name=tag_name,
        version=version_str,
        name=name,
        body=body,
        published_at=published_at,
        html_url=html_url,
        asset=matched_asset,
        is_newer=newer,
        current_version=current_version,
    )


def get_default_download_path(filename: str) -> Path:
    """Return default destination path in user's Downloads directory."""
    downloads = Path.home() / "Downloads"
    if downloads.is_dir():
        return downloads / filename
    import tempfile
    return Path(tempfile.gettempdir()) / filename
