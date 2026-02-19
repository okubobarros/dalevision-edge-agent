from __future__ import annotations

from pathlib import Path


def resolve_agent_bat_path(*, install_dir: Path | None, script_root: Path) -> Path:
    if install_dir is None or str(install_dir).strip() == "":
        install_dir = script_root
        fallback = script_root / ".." / "release" / "win"
        candidate = install_dir / "Start_DaleVision_Agent.bat"
        if not candidate.exists() and fallback.exists():
            install_dir = fallback.resolve()

    agent_bat = Path(install_dir) / "Start_DaleVision_Agent.bat"
    if not agent_bat.exists():
        files = []
        install_dir_path = Path(install_dir)
        if install_dir_path.exists():
            files = [
                item.name for item in install_dir_path.iterdir() if item.is_file()
            ]
        message = f"Arquivo nao encontrado: {agent_bat}"
        if files:
            message += f". Arquivos encontrados: {', '.join(sorted(files))}"
        raise FileNotFoundError(message)

    return agent_bat
