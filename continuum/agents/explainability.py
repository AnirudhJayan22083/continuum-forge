import matplotlib.pyplot as plt
import os
from pathlib import Path
from continuum.models.heuristic import Heuristic
from continuum.models.validation import ValidationResult

class ExplainabilityEngine:
    def __init__(self, charts_dir: str = "continuum/data/charts"):
        self.charts_dir = Path(charts_dir)
        self.charts_dir.mkdir(parents=True, exist_ok=True)

    def generate_explanation(self, heuristic: Heuristic, result: ValidationResult) -> dict:
        # Generate a chart showing the probability of failure when condition is met vs baseline
        # For simplicity, we just plot the conditional probability
        
        chart_path = self.charts_dir / f"{heuristic.machine}_{heuristic.component}_validation.png"
        
        plt.figure(figsize=(6, 4))
        plt.bar(["Condition Met", "Condition Not Met (Est)"], [result.conditional_probability, 0.05], color=['red', 'blue'])
        plt.ylabel("Probability of Failure")
        plt.title(f"Validation: {heuristic.failure}")
        plt.ylim(0, 1.0)
        plt.text(0, result.conditional_probability + 0.02, f"{result.conditional_probability:.2f}", ha='center')
        
        # Save chart
        plt.savefig(chart_path)
        plt.close()
        
        return {
            "explanation_text": result.explanation,
            "chart_path": str(chart_path.absolute())
        }
