import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("ai-service.orchestrator.metrics")

class MetricsCollector:
    """
    Abstracted collector for application metrics.
    Accumulates metrics in memory; ready to connect to Prometheus/OTel in the future.
    """
    _instance: Optional["MetricsCollector"] = None

    def __new__(cls) -> "MetricsCollector":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.reset()
        return cls._instance

    def reset(self) -> None:
        self.request_count: int = 0
        self.failure_count: int = 0
        self.agent_executions: Dict[str, int] = {}
        self.node_latencies_ms: Dict[str, float] = {}
        self.node_executions: Dict[str, int] = {}
        self.request_latencies_ms: float = 0.0

    def increment_request(self) -> None:
        self.request_count += 1
        logger.debug("Metrics: increment_request")

    def increment_failure(self) -> None:
        self.failure_count += 1
        logger.debug("Metrics: increment_failure")

    def record_agent_execution(self, agent_name: str) -> None:
        self.agent_executions[agent_name] = self.agent_executions.get(agent_name, 0) + 1
        logger.debug(f"Metrics: record_agent_execution agent='{agent_name}'")

    def record_node_latency(self, node_name: str, latency_ms: float) -> None:
        current_sum = self.node_latencies_ms.get(node_name, 0.0)
        current_count = self.node_executions.get(node_name, 0)
        
        self.node_latencies_ms[node_name] = current_sum + latency_ms
        self.node_executions[node_name] = current_count + 1
        logger.debug(f"Metrics: record_node_latency node='{node_name}' latency={latency_ms:.2f}ms")

    def record_request_latency(self, latency_ms: float) -> None:
        self.request_latencies_ms += latency_ms
        logger.debug(f"Metrics: record_request_latency latency={latency_ms:.2f}ms")

    def get_summary(self) -> Dict[str, Any]:
        """Returns summarized metrics dashboard data."""
        avg_node_latencies = {}
        for node, total_time in self.node_latencies_ms.items():
            count = self.node_executions.get(node, 1)
            avg_node_latencies[node] = round(total_time / count, 2)

        return {
            "total_requests": self.request_count,
            "total_failures": self.failure_count,
            "agent_executions": self.agent_executions,
            "average_node_latencies_ms": avg_node_latencies,
            "accumulated_request_latency_ms": round(self.request_latencies_ms, 2)
        }

metrics_collector = MetricsCollector()
