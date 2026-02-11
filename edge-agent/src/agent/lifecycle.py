from __future__ import annotations

import time
import threading
import queue as mem_queue
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..events.builder import build_envelope
from ..events.receipts import compute_receipt_id
from ..queue.sqlite_queue import SqliteQueue
from ..transport.api_client import ApiClient
from .runtime_state import RUNTIME_STATE


@dataclass
class _CameraHeartbeatStub:
    camera_id: str
    name: str
    rtsp_url: str = ""
    last_error: Optional[str] = None

    def is_ok(self) -> bool:
        # Heartbeat-only: não valida RTSP/frames.
        return True


def _make_heartbeat_envelope(
    *,
    settings,
    camera_id: Optional[str] = None,
    external_id: Optional[str] = None,
    name: Optional[str] = None,
    rtsp_url: Optional[str] = None,
    status: str = "online",
    error: Optional[str] = None,
) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "store_id": settings.store_id,
        "camera_id": camera_id,
        "external_id": external_id or camera_id,
        "name": name,
        "rtsp_url": rtsp_url,
        "status": status,
        "error": error,
        "agent_id": settings.agent_id,
        "ts": datetime.now(timezone.utc).isoformat(),
    }

    envelope = build_envelope(
        event_name="edge_camera_heartbeat" if camera_id else "edge_heartbeat",
        source=f"edge-agent:{settings.agent_id}",
        data=data,
        meta={},
        event_version=1,
        lead_id=None,
        org_id=None,
    )
    receipt_id = compute_receipt_id(envelope)
    envelope["receipt_id"] = receipt_id
    data["receipt_id"] = receipt_id
    return envelope


def _heartbeat_loop(
    *,
    settings,
    pending_queue: mem_queue.Queue,
    cameras: List[Any],
    stop_event: threading.Event,
) -> None:
    interval = max(5, int(getattr(settings, "heartbeat_interval_seconds", 30) or 30))

    while not stop_event.is_set():
        try:
            # store heartbeat
            pending_queue.put(_make_heartbeat_envelope(settings=settings))

            # camera heartbeats
            for cam in cameras:
                cam_ok = True
                cam_err = None

                if hasattr(cam, "is_ok") and callable(getattr(cam, "is_ok")):
                    try:
                        cam_ok = bool(cam.is_ok())
                    except Exception as e:
                        cam_ok = False
                        cam_err = str(e)

                if not cam_ok:
                    cam_err = cam_err or getattr(cam, "last_error", None)

                pending_queue.put(
                    _make_heartbeat_envelope(
                        settings=settings,
                        camera_id=getattr(cam, "camera_id", None),
                        external_id=getattr(cam, "camera_id", None),
                        name=getattr(cam, "name", None),
                        rtsp_url=getattr(cam, "rtsp_url", None),
                        status="online" if cam_ok else "error",
                        error=cam_err,
                    )
                )
        except Exception as e:
            # Não deixa o loop morrer
            print(f"[heartbeat] error: {e}")

        stop_event.wait(interval)


def _log_error_throttled(state: Dict[str, Any], message: str) -> None:
    now = time.time()
    last_at = float(state.get("last_log_at") or 0.0)
    last_msg = state.get("last_log_msg")
    if (now - last_at) >= 10.0 or message != last_msg:
        print(message)
        state["last_log_at"] = now
        state["last_log_msg"] = message


def _send_event(
    *,
    client: ApiClient,
    envelope: Dict[str, Any],
    enqueue_on_fail: Optional[callable],
) -> tuple[bool, Optional[int], Optional[str]]:
    res = client.post_event(envelope)
    ok = bool(res.get("ok"))
    status = res.get("status")
    error = res.get("error")
    if ok:
        RUNTIME_STATE.record_flush(
            ok=True,
            status=status,
            error=None,
            sent_ok=1,
            sent_fail=0,
            backend_ok=True,
        )
        return True, status, None

    RUNTIME_STATE.record_flush(
        ok=False,
        status=status,
        error=error,
        sent_ok=0,
        sent_fail=1,
        backend_ok=False,
    )
    if enqueue_on_fail is not None:
        enqueue_on_fail()
    return False, status, error


def _flush_queue(
    *,
    queue: SqliteQueue,
    client: ApiClient,
    log_state: Dict[str, Any],
) -> None:
    batch = queue.dequeue_batch(limit=50)
    if not batch:
        return

    for row_id, payload in batch:
        ok, status, error = _send_event(
            client=client,
            envelope=payload,
            enqueue_on_fail=None,
        )
        if ok:
            queue.ack(row_id)
            continue

        msg = f"🌐 flush failed status={status} err={error}"
        _log_error_throttled(log_state, msg)
        break


