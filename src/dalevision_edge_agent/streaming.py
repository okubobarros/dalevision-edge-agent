import os
import subprocess
import logging
import signal
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class StreamManager:
    def __init__(self, streams_dir: str = "tmp_streams"):
        self.streams_dir = streams_dir
        self.processes: Dict[str, subprocess.Popen] = {}
        
        if not os.path.exists(self.streams_dir):
            os.makedirs(self.streams_dir)

    def start_hls(self, camera_id: str, rtsp_url: str):
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

stream_manager = StreamManager()
