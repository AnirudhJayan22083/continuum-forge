"""
agents/validation.py

ValidationEngine: the statistical core of CONTINUUM.

Given a Heuristic, tests whether its trigger conditions actually predict
its failure_type across the real historical maintenance/sensor data —
using Pandas/NumPy/SciPy only. No LLM involvement anywhere in this file.

This is deliberately the most heavily tested module in the project: a
heuristic that "sounds true" (like the bearing pattern) must be
statistically demonstrable, not just plausible-sounding, and a heuristic
that sounds true but isn't (like "failures increase every Tuesday")
must be correctly rejected.
"""

import logging
import operator
from datetime import datetime
from typing import Callable, Dict, List, Optional, Union

import numpy as np
from scipy import stats

from database.sqlite import Database
from models.heuristic import Heuristic, HeuristicCondition
from models.maintenance import MaintenanceLog, SensorReading
from models.validation import ValidationResult

logger = logging.getLogger(__name__)

# Conditions referencing these parameters are evaluated against the
# nearest SensorReading on the same machine, within SENSOR_WINDOW_HOURS
# of the incident.
SENSOR_PARAMETERS = {
    "humidity_percent",
    "vibration_mm_s",
    "temperature_celsius",
    "pressure_bar",
}

# Conditions referencing these parameters are evaluated directly against
# the MaintenanceLog's own timestamp — no sensor join needed. This is
# what lets a temporal heuristic (e.g. "failures increase every Tuesday")
# actually get tested, rather than only sensor-based ones.
DERIVED_LOG_ATTRIBUTES: Dict[str, Callable[[MaintenanceLog], float]] = {
    "day_of_week": lambda log: float(log.timestamp.weekday()),  # Monday=0 ... Sunday=6
    "hour": lambda log: float(log.timestamp.hour),
}

OPERATORS: Dict[str, Callable[[float, float], bool]] = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}

DEFAULT_SENSOR_WINDOW_HOURS = 24.0
DEFAULT_P_VALUE_THRESHOLD = 0.05
DEFAULT_MIN_SUPPORT_COUNT = 5


class ValidationInputError(Exception):
    """Raised when a Heuristic references something ValidationEngine
    cannot evaluate at all (e.g. an unknown condition parameter).

    This is distinct from "the condition doesn't hold" or "no nearby
    sensor reading exists" — both of those are normal, expected outcomes
    of validation. This error means the heuristic itself is malformed
    in a way that makes validation impossible, which should surface
    loudly rather than produce a misleading Rejected result.
    """


