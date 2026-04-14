from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from dalevision_edge_agent.release_registry import prepare_release_record, sync_release_record


def _resolve_database_url(explicit_database_url: str) -> str:
    for candidate in (
        explicit_database_url,
        os.getenv("EDGE_RELEASES_DATABASE_URL", ""),
        os.getenv("SUPABASE_DB_URL", ""),
        os.getenv("SUPABASE_DATABASE_URL", ""),
        os.getenv("DATABASE_URL", ""),
    ):
        value = str(candidate or "").strip()
        if value:
            return value
    raise ValueError(
        "missing database URL. Configure EDGE_RELEASES_DATABASE_URL "
        "or pass --database-url."
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Upsert the current GitHub release into the edge_releases table."
    )
    parser.add_argument("--tag", default=os.getenv("GITHUB_REF_NAME", ""), help="Git tag, e.g. v1.0.26")
    parser.add_argument(
        "--repo",
        default=os.getenv("GITHUB_REPOSITORY", ""),
        help="GitHub repository in owner/name format",
    )
    parser.add_argument(
        "--asset-path",
        default=str(REPO_ROOT / "dalevision-edge-agent-windows.zip"),
        help="Local path to the release asset that was published to GitHub",
    )
    parser.add_argument(
        "--asset-name",
        default="",
        help="Asset name in GitHub Releases. Defaults to the filename from --asset-path.",
    )
    parser.add_argument("--channel", default="", help="Optional explicit channel override")
    parser.add_argument(
        "--release-notes",
        default="",
        help="Optional release_notes override stored in edge_releases",
    )
    parser.add_argument(
        "--min-supported-version",
        default=os.getenv("EDGE_RELEASES_MIN_SUPPORTED_VERSION", ""),
        help="Optional minimum supported version override",
    )
    parser.add_argument(
        "--database-url",
        default="",
        help="Optional Postgres connection string override",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print the resolved payload without writing to the database",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    record = prepare_release_record(
        tag=args.tag,
        repository=args.repo,
        asset_path=Path(args.asset_path),
        asset_name=args.asset_name,
        channel=args.channel,
        release_notes=args.release_notes,
    )

    if args.dry_run:
        print(
            json.dumps(
                {
                    "tag": record.tag,
                    "version": record.version,
                    "channel": record.channel,
                    "asset_name": record.asset_name,
                    "download_url": record.download_url,
                    "release_notes": record.release_notes,
                    "package_sha256": record.package_sha256,
                    "package_size_bytes": record.package_size_bytes,
                    "minimum_supported_version": args.min_supported_version or "<auto>",
                },
                indent=2,
            )
        )
        return 0

    database_url = _resolve_database_url(args.database_url)
    result = sync_release_record(
        database_url=database_url,
        record=record,
        minimum_supported_version=args.min_supported_version,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
