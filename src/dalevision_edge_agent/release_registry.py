from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import psycopg
except ImportError:  # pragma: no cover - exercised via runtime error path
    psycopg = None


_PRE_RELEASE_CHANNELS = ("canary", "alpha", "beta", "rc", "preview")


@dataclass(frozen=True)
class ReleaseRecord:
    tag: str
    version: str
    channel: str
    asset_name: str
    asset_path: Path
    download_url: str
    release_notes: str
    package_sha256: str
    package_size_bytes: int


def normalize_release_tag(tag: str) -> str:
    raw = str(tag or "").strip()
    if raw.startswith("refs/tags/"):
        raw = raw[len("refs/tags/") :]
    if not raw:
        raise ValueError("release tag is required")
    return raw


def normalize_release_version(tag: str) -> str:
    normalized_tag = normalize_release_tag(tag)
    version = normalized_tag[1:] if normalized_tag.lower().startswith("v") else normalized_tag
    version = version.strip()
    if not version or not re.search(r"\d", version):
        raise ValueError(f"invalid release tag: {tag}")
    return version


def infer_release_channel(tag: str, explicit_channel: str = "") -> str:
    if explicit_channel.strip():
        return explicit_channel.strip().lower()

    lowered = normalize_release_tag(tag).lower()
    for channel in _PRE_RELEASE_CHANNELS:
        token = f"-{channel}"
        dotted = f".{channel}"
        if token in lowered or dotted in lowered or lowered.endswith(channel):
            return channel
    return "stable"


def build_release_download_url(*, repository: str, tag: str, asset_name: str) -> str:
    repo = str(repository or "").strip().strip("/")
    if not repo or "/" not in repo:
        raise ValueError("repository must be in owner/name format")
    normalized_tag = normalize_release_tag(tag)
    safe_asset = str(asset_name or "").strip()
    if not safe_asset:
        raise ValueError("asset_name is required")
    return f"https://github.com/{repo}/releases/download/{normalized_tag}/{safe_asset}"


def build_release_notes(*, version: str, channel: str) -> str:
    normalized_version = normalize_release_version(version)
    normalized_channel = str(channel or "stable").strip().lower() or "stable"
    if normalized_channel == "stable":
        return f"Edge Agent {normalized_version}"
    return f"Edge Agent {normalized_version} ({normalized_channel})"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest().upper()


def prepare_release_record(
    *,
    tag: str,
    repository: str,
    asset_path: Path,
    asset_name: str = "",
    channel: str = "",
    release_notes: str = "",
) -> ReleaseRecord:
    resolved_asset_path = Path(asset_path).resolve()
    if not resolved_asset_path.exists():
        raise FileNotFoundError(f"release asset not found: {resolved_asset_path}")

    normalized_tag = normalize_release_tag(tag)
    version = normalize_release_version(normalized_tag)
    resolved_asset_name = str(asset_name or resolved_asset_path.name).strip()
    resolved_channel = infer_release_channel(normalized_tag, explicit_channel=channel)
    resolved_release_notes = release_notes.strip() or build_release_notes(
        version=version,
        channel=resolved_channel,
    )

    return ReleaseRecord(
        tag=normalized_tag,
        version=version,
        channel=resolved_channel,
        asset_name=resolved_asset_name,
        asset_path=resolved_asset_path,
        download_url=build_release_download_url(
            repository=repository,
            tag=normalized_tag,
            asset_name=resolved_asset_name,
        ),
        release_notes=resolved_release_notes,
        package_sha256=sha256_file(resolved_asset_path),
        package_size_bytes=resolved_asset_path.stat().st_size,
    )


def resolve_minimum_supported_version(
    *,
    current_version: str,
    explicit_min_supported: str = "",
    existing_min_supported: str = "",
    active_version: str = "",
) -> str:
    for candidate in (explicit_min_supported, existing_min_supported, active_version):
        value = str(candidate or "").strip()
        if value:
            return normalize_release_version(value)
    return normalize_release_version(current_version)


