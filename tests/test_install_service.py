from pathlib import Path

import pytest

from dalevision_edge_agent.install_service import resolve_agent_bat_path


def test_resolve_agent_bat_prefers_install_dir(tmp_path: Path) -> None:
    install_dir = tmp_path / "install"
    install_dir.mkdir()
    expected = install_dir / "03_INICIAR.bat"
    expected.write_text("echo ok")

    result = resolve_agent_bat_path(install_dir=install_dir, script_root=tmp_path)

    assert result == expected


def test_resolve_agent_bat_fallbacks_to_release_win(tmp_path: Path) -> None:
    script_root = tmp_path / "scripts"
    script_root.mkdir()
    fallback = tmp_path / "release" / "win"
    fallback.mkdir(parents=True)
    expected = fallback / "03_INICIAR.bat"
    expected.write_text("echo ok")

    result = resolve_agent_bat_path(install_dir=None, script_root=script_root)

    assert result == expected


def test_resolve_agent_bat_errors_with_listing(tmp_path: Path) -> None:
    script_root = tmp_path / "scripts"
    script_root.mkdir()
    missing_dir = tmp_path / "missing"
    missing_dir.mkdir()
    extra = missing_dir / "Outro.bat"
    extra.write_text("echo nope")

    with pytest.raises(FileNotFoundError) as excinfo:
        resolve_agent_bat_path(install_dir=missing_dir, script_root=script_root)

    message = str(excinfo.value)
    assert "Arquivo nao encontrado" in message
    assert "Outro.bat" in message
