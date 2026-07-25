"""Interview queue generator for CONTINUUM.

Builds the ordered queue of technicians to interview, ordered by
years_experience (descending) then retirement_date (ascending) — the
most experienced, soonest-to-retire technicians get interviewed first.
No ranking algorithm beyond this ordering is required.
"""

import json
import logging
from pathlib import Path
from typing import List

from models.employee import Employee

logger = logging.getLogger(__name__)


class InterviewQueueGenerator:
    """Builds and persists the interview queue from a list of Employees."""

    def __init__(self, config_dir: str = "config"):
        """Initialize generator.

        Args:
            config_dir: Directory to store the interview queue JSON file.
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def build_queue(self, employees: List[Employee]) -> List[dict]:
        """Order employees into an interview queue.

        Ordering: years_experience descending, then retirement_date
        ascending (ties broken by whoever retires sooner).

        Args:
            employees: Employees to order into a queue.

        Returns:
            List of queue entry dicts, each with queue_position starting at 1.
        """
        ordered = sorted(
            employees,
            key=lambda e: (-e.years_experience, e.retirement_date),
        )

        queue = []
        for position, employee in enumerate(ordered, start=1):
            queue.append(
                {
                    "queue_position": position,
                    "employee_id": employee.employee_id,
                    "name": employee.name,
                    "years_experience": employee.years_experience,
                    "retirement_date": employee.retirement_date.date().isoformat(),
                    "status": "completed" if employee.interview_completed else "pending",
                }
            )
        return queue

    def save_queue(self, queue: List[dict], filename: str = "interview_queue.json") -> Path:
        """Save the interview queue to disk as JSON.

        Args:
            queue: Queue entries produced by build_queue().
            filename: Filename within config_dir to write to.

        Returns:
            Path the queue was written to.
        """
        json_path = self.config_dir / filename
        with open(json_path, "w") as f:
            json.dump(queue, f, indent=2)
        logger.info(f"Saved interview queue to {json_path}")
        return json_path

    def generate(
        self, employees: List[Employee], filename: str = "interview_queue.json"
    ) -> List[dict]:
        """Build and persist the interview queue in one call.

        Args:
            employees: Employees to order into a queue.
            filename: Filename within config_dir to write to.

        Returns:
            The queue entries that were written to disk.
        """
        queue = self.build_queue(employees)
        self.save_queue(queue, filename)
        return queue