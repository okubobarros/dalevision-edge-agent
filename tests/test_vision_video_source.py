from __future__ import annotations

import pytest

from dalevision_edge_agent.vision.sources.video import VideoFrameSource


def test_video_source_missing_file_raises(tmp_path) -> None:
    path = tmp_path / "missing.mp4"
    source = VideoFrameSource(path=str(path), realtime=False, loop=False, logger=None)
    with pytest.raises(RuntimeError, match="nao encontrado|not found"):
        next(source.frames())
