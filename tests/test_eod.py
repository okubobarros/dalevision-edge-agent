import datetime as dt

from scripts.eod import build_markdown, parse_git_log


def test_parse_git_log():
    raw = (
        "abc123\t2026-02-19 10:00:00 +0000\tFix: heartbeat retry\n"
        "def456\t2026-02-19 12:30:00 +0000\tDocs: update README\n"
    )
    commits = parse_git_log(raw)
    assert len(commits) == 2
    assert commits[0]["hash"] == "abc123"
    assert commits[0]["subject"] == "Fix: heartbeat retry"


def test_build_markdown_with_commits_and_status():
    commits = [
        {"hash": "abc123", "date": "2026-02-19 10:00:00 +0000", "subject": "Fix bug"},
        {"hash": "def456", "date": "2026-02-19 12:30:00 +0000", "subject": "Docs"},
    ]
    status_lines = ["M README.md", "?? scripts/eod.py"]
    now = dt.datetime(2026, 2, 20, 18, 0)
    output = build_markdown(commits, status_lines, now, since_hours=24)
    assert "# EOD Draft - 2026-02-20" in output
    assert "## Commits" in output
    assert "`abc123`" in output
    assert "## Status" in output
    assert "M README.md" in output


def test_build_markdown_empty():
    output = build_markdown([], [], dt.datetime(2026, 2, 20, 9, 0), since_hours=24)
    assert "Sem commits no periodo" in output
    assert "Working tree limpo" in output
