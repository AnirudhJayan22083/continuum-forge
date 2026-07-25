"""
agents/explainability.py

ExplainabilityEngine: turns a ValidationResult into something a human
can actually read and trust — a natural-language explanation grounded
in specific historical incidents, plus charts saved to disk.

No new statistics are computed here beyond what ValidationEngine already
produced; this module explains those numbers, using the exact same
condition-evaluation logic (via ValidationEngine.evaluate_conditions) so
the charts can never contradict the validation decision they're
explaining.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import matplotlib
matplotlib.use("Agg")  # headless — no display available in this environment
import matplotlib.pyplot as plt

from agents.validation import ValidationEngine
from database.sqlite import Database
from models.heuristic import Heuristic
from models.validation import ValidationResult

logger = logging.getLogger(__name__)

DEFAULT_CHARTS_DIR = "data/charts"
MAX_SUPPORTING_INCIDENTS = 5


@dataclass
class SupportingIncident:
    """A single historical incident cited as evidence for/against a heuristic."""

    log_id: str
    machine_id: str
    timestamp: str
    failure_type: str
    condition_held: bool
    description: str


@dataclass
class Explanation:
    """Full explainability output for one validated heuristic."""

    heuristic_id: str
    decision: str
    narrative: str
    supporting_incidents: List[SupportingIncident] = field(default_factory=list)
    timeline_chart_path: str = ""
    probability_chart_path: str = ""


class ExplainabilityEngine:
    """Produces natural-language explanations and charts for validated heuristics."""

    def __init__(
        self,
        db: Database,
        validation_engine: ValidationEngine,
        charts_dir: str = DEFAULT_CHARTS_DIR,
    ):
        """Initialize the engine.

        Args:
            db: Connected Database instance to read historical data from.
            validation_engine: The same ValidationEngine used to produce
                the ValidationResult being explained — reused here so the
                charts use identical condition-evaluation logic, never a
                second, potentially-drifting implementation of it.
            charts_dir: Directory to save generated chart PNGs to.
        """
        self.db = db
        self.validation_engine = validation_engine
        self.charts_dir = Path(charts_dir)
        self.charts_dir.mkdir(parents=True, exist_ok=True)

    def explain(self, heuristic: Heuristic, validation_result: ValidationResult) -> Explanation:
        """Produce a full explanation for a validated heuristic.

        Args:
            heuristic: The Heuristic that was validated.
            validation_result: The ValidationResult produced for it.

        Returns:
            An Explanation with narrative text, supporting incidents, and
            chart file paths.
        """
        logs = self.db.get_maintenance_logs()
        readings = self.db.get_sensor_readings()

        supporting_incidents = self._collect_supporting_incidents(heuristic, logs, readings)
        narrative = self._build_narrative(heuristic, validation_result, supporting_incidents)

        timeline_path = self._generate_timeline_chart(heuristic, logs, readings)
        probability_path = self._generate_probability_chart(heuristic, validation_result)

        explanation = Explanation(
            heuristic_id=heuristic.heuristic_id,
            decision=validation_result.decision,
            narrative=narrative,
            supporting_incidents=supporting_incidents,
            timeline_chart_path=str(timeline_path),
            probability_chart_path=str(probability_path),
        )
        logger.info(
            "Generated explanation for heuristic %s (decision=%s, %d supporting incidents, charts at %s / %s)",
            heuristic.heuristic_id, validation_result.decision, len(supporting_incidents),
            timeline_path, probability_path,
        )
        return explanation

    # ------------------------------------------------------------------
    # Supporting incidents
    # ------------------------------------------------------------------

    def _collect_supporting_incidents(
        self, heuristic: Heuristic, logs, readings
    ) -> List[SupportingIncident]:
        """Pick a handful of concrete historical incidents to cite as evidence.

        Prioritizes incidents where the trigger condition actually held
        AND the predicted failure occurred — these are the clearest,
        most citable examples of the pattern, whether the overall
        decision was Accepted or Rejected.
        """
        candidates = []
        for log in logs:
            condition_met = self.validation_engine.evaluate_conditions(
                heuristic.conditions, log, readings
            )
            if condition_met is None:
                continue
            is_target_failure = log.failure_type == heuristic.failure_type
            candidates.append((log, condition_met, is_target_failure))

        # Best evidence first: condition held AND failure matched.
        candidates.sort(key=lambda item: (item[1] and item[2]), reverse=True)

        incidents = [
            SupportingIncident(
                log_id=log.log_id,
                machine_id=log.machine_id,
                timestamp=log.timestamp.isoformat(),
                failure_type=log.failure_type,
                condition_held=condition_met,
                description=log.description,
            )
            for log, condition_met, _ in candidates[:MAX_SUPPORTING_INCIDENTS]
        ]
        return incidents

    # ------------------------------------------------------------------
    # Narrative
    # ------------------------------------------------------------------

    @staticmethod
    def _build_narrative(
        heuristic: Heuristic,
        validation_result: ValidationResult,
        supporting_incidents: List[SupportingIncident],
    ) -> str:
        """Build the full natural-language explanation.

        Reuses ValidationResult.reasoning (already grounded in the actual
        numbers from Phase 4) as the core statistical explanation, and
        adds concrete incident references on top of it.
        """
        lines = [
            f"Heuristic: {heuristic.trigger}",
            f"Machine/Component: {heuristic.machine_id} / {heuristic.component}",
            f"Predicted failure: {heuristic.failure_type}",
            "",
            validation_result.reasoning,
            "",
        ]

        if supporting_incidents:
            lines.append("Representative historical incidents:")
            for incident in supporting_incidents:
                condition_note = "condition held" if incident.condition_held else "condition did not hold"
                lines.append(
                    f"  - {incident.log_id} on {incident.machine_id} at {incident.timestamp} "
                    f"({incident.failure_type}, {condition_note}): {incident.description}"
                )
        else:
            lines.append("No historical incidents could be matched to this trigger's conditions.")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Charts
    # ------------------------------------------------------------------

    def _generate_timeline_chart(self, heuristic: Heuristic, logs, readings) -> Path:
        """Scatter plot of every maintenance event over time, colored by
        whether it's the target failure type and marked by whether the
        trigger condition held — makes the clustering (or lack thereof)
        visually obvious."""
        fig, ax = plt.subplots(figsize=(10, 4))

        for log in logs:
            condition_met = self.validation_engine.evaluate_conditions(
                heuristic.conditions, log, readings
            )
            if condition_met is None:
                continue

            is_target = log.failure_type == heuristic.failure_type
            color = "#d62728" if is_target else "#7f7f7f"
            marker = "o" if condition_met else "x"
            ax.scatter(log.timestamp, 1, color=color, marker=marker, s=60, alpha=0.7)

        ax.set_yticks([])
        ax.set_xlabel("Date")
        ax.set_title(f"Timeline: {heuristic.trigger}\n(red = {heuristic.failure_type}, "
                     f"gray = other; o = condition held, x = condition not held)")
        fig.autofmt_xdate()
        fig.tight_layout()

        chart_path = self.charts_dir / f"{heuristic.heuristic_id}_timeline.png"
        fig.savefig(chart_path, dpi=100)
        plt.close(fig)
        return chart_path

    def _generate_probability_chart(
        self, heuristic: Heuristic, validation_result: ValidationResult
    ) -> Path:
        """Bar chart comparing conditional probability against the
        dataset's baseline failure rate — the visual case for why the
        pattern is (or isn't) meaningfully different from chance."""
        fig, ax = plt.subplots(figsize=(5, 4))

        labels = ["When condition\nheld", "Baseline rate\n(all events)"]
        # Baseline rate isn't stored on ValidationResult directly, so we
        # recompute it the same simple way ValidationEngine does: overall
        # fraction of logs matching this failure_type.
        logs = self.db.get_maintenance_logs()
        overall_rate = (
            sum(1 for log in logs if log.failure_type == heuristic.failure_type) / len(logs)
            if logs else 0.0
        )
        values = [validation_result.conditional_probability, overall_rate]
        colors = ["#2ca02c" if validation_result.decision == "Accepted" else "#d62728", "#7f7f7f"]

        ax.bar(labels, values, color=colors)
        ax.set_ylim(0, 1)
        ax.set_ylabel(f"P({heuristic.failure_type})")
        ax.set_title(f"{heuristic.heuristic_id}: {validation_result.decision}\n"
                     f"p={validation_result.chi_square_p_value:.4g}, "
                     f"correlation={validation_result.pearson_correlation:.3f}")
        for i, v in enumerate(values):
            ax.text(i, v + 0.02, f"{v*100:.1f}%", ha="center")

        fig.tight_layout()

        chart_path = self.charts_dir / f"{heuristic.heuristic_id}_probability.png"
        fig.savefig(chart_path, dpi=100)
        plt.close(fig)
        return chart_path