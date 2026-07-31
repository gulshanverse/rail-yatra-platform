"""
Phase 10 Production Platform Test Suite.
"""

from fastapi.testclient import TestClient

from app.main import app
from app.production.version import get_version_info
from app.production.config import production_config
from app.production.secrets import secrets_manager
from app.production.health import health_checker
from app.production.readiness import readiness_probe
from app.production.liveness import liveness_probe
from app.production.metrics import metrics_collector
from app.production.diagnostics import diagnostics_engine
from app.production.startup import startup_validator
from app.production.shutdown import shutdown_manager
from app.production.security import security_manager
from app.production.logging_config import logging_platform
from app.production.tracing import tracing_platform
from app.production.backup import backup_manager
from app.production.restore import restore_manager
from app.production.recovery import recovery_manager
from app.production.maintenance import maintenance_scheduler

client = TestClient(app)


class TestProductionPlatform:
    def test_version_info(self):
        info = get_version_info()
        assert info["application"] == "RailYatra AI Platform"
        assert info["version"] == "10.0.0"

    def test_production_config(self):
        assert production_config.get("app_name") == "RailYatra AI Platform"
        assert production_config.feature_flags.is_enabled("enable_ai_predictions") is True
        summary = production_config.to_dict()
        assert "environment" in summary

    def test_secrets_manager(self):
        val = secrets_manager.validate(is_production=False)
        assert "loaded_count" in val
        sum_dict = secrets_manager.summary()
        assert isinstance(sum_dict, dict)

    def test_health_checks(self):
        h = health_checker.check_all()
        assert h["status"] in ("HEALTHY", "DEGRADED")
        assert "dependencies" in h

    def test_readiness_and_liveness(self):
        r = readiness_probe.check()
        assert r["ready"] is True
        live_check = liveness_probe.check()
        assert live_check["alive"] is True

    def test_metrics_collector(self):
        metrics_collector.increment("http_requests_total")
        metrics_collector.set_gauge("active_connections", 5)
        metrics_collector.observe("http_request_duration_ms", 12.5)
        m = metrics_collector.get_metrics()
        assert m["counters"]["http_requests_total"] >= 1
        prom = metrics_collector.prometheus_text()
        assert "http_requests_total" in prom

    def test_diagnostics_engine(self):
        diag = diagnostics_engine.collect()
        assert "version" in diag
        assert "runtime" in diag

    def test_startup_validator(self):
        res = startup_validator.validate()
        assert res["status"] == "PASSED"

    def test_shutdown_manager(self):
        executed = []
        shutdown_manager.register("test_handler", lambda: executed.append(True), priority=100)
        res = shutdown_manager.execute()
        assert res["shutdown_complete"] is True
        assert True in executed

    def test_security_manager(self):
        headers = security_manager.get_security_headers()
        assert "Content-Security-Policy" in headers
        assert security_manager.rate_limiter.is_allowed("test_client") is True
        val = security_manager.validate_configuration()
        assert val["headers_configured"] >= 8

    def test_logging_platform(self):
        logging_platform.configure("INFO")
        status = logging_platform.get_status()
        assert status["configured"] is True

    def test_tracing_platform(self):
        span = tracing_platform.start_trace("test_operation")
        span.set_attribute("key", "val")
        tracing_platform.finish_span(span)
        trace = tracing_platform.get_trace(span.trace_id)
        assert len(trace) == 1
        assert trace[0]["operation"] == "test_operation"

    def test_backup_and_restore(self):
        bkp = backup_manager.backup_database()
        assert bkp.status == "COMPLETED"
        verify_b = backup_manager.verify_backup(bkp.backup_id)
        assert verify_b["verified"] is True

        rst = restore_manager.execute_restore(bkp.backup_id, "postgresql")
        assert rst.status == "COMPLETED"
        verify_r = restore_manager.verify_restore(rst.restore_id)
        assert verify_r["verified"] is True

    def test_disaster_recovery(self):
        procs = recovery_manager.list_procedures()
        assert len(procs) >= 3
        tested = recovery_manager.execute_recovery_test("DR_001")
        assert tested["status"] == "TESTED"

    def test_maintenance_scheduler(self):
        tasks = maintenance_scheduler.list_tasks()
        assert len(tasks) >= 4
        res = maintenance_scheduler.execute_task("MAINT_001")
        assert res["status"] == "SUCCESS"


class TestProductionAPIRoutes:
    def test_get_health(self):
        res = client.get("/health")
        assert res.status_code == 200
        assert "status" in res.json()

    def test_get_readiness(self):
        res = client.get("/health/ready")
        assert res.status_code == 200
        assert res.json()["ready"] is True

    def test_get_liveness(self):
        res = client.get("/health/live")
        assert res.status_code == 200
        assert res.json()["alive"] is True

    def test_get_metrics(self):
        res = client.get("/metrics?format=json")
        assert res.status_code == 200
        assert "counters" in res.json()

    def test_get_metrics_prometheus(self):
        res = client.get("/metrics")
        assert res.status_code == 200
        assert "http_requests_total" in res.text
        assert "memory_health_status" in res.text

    def test_get_version(self):
        res = client.get("/version")
        assert res.status_code == 200
        assert res.json()["version"] == "10.0.0"

    def test_get_diagnostics(self):
        res = client.get("/diagnostics")
        assert res.status_code == 200
        assert "runtime" in res.json()

    def test_get_production_config(self):
        res = client.get("/production/config")
        assert res.status_code == 200
        assert res.json()["app_name"] == "RailYatra AI Platform"

    def test_get_security_status(self):
        res = client.get("/production/security")
        assert res.status_code == 200
        assert res.json()["rate_limiting_enabled"] is True

    def test_trigger_backup_and_list(self):
        res_post = client.post("/production/backup?backup_type=DATABASE")
        assert res_post.status_code == 200
        assert res_post.json()["status"] == "COMPLETED"

        res_list = client.get("/production/backups")
        assert res_list.status_code == 200
        assert len(res_list.json()) >= 1

    def test_trigger_restore(self):
        res = client.post("/production/restore?backup_id=BKP_000001&target=postgresql")
        assert res.status_code == 200
        assert res.json()["status"] == "COMPLETED"

    def test_get_recovery_status(self):
        res = client.get("/production/recovery")
        assert res.status_code == 200
        assert "total_procedures" in res.json()

    def test_get_maintenance_status(self):
        res = client.get("/production/maintenance")
        assert res.status_code == 200
        assert res.json()["total_tasks"] >= 4
