from typing import Dict, Any, List

class RuleEngine:
    def evaluate(self, bucket: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Transformar métricas de bucket em alertas.
        No v1, mantenha 1–2 regras simples.
        """
        events = []
        m = bucket["metrics"]

        # Exemplo: fila longa baseado em people_count_max
        people_max = m.get("people_count_max")
        if people_max is not None and people_max >= 6:
            events.append({
                "event_type": "queue_long",
                "severity": "warning",
                "title": "Possível fila longa",
                "description": f"Pico de pessoas detectadas: {people_max}",
                "metadata": {"ts_bucket": bucket["ts_bucket"], "people_max": people_max},
            })
        return events
