# app/traveler/alerts/reminder_engine.py
import time
from typing import Any, List
from app.traveler.interfaces.contracts import IReminderEngine
from app.traveler.dto.models import TravelerReminderDTO


class ReminderEngine(IReminderEngine):
    def process_reminders(self, context: Any) -> List[TravelerReminderDTO]:
        reminders = []
        now = time.time()

        # Schedules dynamic alerts
        # Remind traveler to leave home 2 hours prior to scheduled departure
        departure_time = context.telemetry.get("scheduled_departure", now + 7200.0)
        leave_home_time = departure_time - 7200.0

        if now < leave_home_time:
            reminders.append(
                TravelerReminderDTO(
                    reminder_id="rem_leave_home",
                    fire_time=leave_home_time,
                    title="Departure Reminder",
                    body="Time to leave for the station to beat the city traffic.",
                )
            )

        return reminders
