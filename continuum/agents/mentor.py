"""
agents/mentor.py

MentorAgent: given a current sensor reading, searches the stored,
statistically-validated OperationalRules and returns ranked
recommendations — this is what a technician (especially a newer one)
actually queries in production.

Reuses the same SENSOR_PARAMETERS/OPERATORS constants ValidationEngine
uses, so a rule that was validated against a certain condition
definition is checked against live readings using that exact same
definition — no drift between "what we proved" and "what we alert on".
"""

import logging
from dataclasses import dataclass, field
from typing import Callable, Dict, List

from agents.validation import OPERATORS, SENSOR_PARAMETERS
from database.sqlite import Database
from models.maintenance import SensorReading
from models.operational_rule import OperationalRule

logger = logging.getLogger(__name__)

MAX_SUPPORTING_INCIDENTS = 3

# Same derived-attribute idea as ValidationEngine's DERIVED_LOG_ATTRIBUTES,
# but generalized to anything with a .timestamp (SensorReading here,
# MaintenanceLog in validation.py) since a live reading also has a
# timestamp a temporal condition could reference.
DERIVED_ATTRIBUTES: Dict[str, Callable[[SensorReading], float]] = {
    "day_of_week": lambda reading: float(reading.timestamp.weekday()),
    "hour": lambda reading: float(reading.timestamp.hour),
}


class MentorInputError(Exception):
    """Raised when a stored rule references a condition parameter the
    MentorAgent doesn't recognize. This would indicate a bug upstream
    (e.g. an unvalidated rule slipping into the database) rather than a
    normal "no match" outcome, so it's surfaced distinctly."""


@dataclass
class MentorRecommendation:
    """A single ranked recommendation for a live sensor reading."""

    rule_id: str
    machine_id: str
    failure_type: str
    trigger: str
    recommended_action: str
    confidence: float
    supporting_incidents: List[str] = field(default_factory=list)
    explanation: str = ""


class MentorAgent:
    """Matches live sensor readings against validated operational rules."""

    def __init__(self, db: Database):
        """Initialize the agent.

        Args:
            db: Connected Database instance to read operational rules
                and historical maintenance logs from.
        """
        self.db = db

    def get_recommendations(
        self, machine_id: str, current_reading: SensorReading
    ) -> List[MentorRecommendation]:
        """Get all matching recommendations for a live sensor reading,
        ranked by confidence (highest first).

        Args:
            machine_id: The machine the reading came from. Rules are
                looked up for this machine specifically.
            current_reading: The live sensor reading to evaluate rules against.

        Returns:
            A list of MentorRecommendation, ranked by confidence
            descending. Empty if no stored rule's conditions match the
            current reading.

        Raises:
            MentorInputError: if a stored rule references a condition
                parameter that can't be evaluated against a SensorReading.
        """
        rules = self.db.get_operational_rules(machine_id)
        matches = []

        for rule in rules:
            if self._conditions_match(rule, current_reading):
                matches.append(rule)

        recommendations = [self._build_recommendation(rule) for rule in matches]
        recommendations.sort(key=lambda r: r.confidence, reverse=True)

        logger.info(
            "Mentor lookup for %s: %d/%d rules matched current reading",
            machine_id, len(matches), len(rules),
        )
        return recommendations

    def get_best_recommendation(
        self, machine_id: str, current_reading: SensorReading
    ) -> "MentorRecommendation | None":
        """Convenience wrapper: return only the single highest-confidence
        recommendation, or None if nothing matched."""
        recommendations = self.get_recommendations(machine_id, current_reading)
        return recommendations[0] if recommendations else None

    # ------------------------------------------------------------------
    # Condition matching
    # ------------------------------------------------------------------

    def _conditions_match(self, rule: OperationalRule, reading: SensorReading) -> bool:
        """Check whether ALL of a rule's conditions hold against a live reading.

        Raises:
            MentorInputError: for an unrecognized condition parameter.
        """
        for condition in rule.conditions:
            if condition.parameter in SENSOR_PARAMETERS:
                value = getattr(reading, condition.parameter)
            elif condition.parameter in DERIVED_ATTRIBUTES:
                value = DERIVED_ATTRIBUTES[condition.parameter](reading)
            else:
                raise MentorInputError(
                    f"Rule {rule.rule_id} references unknown condition parameter "
                    f"'{condition.parameter}' — cannot evaluate against a live reading."
                )

            op = OPERATORS[condition.operator]
            if not op(value, condition.value):
                return False
        return True

    # ------------------------------------------------------------------
    # Recommendation construction
    # ------------------------------------------------------------------

    def _build_recommendation(self, rule: OperationalRule) -> MentorRecommendation:
        """Build a full MentorRecommendation for a matched rule, including
        a few concrete supporting historical incidents and an explanation."""
        historical_logs = self.db.get_maintenance_logs(rule.machine_id)
        supporting = [
            log.log_id
            for log in historical_logs
            if log.failure_type == rule.failure_type
        ][:MAX_SUPPORTING_INCIDENTS]

        explanation = (
            f"Current readings on {rule.machine_id} match a validated pattern: "
            f"\"{rule.trigger}\". This pattern predicts {rule.failure_type} with "
            f"{rule.confidence_score*100:.1f}% confidence, based on "
            f"{len(supporting)} historical incident(s) "
            f"({', '.join(supporting) if supporting else 'see validation record'}). "
            f"Recommended action: {rule.recommended_action}"
        )

        return MentorRecommendation(
            rule_id=rule.rule_id,
            machine_id=rule.machine_id,
            failure_type=rule.failure_type,
            trigger=rule.trigger,
            recommended_action=rule.recommended_action,
            confidence=rule.confidence_score,
            supporting_incidents=supporting,
            explanation=explanation,
        )