class ValidationEngine:
    """Statistically validates Heuristics against historical data.

    No LLM involvement. Every number produced here comes from actual
    Pandas/NumPy/SciPy computation over real historical records.
    """

    def __init__(
        self,
        db: Database,
        sensor_window_hours: float = DEFAULT_SENSOR_WINDOW_HOURS,
        p_value_threshold: float = DEFAULT_P_VALUE_THRESHOLD,
        min_support_count: int = DEFAULT_MIN_SUPPORT_COUNT,
    ):
        """Initialize the engine.

        Args:
            db: Connected Database instance to read historical data from.
            sensor_window_hours: Max time gap allowed between a maintenance
                log and the sensor reading used to evaluate sensor-based
                conditions for it.
            p_value_threshold: Chi-square p-value must be below this for
                a heuristic to be Accepted.
            min_support_count: Minimum number of historical occurrences
                where the trigger condition held, required for acceptance
                (guards against accepting a pattern with too little data
                behind it, even if it happens to look significant).
        """
        self.db = db
        self.sensor_window_hours = sensor_window_hours
        self.p_value_threshold = p_value_threshold
        self.min_support_count = min_support_count

    def validate(
        self,
        heuristic: Heuristic,
        validation_id: str,
        validation_timestamp: Union[str, datetime],
    ) -> ValidationResult:
        """Validate a Heuristic against all historical maintenance/sensor data.

        Args:
            heuristic: The Heuristic to validate.
            validation_id: Unique ID to assign to the resulting ValidationResult.
            validation_timestamp: When this validation is being performed.

        Returns:
            A ValidationResult with the full statistical evidence and a
            final Accepted/Rejected decision.

        Raises:
            ValidationInputError: if the heuristic references an unknown
                condition parameter.
            ValueError: if there is no historical data at all to validate against.
        """
        logs = self.db.get_maintenance_logs()
        if not logs:
            raise ValueError("No historical maintenance logs available for validation.")

        readings = self.db.get_sensor_readings()

        condition_flags: List[int] = []
        failure_flags: List[int] = []

        for log in logs:
            condition_met = self.evaluate_conditions(heuristic.conditions, log, readings)
            if condition_met is None:
                # No sensor reading within window for a sensor-based
                # condition on this specific log — we genuinely lack the
                # data to judge this one, so it's excluded rather than
                # guessed at.
                continue
            condition_flags.append(1 if condition_met else 0)
            failure_flags.append(1 if log.failure_type == heuristic.failure_type else 0)

        total_occurrences = len(condition_flags)
        if total_occurrences == 0:
            raise ValueError(
                "No historical logs could be evaluated against this heuristic's "
                "conditions (no matching sensor data within the configured window)."
            )

        a, b, c, d = self._build_contingency_table(condition_flags, failure_flags)
        support_count = a + b
        conditional_probability = (a / support_count) if support_count > 0 else 0.0
        baseline_rate = sum(failure_flags) / total_occurrences

        pearson_correlation = self._safe_pearson_correlation(condition_flags, failure_flags)
        chi_square_statistic, chi_square_p_value = self._safe_chi_square(a, b, c, d)

        confidence_score = self._compute_confidence_score(
            conditional_probability, chi_square_p_value, pearson_correlation
        )

        decision = self._decide(
            chi_square_p_value, support_count, conditional_probability, baseline_rate
        )
        reasoning = self._build_reasoning(
            decision=decision,
            support_count=support_count,
            total_occurrences=total_occurrences,
            conditional_probability=conditional_probability,
            baseline_rate=baseline_rate,
            pearson_correlation=pearson_correlation,
            chi_square_statistic=chi_square_statistic,
            chi_square_p_value=chi_square_p_value,
        )

        result = ValidationResult(
            validation_id=validation_id,
            heuristic_id=heuristic.heuristic_id,
            support_count=support_count,
            total_occurrences=total_occurrences,
            conditional_probability=round(conditional_probability, 4),
            pearson_correlation=round(pearson_correlation, 4),
            chi_square_statistic=round(chi_square_statistic, 4),
            chi_square_p_value=round(min(max(chi_square_p_value, 0.0), 1.0), 6),
            confidence_score=round(confidence_score, 4),
            decision=decision,
            reasoning=reasoning,
            validation_timestamp=validation_timestamp,
        )

        logger.info(
            "Validated heuristic %s: decision=%s (p=%.6f, support=%d/%d)",
            heuristic.heuristic_id, decision, chi_square_p_value, support_count, total_occurrences,
        )
        return result

    # ------------------------------------------------------------------
    # Condition evaluation
    # ------------------------------------------------------------------

    def evaluate_conditions(
        self,
        conditions: List[HeuristicCondition],
        log: MaintenanceLog,
        readings: List[SensorReading],
    ) -> Optional[bool]:
        """Evaluate all of a heuristic's conditions (AND'd together) for one log.

        Returns:
            True if all conditions hold, False if any doesn't, or None if
            a sensor-based condition couldn't be evaluated (no reading
            within the configured window for this log).

        Raises:
            ValidationInputError: if a condition references an unrecognized parameter.
        """
        nearest_reading_cache: Dict[str, Optional[SensorReading]] = {}

        for condition in conditions:
            if condition.parameter in SENSOR_PARAMETERS:
                if condition.parameter not in nearest_reading_cache:
                    nearest_reading_cache[condition.parameter] = self._nearest_reading(
                        log, readings
                    )
                reading = nearest_reading_cache[condition.parameter]
                if reading is None:
                    return None
                value = getattr(reading, condition.parameter)

            elif condition.parameter in DERIVED_LOG_ATTRIBUTES:
                value = DERIVED_LOG_ATTRIBUTES[condition.parameter](log)

            else:
                raise ValidationInputError(
                    f"Unknown condition parameter '{condition.parameter}' — "
                    f"ValidationEngine only knows about sensor parameters "
                    f"{sorted(SENSOR_PARAMETERS)} and derived attributes "
                    f"{sorted(DERIVED_LOG_ATTRIBUTES)}."
                )

            op = OPERATORS[condition.operator]
            if not op(value, condition.value):
                return False

        return True

    def _nearest_reading(
        self, log: MaintenanceLog, readings: List[SensorReading]
    ) -> Optional[SensorReading]:
        """Find the nearest SensorReading on the same machine, within the
        configured time window of a maintenance log."""
        window_seconds = self.sensor_window_hours * 3600
        candidates = [
            r
            for r in readings
            if r.machine_id == log.machine_id
            and abs((r.timestamp - log.timestamp).total_seconds()) <= window_seconds
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda r: abs((r.timestamp - log.timestamp).total_seconds()))

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    @staticmethod
    def _build_contingency_table(
        condition_flags: List[int], failure_flags: List[int]
    ) -> tuple:
        """Build the 2x2 contingency table.

        Returns (a, b, c, d) where:
            a = condition met AND failure occurred
            b = condition met AND failure did NOT occur
            c = condition NOT met AND failure occurred
            d = condition NOT met AND failure did NOT occur
        """
        a = b = c = d = 0
        for condition_met, failure_occurred in zip(condition_flags, failure_flags):
            if condition_met and failure_occurred:
                a += 1
            elif condition_met and not failure_occurred:
                b += 1
            elif not condition_met and failure_occurred:
                c += 1
            else:
                d += 1
        return a, b, c, d

    @staticmethod
    def _safe_pearson_correlation(condition_flags: List[int], failure_flags: List[int]) -> float:
        """Pearson correlation between the two binary flag arrays.

        Returns 0.0 if either array has zero variance (e.g. the condition
        never held, or always held) — correlation is mathematically
        undefined there, and 0.0 (no detectable linear relationship) is
        the honest value to report rather than raising or faking a number.
        """
        if len(set(condition_flags)) < 2 or len(set(failure_flags)) < 2:
            return 0.0
        correlation, _ = stats.pearsonr(condition_flags, failure_flags)
        return float(correlation)

    @staticmethod
    def _safe_chi_square(a: int, b: int, c: int, d: int) -> tuple:
        """Chi-square test on the 2x2 contingency table.

        Returns (statistic, p_value). Falls back to (0.0, 1.0) — i.e. "no
        significant association" — if the table is degenerate (a zero
        row/column makes the chi-square test undefined), rather than
        raising and aborting the whole validation.
        """
        table = np.array([[a, b], [c, d]])
        if (table.sum(axis=0) == 0).any() or (table.sum(axis=1) == 0).any():
            return 0.0, 1.0
        try:
            chi2, p_value, _, _ = stats.chi2_contingency(table)
            return float(chi2), float(p_value)
        except ValueError:
            return 0.0, 1.0

    @staticmethod
    def _compute_confidence_score(
        conditional_probability: float, p_value: float, pearson_correlation: float
    ) -> float:
        """Composite confidence score in [0, 1].

        Weighted blend of:
          - conditional_probability (50%): how often the condition, when
            true, actually coincided with the predicted failure
          - statistical significance (30%): 1 - p_value
          - strength of correlation (20%): |Pearson r|

        This is a transparent, fixed formula — not learned or tuned per
        heuristic — so the same inputs always produce the same score.
        """
        significance_term = 1.0 - min(max(p_value, 0.0), 1.0)
        correlation_term = min(abs(pearson_correlation), 1.0)
        score = (
            0.5 * conditional_probability
            + 0.3 * significance_term
            + 0.2 * correlation_term
        )
        return min(max(score, 0.0), 1.0)

    def _decide(
        self,
        chi_square_p_value: float,
        support_count: int,
        conditional_probability: float,
        baseline_rate: float,
    ) -> str:
        """Final Accepted/Rejected decision.

        Accepted requires ALL of:
          - statistically significant (p < p_value_threshold)
          - enough historical support (support_count >= min_support_count)
          - the condition actually raises the odds of failure above the
            dataset's baseline rate (not just correlated by coincidence
            with a rare event)
        """
        is_significant = chi_square_p_value < self.p_value_threshold
        has_enough_support = support_count >= self.min_support_count
        beats_baseline = conditional_probability > baseline_rate

        if is_significant and has_enough_support and beats_baseline:
            return "Accepted"
        return "Rejected"

    @staticmethod
    def _build_reasoning(
        decision: str,
        support_count: int,
        total_occurrences: int,
        conditional_probability: float,
        baseline_rate: float,
        pearson_correlation: float,
        chi_square_statistic: float,
        chi_square_p_value: float,
    ) -> str:
        """Human-readable explanation of the decision, grounded in the actual numbers."""
        if decision == "Accepted":
            return (
                f"Accepted: the trigger condition held in {support_count} of "
                f"{total_occurrences} historical events, and when it held, the "
                f"predicted failure occurred {conditional_probability*100:.1f}% of the "
                f"time (vs. a baseline rate of {baseline_rate*100:.1f}% across all "
                f"events). This association is statistically significant "
                f"(chi-square={chi_square_statistic:.2f}, p={chi_square_p_value:.6f}), "
                f"with a Pearson correlation of {pearson_correlation:.3f}."
            )
        return (
            f"Rejected: the trigger condition held in {support_count} of "
            f"{total_occurrences} historical events, with a conditional probability "
            f"of {conditional_probability*100:.1f}% (baseline rate: "
            f"{baseline_rate*100:.1f}%). This does not meet the bar for statistical "
            f"significance and/or sufficient support "
            f"(chi-square={chi_square_statistic:.2f}, p={chi_square_p_value:.6f}, "
            f"Pearson correlation={pearson_correlation:.3f}) — the pattern is not "
            f"reliably distinguishable from chance in the historical data."
        )