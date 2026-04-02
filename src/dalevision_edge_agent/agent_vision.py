import os
import sys
import time
import logging
import traceback
import threading
from datetime import datetime, timezone
from pathlib import Path

# Add src to path if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dalevision_edge_agent.vision.worker import VisionWorker
from dalevision_edge_agent.env import DaleSettings
from dalevision_edge_agent.setup_api import serve_setup_api
from dalevision_edge_agent.streaming import stream_manager

def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger("agent_vision")

def update_heartbeat():
    hb_path = Path("vision_heartbeat.tmp")
    hb_path.write_text(str(time.time()), encoding="utf-8")

def main():
    logger = setup_logger()
    logger.info("AGENT_VISION v1.1 starting...")
    
    settings = DaleSettings.from_env()
    
    try:
        worker = VisionWorker(
            cloud_base_url=settings.cloud_base_url,
            store_id=settings.store_id,
            edge_token=settings.edge_token,
            logger=logger
        )
        
        if not worker.cfg.enabled:
            logger.error("VISION_ENABLED is 0. Exiting.")
            return 1

        # Discovery provider for Setup API
        def discovery_provider():
            # Returns internal camera list for streaming / status
            # In a real scenario, this would scan the network too.
            return getattr(worker, "_last_cameras_list", [])

        # Start Setup API in a background thread
        # Port 8787 is used by the frontend to talk to edge
        api_thread = threading.Thread(
            target=serve_setup_api,
            kwargs={
                "host": "0.0.0.0",
                "port": 8787,
                "discovery_provider": discovery_provider,
                "logger": logger
            },
            daemon=True
        )
        api_thread.start()
        logger.info("Setup API thread started on port 8787")

        logger.info("Vision worker loop starting...")
        while True:
            try:
                worker.tick_once()
                
                # Keep track of cameras for the API
                # worker._last_cameras_list is updated inside tick_once fetch
                
                update_heartbeat()
                time.sleep(worker.cfg.poll_seconds)
            except Exception as e:
                logger.error("Vision worker tick failed: %s", traceback.format_exc())
                time.sleep(5)
                
    except Exception as e:
        logger.error("Fatal error in agent_vision: %s", traceback.format_exc())
        return 1
    finally:
        stream_manager.stop_all()

if __name__ == "__main__":
    sys.exit(main())
