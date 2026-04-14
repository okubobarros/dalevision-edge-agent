from pathlib import Path

from dalevision_edge_agent.release_registry import (
    build_release_download_url,
    infer_release_channel,
    normalize_release_tag,
    normalize_release_version,
    prepare_release_record,
    resolve_minimum_supported_version,
)


def test_normalize_release_tag_accepts_refs_prefix() -> None:
    assert normalize_release_tag("refs/tags/v1.0.26") == "v1.0.26"


def test_normalize_release_version_strips_leading_v() -> None:
    assert normalize_release_version("v1.0.26") == "1.0.26"


def test_infer_release_channel_defaults_to_stable() -> None:
    assert infer_release_channel("v1.0.26") == "stable"


def test_infer_release_channel_detects_beta() -> None:
    assert infer_release_channel("v1.0.27-beta.1") == "beta"


def test_build_release_download_url_uses_tag_and_asset_name() -> None:
    assert (
        build_release_download_url(
            repository="okubobarros/dalevision-edge-agent",
            tag="v1.0.26",
            asset_name="dalevision-edge-agent-windows.zip",
        )
        == "https://github.com/okubobarros/dalevision-edge-agent/releases/download/v1.0.26/dalevision-edge-agent-windows.zip"
    )


def test_resolve_minimum_supported_version_prefers_explicit_override() -> None:
    assert (
        resolve_minimum_supported_version(
            current_version="1.0.26",
            explicit_min_supported="1.0.24",
            existing_min_supported="1.0.25",
            active_version="1.0.25",
        )
        == "1.0.24"
    )


def test_resolve_minimum_supported_version_falls_back_to_active_version() -> None:
    assert (
        resolve_minimum_supported_version(
            current_version="1.0.26",
            active_version="1.0.25",
        )
        == "1.0.25"
    )


def test_prepare_release_record_builds_checksum_and_metadata(tmp_path: Path) -> None:
    asset_path = tmp_path / "dalevision-edge-agent-windows.zip"
    asset_path.write_bytes(b"dalevision-edge-agent")

    record = prepare_release_record(
        tag="v1.0.26",
        repository="okubobarros/dalevision-edge-agent",
        asset_path=asset_path,
    )

    assert record.version == "1.0.26"
    assert record.channel == "stable"
    assert record.asset_name == "dalevision-edge-agent-windows.zip"
    assert record.release_notes == "Edge Agent 1.0.26"
    assert record.download_url.endswith("/v1.0.26/dalevision-edge-agent-windows.zip")
    assert record.package_size_bytes == len(b"dalevision-edge-agent")
    assert len(record.package_sha256) == 64
