import os
import subprocess
import logging
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class StreamManager:
    def __init__(self, streams_dir: str = "tmp_streams"):
        self.streams_dir = streams_dir
        self.processes: Dict[str, subprocess.Popen] = {}
        self.last_access: Dict[str, float] = {}
        
        if not os.path.exists(self.streams_dir):
            os.makedirs(self.streams_dir)

    def touch(self, camera_id: str):
        """Notifica que o stream está sendo assistido."""
        self.last_access[camera_id] = time.time()

    def start_hls(self, camera_id: str, rtsp_url: str):
        self.touch(camera_id)
        
        # Aproveita para limpar outros streams inativos (Inactivity Threshold: 60s)
        self._cleanup_inactive()

        if camera_id in self.processes:
            # Check if still running
            if self.processes[camera_id].poll() is None:
                return True
            else:
                self.stop_hls(camera_id)

        output_path = os.path.join(self.streams_dir, f"{camera_id}.m3u8")
        
        # FFmpeg command for low-latency HLS
        # -rtsp_transport tcp: Force TCP to avoid packet loss artifacts
        # -hls_time 2: 2-second segments
        # -hls_list_size 5: Keep 5 segments in the playlist
        # -hls_flags delete_segments: Self-cleanup
        cmd = [
            "ffmpeg",
            "-rtsp_transport", "tcp",
            "-i", rtsp_url,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-tune", "zerolatency",
            "-an",  # No audio to save CPU
            "-f", "hls",
            "-hls_time", "2",
            "-hls_list_size", "5",
            "-hls_flags", "delete_segments",
            output_path
        ]

        try:
            logger.info(f"Starting HLS for {camera_id}...")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            self.processes[camera_id] = process
            return True
        except Exception as e:
            logger.error(f"Failed to start FFmpeg for {camera_id}: {e}")
            return False

    def get_snapshot(self, camera_id: str, rtsp_url: str) -> Optional[str]:
        """
        Gera um snapshot JPEG único para identificação visual rápida.
        Retorna o caminho do arquivo gerado.
        """
        output_path = os.path.join(self.streams_dir, f"snap_{camera_id}.jpg")
        
        # FFmpeg command for single frame capture
        # -frames:v 1: Capture 1 frame
        # -q:v 2: High quality JPEG
        cmd = [
            "ffmpeg",
            "-rtsp_transport", "tcp",
            "-i", rtsp_url,
            "-frames:v", "1",
            "-q:v", "2",
            "-y", # Overwrite
            output_path
        ]

        try:
            logger.info(f"Generating snapshot for {camera_id}...")
            subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            if os.path.exists(output_path):
                return output_path
        except Exception as e:
            logger.error(f"Failed to generate snapshot for {camera_id}: {e}")
        
        return None

    def stop_hls(self, camera_id: str):
        if camera_id in self.processes:
            process = self.processes[camera_id]
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            del self.processes[camera_id]
            
            # Cleanup files
            m3u8_file = os.path.join(self.streams_dir, f"{camera_id}.m3u8")
            if os.path.exists(m3u8_file):
                try: os.remove(m3u8_file)
                except: pass

    def stop_all(self):
        ids = list(self.processes.keys())
        for cid in ids:
            self.stop_hls(cid)

    def _cleanup_inactive(self, threshold_seconds: int = 60):
        """Mata FFmpegs que não são acessados há algum tempo."""
        now = time.time()
        stale_ids = [
            cid for cid, last in self.last_access.items() 
            if (now - last) > threshold_seconds and cid in self.processes
        ]
        for cid in stale_ids:
            logger.info(f"Stream {cid} inactive for over {threshold_seconds}s. Stopping FFmpeg.")
            self.stop_hls(cid)

stream_manager = StreamManager()
