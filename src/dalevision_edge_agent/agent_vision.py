from __future__ import annotations
import os
import sys
import time
import logging
import traceback
from datetime import datetime, timezone
from pathlib import Path

# Add src to path if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dalevision_edge_agent.vision.worker import VisionWorker
from dalevision_edge_agent.env import DaleSettings

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
    logger.info("AGENT_VISION starting...")
    
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

        logger.info("Vision worker loop starting...")
        while True:
            try:
                worker.tick_once()
                update_heartbeat()
                time.sleep(worker.cfg.poll_seconds)
            except Exception as e:
                logger.error("Vision worker tick failed: %s", traceback.format_exc())
                time.sleep(5)
                
    except Exception as e:
        logger.error("Fatal error in agent_vision: %s", traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
