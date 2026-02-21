from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def parse_git_log(raw: str) -> list[dict[str, str]]:
    commits: list[dict[str, str]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        commits.append(
            {
                "hash": parts[0],
                "date": parts[1],
                "subject": parts[2],
            }
        )
    return commits


def build_markdown(
    commits: list[dict[str, str]],
    status_lines: list[str],
    now: dt.datetime,
    since_hours: int,
) -> str:
    date_str = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%Y-%m-%d %H:%M")
    lines: list[str] = [
        f"# EOD Draft - {date_str}",
        "",
        f"Janela: ultimas {since_hours} horas",
        f"Gerado em: {timestamp}",
        "",
        "## Commits",
    ]

    if commits:
        for item in commits:
            lines.append(
                f"- `{item['hash']}` {item['date']} - {item['subject']}"
            )
    else:
        lines.append("- Sem commits no periodo.")

    lines.append("")
    lines.append("## Status")
    if status_lines:
        lines.append("```")
        lines.extend(status_lines)
        lines.append("```")
    else:
        lines.append("Working tree limpo.")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera um draft EOD com commits recentes e status do repo."
    )
    parser.add_argument(
        "--since-hours",
        type=int,
        default=24,
        help="Janela de tempo em horas para commits (padrao: 24).",
    )
    args = parser.parse_args()

    try:
        log_raw = run_git(
            [
                "log",
                f"--since={args.since_hours}.hours",
                "--pretty=format:%h\t%ad\t%s",
                "--date=iso",
            ]
        )
        status_raw = run_git(["status", "--short"])
    except RuntimeError as exc:
        print(f"Erro ao executar git: {exc}", file=sys.stderr)
        return 1

    commits = parse_git_log(log_raw)
    status_lines = [line for line in status_raw.splitlines() if line.strip()]
    output = build_markdown(
        commits=commits,
        status_lines=status_lines,
        now=dt.datetime.now(),
        since_hours=args.since_hours,
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
