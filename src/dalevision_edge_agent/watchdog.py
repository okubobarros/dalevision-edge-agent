from __future__ import annotations
import os
import sys
import time
import subprocess
import logging
import traceback
from pathlib import Path

def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [WATCHDOG] %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler("watchdog.log", encoding="utf-8")]
    )
    return logging.getLogger("watchdog")

logger = setup_logger()

def check_heartbeat(max_age_seconds: int = 60) -> bool:
    hb_path = Path("vision_heartbeat.tmp")
    if not hb_path.exists():
        return False
    
    try:
        ts = hb_path.read_text(encoding="utf-8")
        if not ts: return False
        age = time.time() - float(ts.strip())
        return age <= max_age_seconds
    except:
        return False

def main():
    logger.info("WATCHDOG starting up.")
    restarts = 0
    max_restarts = 10
    
    while restarts < max_restarts:
        logger.info("Starting agent_vision (attempt %s/%s)...", restarts + 1, max_restarts)
        
        # Start agent_vision.py
        proc = subprocess.Popen([sys.executable, "agent_vision.py"])
        
        while proc.poll() is None:
            time.sleep(30)
            if not check_heartbeat():
                logger.warning("VISION HEARTBEAT MISSING. Killing process...")
                proc.kill()
                proc.wait()
                break
        
        exit_code = proc.poll()
        logger.warning("Vision process exited with code %s", exit_code)
        
        restarts += 1
        time.sleep(5) # Cooldown
        
    logger.error("Too many restarts. Watchdog giving up.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
