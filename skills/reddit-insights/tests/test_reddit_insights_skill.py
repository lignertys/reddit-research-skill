"""
Tests for the reddit-insights optional skill.

In the hermes-agent repo this file belongs at
tests/skills/test_reddit_insights_skill.py, with the skill itself at
optional-skills/research/reddit-insights/ (REPO_ROOT below assumes that).

Validates:
  - SKILL.md frontmatter meets the hardline authoring standards
  - the shipped scripts/reddapi.py builds correct requests (urlopen mocked,
    no live network)
  - the key is never written into the request URL or body
"""
from __future__ import annotations

import importlib.util
import io
import json
import re
import urllib.error
from pathlib import Path
from unittest import mock

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / "optional-skills" / "research" / "reddit-insights"
SCRIPT = SKILL_DIR / "scripts" / "reddapi.py"


@pytest.fixture(scope="module")
def frontmatter() -> dict:
    src = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    m = re.search(r"^---\n(.*?)\n---", src, re.DOTALL)
    assert m, "SKILL.md missing YAML frontmatter"
    return yaml.safe_load(m.group(1))


@pytest.fixture(scope="module")
def body() -> str:
    src = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    return re.sub(r"^---\n.*?\n---\n", "", src, count=1, flags=re.DOTALL)


@pytest.fixture(scope="module")
def reddapi():
    spec = importlib.util.spec_from_file_location("reddapi_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --- frontmatter -----------------------------------------------------------


def test_skill_dir_exists() -> None:
    assert SKILL_DIR.is_dir(), f"missing skill dir: {SKILL_DIR}"
    assert SCRIPT.is_file(), f"missing helper script: {SCRIPT}"
    assert (SKILL_DIR / "references" / "api-reference.md").is_file()


def test_description_is_one_short_sentence(frontmatter) -> None:
    desc = frontmatter["description"]
    assert len(desc) <= 60, f"description is {len(desc)} chars (limit 60): {desc!r}"
    assert desc.endswith("."), "description must end with a period"
    # a sentence break is a period followed by whitespace; "reddapi.dev" is not one
    assert re.search(r"\.\s", desc) is None, "description must be a single sentence"


def test_has_required_frontmatter_fields(frontmatter) -> None:
    for field in ("name", "description", "version", "author", "license", "platforms"):
        assert field in frontmatter, f"missing required field: {field}"
    assert frontmatter["name"] == "reddit-insights"
    hermes = frontmatter["metadata"]["hermes"]
    for field in ("tags", "category", "related_skills"):
        assert field in hermes, f"missing metadata.hermes.{field}"


def test_platforms_cover_all_three(frontmatter) -> None:
    """The helper is stdlib only, so nothing narrows the platform list."""
    assert set(frontmatter["platforms"]) == {"linux", "macos", "windows"}


def test_body_uses_modern_section_order(body) -> None:
    expected = [
        "When to Use",
        "Prerequisites",
        "How to Run",
        "Quick Reference",
        "Procedure",
        "Pitfalls",
        "Verification",
    ]
    found = re.findall(r"^## (.+)$", body, re.MULTILINE)
    assert found == expected, f"section order is {found}"


def test_prose_does_not_headline_raw_shell_utilities(body) -> None:
    """Prose points at the shipped script, not at curl/grep/cat/sed."""
    wrapped = r"curl|grep|cat|head|tail|sed|awk|find|ls"
    commands = re.findall(rf"^\s*(?:{wrapped})\b", body, re.MULTILINE)
    assert not commands, f"code blocks invoke wrapped shell utilities: {commands}"
    inline = re.findall(rf"`({wrapped})`", body)
    assert not inline, f"prose names wrapped shell utilities as tools: {inline}"
    assert "`terminal`" in body, "prose must name the native terminal tool"


# --- request building (network mocked) -------------------------------------


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


def _capture(reddapi, monkeypatch, payload=None):
    """Run a call with urlopen mocked; return the captured Request."""
    monkeypatch.setenv("REDDAPI_API_KEY", "test-key-do-not-log")
    seen = {}

    def fake_urlopen(req, timeout=None):
        seen["req"] = req
        return _Resp(json.dumps(payload or {"success": True, "data": {}}).encode())

    monkeypatch.setattr(reddapi.urllib.request, "urlopen", fake_urlopen)
    return seen


def test_vector_search_posts_json_with_dates(reddapi, monkeypatch) -> None:
    seen = _capture(reddapi, monkeypatch)
    reddapi.vector("pm tools", limit=100, start_date="2026-01-01", end_date="2026-07-30")
    req = seen["req"]
    assert req.full_url.endswith("/api/v1/search/vector")
    assert req.get_method() == "POST"
    # missing this header is a 403, not a plan limit
    assert req.headers["Content-type"] == "application/json"
    body = json.loads(req.data)
    assert body == {"query": "pm tools", "limit": 100,
                    "start_date": "2026-01-01", "end_date": "2026-07-30"}


def test_limit_is_clamped_to_server_ceiling(reddapi, monkeypatch) -> None:
    seen = _capture(reddapi, monkeypatch)
    reddapi.vector("anything", limit=500)
    assert json.loads(seen["req"].data)["limit"] == 100


def test_semantic_omits_summary_unless_requested(reddapi, monkeypatch) -> None:
    seen = _capture(reddapi, monkeypatch)
    reddapi.semantic("remote team tools", limit=20)
    assert "include_summary" not in json.loads(seen["req"].data)

    seen = _capture(reddapi, monkeypatch)
    reddapi.semantic("remote team tools", limit=20, include_summary=True)
    assert json.loads(seen["req"].data)["include_summary"] is True


def test_trends_always_sends_a_json_body(reddapi, monkeypatch) -> None:
    """An empty POST body 500s, so the body must never be None."""
    seen = _capture(reddapi, monkeypatch)
    reddapi.trends()
    req = seen["req"]
    assert req.get_method() == "POST"
    assert json.loads(req.data) == {"limit": 20}


def test_subreddit_listing_prefers_the_free_route(reddapi, monkeypatch) -> None:
    seen = _capture(reddapi, monkeypatch)
    reddapi.subreddits(search="programming", limit=100)
    req = seen["req"]
    assert "/api/subreddits" in req.full_url and "/api/v1/" not in req.full_url
    assert "Authorization" not in req.headers

    seen = _capture(reddapi, monkeypatch)
    reddapi.subreddits(search="programming", sort="subscribers")
    assert "/api/v1/subreddits" in seen["req"].full_url


def test_subreddit_detail_strips_the_r_prefix(reddapi, monkeypatch) -> None:
    seen = _capture(reddapi, monkeypatch)
    reddapi.subreddit("r/programming")
    assert seen["req"].full_url.endswith("/api/subreddits/programming")


def test_key_travels_in_the_header_only(reddapi, monkeypatch) -> None:
    seen = _capture(reddapi, monkeypatch)
    reddapi.vector("anything")
    req = seen["req"]
    assert req.headers["Authorization"] == "Bearer test-key-do-not-log"
    assert "test-key-do-not-log" not in req.full_url
    assert b"test-key-do-not-log" not in req.data


def test_missing_key_raises_before_any_request(reddapi, monkeypatch) -> None:
    monkeypatch.delenv("REDDAPI_API_KEY", raising=False)
    called = []
    monkeypatch.setattr(reddapi.urllib.request, "urlopen",
                        lambda *a, **k: called.append(1))
    with pytest.raises(reddapi.MissingKey):
        reddapi.vector("anything")
    assert not called, "must not hit the network without a key"


def test_missing_key_exits_2(reddapi, monkeypatch) -> None:
    monkeypatch.delenv("REDDAPI_API_KEY", raising=False)
    assert reddapi.main(["vector", "anything"]) == 2


def test_http_error_does_not_leak_headers(reddapi, monkeypatch) -> None:
    monkeypatch.setenv("REDDAPI_API_KEY", "test-key-do-not-log")

    def boom(req, timeout=None):
        raise urllib.error.HTTPError(
            req.full_url, 429, "Too Many Requests", {}, io.BytesIO(b"quota exhausted")
        )

    monkeypatch.setattr(reddapi.urllib.request, "urlopen", boom)
    with pytest.raises(reddapi.ApiError) as excinfo:
        reddapi.vector("anything")
    message = str(excinfo.value)
    assert "429" in message and "quota exhausted" in message
    assert "test-key-do-not-log" not in message


def test_error_envelope_is_raised(reddapi, monkeypatch) -> None:
    _capture(reddapi, monkeypatch, payload={"success": False, "error": "bad query"})
    with pytest.raises(reddapi.ApiError):
        reddapi.vector("")


# --- output rendering ------------------------------------------------------


def test_digest_reads_either_score_field(reddapi) -> None:
    vector_hit = {"data": {"results": [
        {"subreddit": "rust", "upvotes": 10, "comments": 2, "title": "t",
         "url": "u", "created": "2026-05-01T00:00:00Z", "similarity_score": 0.87}
    ], "total": 1, "processing_time_ms": 340}}
    semantic_hit = json.loads(json.dumps(vector_hit))
    semantic_hit["data"]["results"][0].pop("similarity_score")
    semantic_hit["data"]["results"][0]["relevance"] = 0.72

    assert "[0.87]" in reddapi.digest_search(vector_hit)
    assert "[0.72]" in reddapi.digest_search(semantic_hit)


def test_digest_handles_empty_results(reddapi) -> None:
    assert reddapi.digest_search({"data": {"results": []}}) == "(no results)"
    assert "no trends" in reddapi.digest_trends({"data": {"trends": []}})
