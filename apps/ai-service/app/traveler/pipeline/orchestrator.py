# app/traveler/pipeline/orchestrator.py
from typing import Any
from app.traveler.interfaces.contracts import (
    IPipelineOrchestrator,
    ITimelineEngine,
    IAlertEngine,
    IReminderEngine,
    IActionEngine,
    IRecoveryEngine,
    IExplanationEngine,
    IConfidenceEngine,
)


class TravelerPipelineOrchestrator(IPipelineOrchestrator):
    def __init__(
        self,
        timeline_engine: ITimelineEngine,
        alert_engine: IAlertEngine,
        reminder_engine: IReminderEngine,
        action_engine: IActionEngine,
        recovery_engine: IRecoveryEngine,
        explanation_engine: IExplanationEngine,
        confidence_engine: IConfidenceEngine,
    ):
        self.timeline_engine = timeline_engine
        self.alert_engine = alert_engine
        self.reminder_engine = reminder_engine
        self.action_engine = action_engine
        self.recovery_engine = recovery_engine
        self.explanation_engine = explanation_engine
        self.confidence_engine = confidence_engine

    async def execute_pipeline(self, context: Any) -> Any:
        # 1. Timeline Engine
        timeline_dto = self.timeline_engine.evaluate_timeline(context)
        context = context.copy_with(timeline_version=timeline_dto.version)

        # 2. Alert Engine
        alerts = self.alert_engine.evaluate_alerts(context)
        context = context.copy_with(alerts=alerts)

        # 3. Reminder Engine
        reminders = self.reminder_engine.process_reminders(context)
        context = context.copy_with(reminders=reminders)

        # 4. Action Selection
        action_selected = self.action_engine.select_action(context)
        context = context.copy_with(recommended_action=action_selected)

        # 5. Recovery Engine (Only if missed connection detected)
        if context.status == "MISSED_CONNECTION":
            recovery_dto = await self.recovery_engine.build_recovery_plan(None, context)
            context = context.copy_with(recovery_plan=recovery_dto)

        # 6. Explanation Engine
        explanation_details = self.explanation_engine.generate_explanation(context)
        context = context.copy_with(explanation=explanation_details)

        # 7. Confidence Engine
        confidence_val = self.confidence_engine.calculate_confidence(context)
        context = context.copy_with(confidence_score=confidence_val)

        return context