def sync_release_record(
    *,
    database_url: str,
    record: ReleaseRecord,
    minimum_supported_version: str = "",
) -> dict[str, Any]:
    if psycopg is None:
        raise RuntimeError(
            "psycopg is required to sync edge_releases. Install with "
            "`python -m pip install \"psycopg[binary]>=3.2.0\"`."
        )

    db_url = str(database_url or "").strip()
    if not db_url:
        raise ValueError("database_url is required")

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id::text, COALESCE(NULLIF(TRIM(minimum_supported_version), ''), '')
                FROM edge_releases
                WHERE channel = %s AND current_version = %s
                ORDER BY COALESCE(updated_at, created_at) DESC NULLS LAST, created_at DESC NULLS LAST
                LIMIT 1
                """,
                (record.channel, record.version),
            )
            existing_row = cur.fetchone()

            cur.execute(
                """
                SELECT current_version
                FROM edge_releases
                WHERE channel = %s
                  AND current_version <> %s
                  AND COALESCE(is_active, FALSE) = TRUE
                ORDER BY COALESCE(updated_at, created_at) DESC NULLS LAST, created_at DESC NULLS LAST
                LIMIT 1
                """,
                (record.channel, record.version),
            )
            active_row = cur.fetchone()

            resolved_min_supported = resolve_minimum_supported_version(
                current_version=record.version,
                explicit_min_supported=minimum_supported_version,
                existing_min_supported=(existing_row[1] if existing_row else ""),
                active_version=(active_row[0] if active_row else ""),
            )

            if existing_row:
                canonical_id = str(existing_row[0])
                cur.execute(
                    """
                    UPDATE edge_releases
                    SET minimum_supported_version = %s,
                        download_url = %s,
                        release_notes = %s,
                        is_active = TRUE,
                        package_sha256 = %s,
                        package_size_bytes = %s,
                        updated_at = NOW()
                    WHERE id::text = %s
                    """,
                    (
                        resolved_min_supported,
                        record.download_url,
                        record.release_notes,
                        record.package_sha256,
                        record.package_size_bytes,
                        canonical_id,
                    ),
                )
                inserted = False
            else:
                cur.execute(
                    """
                    INSERT INTO edge_releases (
                        channel,
                        current_version,
                        minimum_supported_version,
                        download_url,
                        release_notes,
                        is_active,
                        package_sha256,
                        package_size_bytes,
                        created_at,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, TRUE, %s, %s, NOW(), NOW())
                    RETURNING id::text
                    """,
                    (
                        record.channel,
                        record.version,
                        resolved_min_supported,
                        record.download_url,
                        record.release_notes,
                        record.package_sha256,
                        record.package_size_bytes,
                    ),
                )
                canonical_id = str(cur.fetchone()[0])
                inserted = True

            cur.execute(
                """
                UPDATE edge_releases
                SET is_active = FALSE,
                    updated_at = NOW()
                WHERE channel = %s
                  AND id::text <> %s
                  AND COALESCE(is_active, FALSE) = TRUE
                """,
                (record.channel, canonical_id),
            )
            deactivated_other_versions = cur.rowcount

            cur.execute(
                """
                UPDATE edge_releases
                SET is_active = FALSE,
                    updated_at = NOW()
                WHERE channel = %s
                  AND current_version = %s
                  AND id::text <> %s
                  AND COALESCE(is_active, TRUE) = TRUE
                """,
                (record.channel, record.version, canonical_id),
            )
            deactivated_duplicates = cur.rowcount

            conn.commit()

    return {
        "id": canonical_id,
        "channel": record.channel,
        "current_version": record.version,
        "minimum_supported_version": resolved_min_supported,
        "download_url": record.download_url,
        "release_notes": record.release_notes,
        "package_sha256": record.package_sha256,
        "package_size_bytes": record.package_size_bytes,
        "inserted": inserted,
        "deactivated_other_versions": deactivated_other_versions,
        "deactivated_duplicates": deactivated_duplicates,
    }
