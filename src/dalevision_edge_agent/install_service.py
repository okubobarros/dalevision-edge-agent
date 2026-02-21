from __future__ import annotations

from pathlib import Path

CANDIDATES = [
    "03_INICIAR.bat",
    "Start_Agent.bat",
    "Start_DaleVision_Agent.bat",
    "01_INICIAR_DALEVISION.bat",
    "01 - Iniciar Agent.bat",
]


def resolve_agent_bat_path(*, install_dir: Path | None, script_root: Path) -> Path:
    if install_dir is None or str(install_dir).strip() == "":
        install_dir = script_root
        fallback = script_root / ".." / "release" / "win"
        if fallback.exists():
            for name in CANDIDATES:
                candidate = fallback / name
                if candidate.exists():
                    install_dir = fallback.resolve()
                    break

    install_dir_path = Path(install_dir)
    for name in CANDIDATES:
        agent_bat = install_dir_path / name
        if agent_bat.exists():
            return agent_bat

    files = []
    if install_dir_path.exists():
        files = [item.name for item in install_dir_path.iterdir() if item.is_file()]
    message = f"Arquivo nao encontrado: {install_dir_path / CANDIDATES[0]}"
    if files:
        message += f". Arquivos encontrados: {', '.join(sorted(files))}"
    raise FileNotFoundError(message)
