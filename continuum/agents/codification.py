"""
agents/codification.py

CodificationAgent: converts an Accepted Heuristic (plus its
ValidationResult) into a stored OperationalRule, and produces a static
diagram of the rule's causal chain for demo purposes.

Duplicate detection (Machine + Failure + Trigger + Condition) is already
implemented in Database.insert_operational_rule / Database.is_duplicate_rule
(Phase 1) — this agent doesn't reimplement that logic, only uses it.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # headless environment, same as ExplainabilityEngine
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from database.sqlite import Database
from models.heuristic import Heuristic
from models.operational_rule import OperationalRule
from models.validation import ValidationResult

logger = logging.getLogger(__name__)

DEFAULT_DIAGRAMS_DIR = "data/diagrams"


class CodificationError(Exception):
    """Raised when codification is attempted on a heuristic that hasn't
    actually been Accepted. Codifying a Rejected (or not-yet-validated)
    heuristic into an operational rule would defeat the entire point of
    the validation step, so this fails loudly rather than silently
    proceeding."""


@dataclass
class CodificationResult:
    """Outcome of a codification attempt."""

    rule: OperationalRule
    inserted: bool  # False if this was a duplicate of an existing rule
    diagram_path: str


class CodificationAgent:
    """Converts Accepted heuristics into stored OperationalRule records."""

    def __init__(self, db: Database, diagrams_dir: str = DEFAULT_DIAGRAMS_DIR):
        """Initialize the agent.

        Args:
            db: Connected Database instance to store rules in.
            diagrams_dir: Directory to save generated diagram PNGs to.
        """
        self.db = db
        self.diagrams_dir = Path(diagrams_dir)
        self.diagrams_dir.mkdir(parents=True, exist_ok=True)

    def codify(
        self,
        heuristic: Heuristic,
        validation_result: ValidationResult,
        rule_id: str,
        created_timestamp: Union[str, datetime],
    ) -> CodificationResult:
        """Convert an Accepted Heuristic into a stored OperationalRule.

        Args:
            heuristic: The Heuristic to codify.
            validation_result: Its ValidationResult — must have decision
                == "Accepted".
            rule_id: Unique ID to assign to the resulting OperationalRule.
            created_timestamp: When this rule is being created.

        Returns:
            A CodificationResult with the rule, whether it was actually
            inserted (False if it was a duplicate of an existing rule),
            and the path to the generated diagram.

        Raises:
            CodificationError: if validation_result.decision != "Accepted".
        """
        if validation_result.decision != "Accepted":
            raise CodificationError(
                f"Cannot codify heuristic {heuristic.heuristic_id}: its ValidationResult "
                f"decision is '{validation_result.decision}', not 'Accepted'. Only "
                f"statistically validated heuristics may become operational rules."
            )

        rule = OperationalRule(
            rule_id=rule_id,
            heuristic_id=heuristic.heuristic_id,
            machine_id=heuristic.machine_id,
            component=heuristic.component,
            failure_type=heuristic.failure_type,
            trigger=heuristic.trigger,
            conditions=heuristic.conditions,
            recommended_action=heuristic.recommended_action,
            confidence_score=validation_result.confidence_score,
            created_timestamp=created_timestamp,
        )

        inserted = self.db.insert_operational_rule(rule)
        if inserted:
            logger.info("Codified new operational rule %s from heuristic %s", rule_id, heuristic.heuristic_id)
        else:
            logger.info(
                "Rule %s is a duplicate of an existing operational rule for %s/%s/%s — not re-inserted",
                rule_id, heuristic.machine_id, heuristic.failure_type, heuristic.trigger,
            )

        diagram_path = self._generate_diagram(heuristic, rule)

        return CodificationResult(rule=rule, inserted=inserted, diagram_path=str(diagram_path))

    # ------------------------------------------------------------------
    # Diagram generation
    # ------------------------------------------------------------------

    def _generate_diagram(self, heuristic: Heuristic, rule: OperationalRule) -> Path:
        """Generate a static diagram of the rule's causal chain:
        Machine -> Component -> Condition -> Symptom -> Failure -> Recommended Action.

        For demo purposes only — this is not used anywhere in the actual
        validation/decision logic.
        """
        stages = [
            ("Machine", heuristic.machine_id),
            ("Component", heuristic.component),
            ("Condition", heuristic.trigger),
            ("Symptom", ", ".join(heuristic.symptoms) if heuristic.symptoms else "(none recorded)"),
            ("Failure", heuristic.failure_type),
            ("Recommended Action", heuristic.recommended_action),
        ]

        fig, ax = plt.subplots(figsize=(6, 12))
        ax.set_xlim(0, 10)
        ax.set_ylim(0, len(stages) * 2)
        ax.axis("off")

        box_height = 1.4
        box_width = 8
        x_center = 5

        for i, (label, value) in enumerate(stages):
            # Stack top-to-bottom
            y_top = len(stages) * 2 - (i * 2) - 1

            box = FancyBboxPatch(
                (x_center - box_width / 2, y_top - box_height / 2),
                box_width, box_height,
                boxstyle="round,pad=0.1",
                edgecolor="#333333",
                facecolor="#e8f0fe" if i % 2 == 0 else "#fff3e0",
            )
            ax.add_patch(box)

            wrapped_value = value if len(value) <= 45 else value[:42] + "..."
            ax.text(
                x_center, y_top, f"{label}\n{wrapped_value}",
                ha="center", va="center", fontsize=9, wrap=True,
            )

            if i < len(stages) - 1:
                arrow = FancyArrowPatch(
                    (x_center, y_top - box_height / 2),
                    (x_center, y_top - 2 + box_height / 2),
                    arrowstyle="-|>", mutation_scale=15, color="#333333",
                )
                ax.add_patch(arrow)

        ax.set_title(f"Operational Rule: {rule.rule_id}", fontsize=11, pad=10)
        fig.tight_layout()

        diagram_path = self.diagrams_dir / f"{rule.rule_id}_chain.png"
        fig.savefig(diagram_path, dpi=100)
        plt.close(fig)
        return diagram_path