#!/usr/bin/env python3
"""Generate a small static SVG stats card for the ACrispyCookie profile README.

Uses GitHub's public REST API by default. If GITHUB_TOKEN is set, it is used to
avoid low unauthenticated rate limits.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape

USER = "ACrispyCookie"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "github-stats.svg"


def gh_json(url: str):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ACrispyCookie-profile-stats",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def all_repos():
    repos = []
    page = 1
    while True:
        data = gh_json(
            f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}&sort=updated&type=owner"
        )
        if not data:
            return repos
        repos.extend(data)
        page += 1


def main() -> int:
    user = gh_json(f"https://api.github.com/users/{USER}")
    repos = [r for r in all_repos() if not r.get("fork")]
    public_repos = len(repos)
    stars = sum(r.get("stargazers_count", 0) for r in repos)
    forks = sum(r.get("forks_count", 0) for r in repos)
    langs = Counter(r.get("language") for r in repos if r.get("language"))
    top_langs = " · ".join(lang for lang, _ in langs.most_common(5)) or "C · C++ · Python · Java"
    updated = max((r.get("pushed_at") or "" for r in repos), default="")[:10]

    lines = [
        ("public repos", str(public_repos), "#58a6ff"),
        ("stars", str(stars), "#d29922"),
        ("forks", str(forks), "#3fb950"),
        ("followers", str(user.get("followers", 0)), "#bc8cff"),
    ]

    metric_cards = []
    for i, (label, value, color) in enumerate(lines):
        x = 44 + i * 188
        metric_cards.append(
            f'<g transform="translate({x} 116)">'
            f'<rect width="156" height="84" rx="10" fill="#161b22" stroke="#30363d"/>'
            f'<text x="18" y="32" class="label">{escape(label)}</text>'
            f'<text x="18" y="66" class="value" fill="{color}">{escape(value)}</text>'
            f'</g>'
        )

    svg = f'''<svg width="840" height="260" viewBox="0 0 840 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="GitHub profile stats for {USER}">
  <defs>
    <style>
      .bg{{fill:#0d1117}}.panel{{fill:#0d1117;stroke:#30363d;stroke-width:2}}.mono{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}.title{{font-size:24px;font-weight:800;fill:#f0f6fc}}.label{{font-size:13px;fill:#8b949e}}.value{{font-size:30px;font-weight:800}}.small{{font-size:14px;fill:#c9d1d9}}
    </style>
  </defs>
  <rect width="840" height="260" rx="18" class="bg"/>
  <rect x="1" y="1" width="838" height="258" rx="18" class="panel"/>
  <text x="44" y="52" class="mono title">GitHub snapshot</text>
  <text x="44" y="82" class="mono small">public repos · practical systems projects · current focus: GPGPU + homelab</text>
  {''.join(metric_cards)}
  <text x="44" y="232" class="mono small">top public languages: {escape(top_langs)} · latest public push: {escape(updated or 'n/a')}</text>
</svg>
'''
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg)
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