def run_agent(settings, heartbeat_only: bool = False) -> None:
    """
    heartbeat_only=True:
      - NÃO importa módulos de visão (numpy/cv2/yolo)
      - NÃO inicia workers RTSP/frames
      - envia heartbeats por store + por câmera configurada (sem validação RTSP)
    """

    if heartbeat_only:
        settings.vision_enabled = False
        print("ℹ️ heartbeat-only mode enabled (vision disabled)")

    queue = SqliteQueue(settings.queue_path)
    client = ApiClient(
        base_url=settings.cloud_base_url,
        token=settings.cloud_token,
        timeout=settings.cloud_timeout,
    )

    pending_queue: mem_queue.Queue = mem_queue.Queue()
    send_interval = float(getattr(settings, "send_interval_seconds", 5) or 5)
    log_state: Dict[str, Any] = {"last_log_at": 0.0, "last_log_msg": None}

    RUNTIME_STATE.set_running(True, heartbeat_only=heartbeat_only)

    # cameras list:
    cameras: List[Any] = []
    detector = None
    aggregator = None
    rules = None

    if not heartbeat_only and settings.vision_enabled:
        from ..camera.rtsp import RtspCameraWorker
        from ..vision.aggregations import MetricAggregator
        from ..vision.rules import RuleEngine
        from ..vision.detector import PersonDetector

        detector = PersonDetector(
            weights_path=settings.yolo_weights_path,
            conf=settings.conf,
            iou=settings.iou,
            device=settings.device,
        )
        aggregator = MetricAggregator(bucket_seconds=60)
        rules = RuleEngine()

        for cam in settings.cameras:
            worker = RtspCameraWorker(
                camera_id=cam.camera_id,
                name=cam.name,
                rtsp_url=cam.rtsp_url,
                roi_config_path=cam.roi_config,
                target_width=settings.target_width,
                fps_limit=settings.fps_limit,
                frame_skip=settings.frame_skip,
            )
            worker.start()
            cameras.append(worker)
    else:
        # Stubs: só pra emitir heartbeats por câmera (sem RTSP)
        for cam in settings.cameras:
            cameras.append(
                _CameraHeartbeatStub(
                    camera_id=cam.camera_id,
                    name=cam.name,
                    rtsp_url=cam.rtsp_url,
                )
            )

    stop_event = threading.Event()

    def _sender_loop() -> None:
        last_flush = 0.0
        while not stop_event.is_set():
            try:
                try:
                    envelope = pending_queue.get(timeout=1.0)
                    ok, status, error = _send_event(
                        client=client,
                        envelope=envelope,
                        enqueue_on_fail=lambda: queue.enqueue(envelope),
                    )
                    if not ok:
                        msg = f"🌐 send failed status={status} err={error}"
                        _log_error_throttled(log_state, msg)
                except mem_queue.Empty:
                    pass

                now = time.time()
                if (now - last_flush) >= send_interval:
                    _flush_queue(queue=queue, client=client, log_state=log_state)
                    last_flush = now
            except Exception as e:
                _log_error_throttled(log_state, f"🌐 sender error: {e}")
                stop_event.wait(1.0)

    sender_thread = threading.Thread(target=_sender_loop, daemon=True)
    sender_thread.start()

    hb_thread = threading.Thread(
        target=_heartbeat_loop,
        kwargs=dict(settings=settings, pending_queue=pending_queue, cameras=cameras, stop_event=stop_event),
        daemon=True,
    )
    hb_thread.start()

    try:
        while True:
            if detector is not None:
                for w in cameras:
                    f = w.try_get_frame()
                    if f is None:
                        continue

                    dets = detector.detect(f.image)
                    metrics = w.update_metrics(dets, f.ts)

                    aggregator.add_sample(
                        camera_id=w.camera_id,
                        ts=f.ts,
                        metrics=metrics,
                    )

                    bucket = aggregator.try_close_bucket(camera_id=w.camera_id, ts=f.ts)
                    if bucket is not None:
                        data = {
                            "store_id": settings.store_id,
                            "camera_id": w.camera_id,
                            "ts_bucket": bucket["ts_bucket"],
                            "metrics": bucket["metrics"],
                        }
                        env = build_envelope(
                            event_name="edge_metric_bucket",
                            source="edge",
                            data=data,
                            meta={"agent_id": settings.agent_id},
                        )
                        env["receipt_id"] = compute_receipt_id(env)
                        pending_queue.put(env)

                        alerts = rules.evaluate(camera_id=w.camera_id, bucket=bucket)
                        for a in alerts:
                            a_data = {
                                "store_id": settings.store_id,
                                "camera_id": w.camera_id,
                                **a,
                            }
                            a_env = build_envelope(
                                event_name="alert",
                                source="edge",
                                data=a_data,
                                meta={"agent_id": settings.agent_id},
                            )
                            a_env["receipt_id"] = compute_receipt_id(a_env)
                            pending_queue.put(a_env)

            time.sleep(0.01 if detector is not None else 0.2)
    except KeyboardInterrupt:
        print("🛑 shutdown requested (KeyboardInterrupt)")
    finally:
        RUNTIME_STATE.set_running(False)
        stop_event.set()
        for cam in cameras:
            if hasattr(cam, "stop") and callable(getattr(cam, "stop")):
                try:
                    cam.stop()
                except Exception:
                    pass
        for cam in cameras:
            if hasattr(cam, "join") and callable(getattr(cam, "join")):
                try:
                    cam.join(timeout=2.0)
                except Exception:
                    pass
