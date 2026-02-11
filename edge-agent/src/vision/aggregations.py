from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import math


@dataclass
class _Bucket:
    ts_bucket: int  # epoch start do bucket (segundos)
    count: int = 0
    sums: Dict[str, float] = field(default_factory=dict)
    maxs: Dict[str, float] = field(default_factory=dict)


class MetricAggregator:
    """
    Agregador simples por camera_id.
    - Buckets fixos de bucket_seconds (ex.: 60s)
    - Produz métricas *_avg e *_max por bucket
    """

    def __init__(self, bucket_seconds: int = 60):
        self.bucket_seconds = int(bucket_seconds)
        self._buckets: Dict[str, _Bucket] = {}

    def _bucket_start(self, ts: float) -> int:
        # início do bucket em epoch-segundos (ex.: minuto)
        return int(math.floor(ts / self.bucket_seconds) * self.bucket_seconds)

    def add_sample(self, camera_id: str, ts: float, metrics: Dict[str, Any]) -> None:
        """
        Adiciona uma amostra instantânea no bucket corrente da câmera.
        """
        bstart = self._bucket_start(ts)
        b = self._buckets.get(camera_id)

        if b is None or b.ts_bucket != bstart:
            # inicia novo bucket (não fecha o anterior aqui)
            self._buckets[camera_id] = _Bucket(ts_bucket=bstart)
            b = self._buckets[camera_id]

        b.count += 1

        # agrega apenas números
        for k, v in (metrics or {}).items():
            if isinstance(v, bool):
                v = int(v)
            if isinstance(v, (int, float)):
                fv = float(v)
                b.sums[k] = b.sums.get(k, 0.0) + fv
                b.maxs[k] = fv if k not in b.maxs else max(b.maxs[k], fv)

    def try_close_bucket(self, camera_id: str, ts: float) -> Optional[Dict[str, Any]]:
        """
        Fecha e retorna o bucket anterior quando o tempo já avançou para o próximo bucket.
        Retorna None se ainda estamos no mesmo bucket.
        """
        b = self._buckets.get(camera_id)
        if b is None:
            return None

        current_start = self._bucket_start(ts)
        if current_start == b.ts_bucket:
            return None  # ainda no mesmo bucket

        # fecha o bucket b e já cria o novo bucket para o current_start
        closed = b
        self._buckets[camera_id] = _Bucket(ts_bucket=current_start)

        out_metrics: Dict[str, Any] = {}

        denom = max(1, closed.count)
        for k, s in closed.sums.items():
            out_metrics[f"{k}_avg"] = s / denom
        for k, m in closed.maxs.items():
            out_metrics[f"{k}_max"] = m

        return {
            "ts_bucket": closed.ts_bucket,
            "count": closed.count,
            "metrics": out_metrics,
        }
