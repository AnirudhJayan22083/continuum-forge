import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency, pearsonr
from continuum.models.heuristic import Heuristic
from continuum.models.validation import ValidationResult

class ValidationEngine:
    def __init__(self, sensor_data_path: str, logs_data_path: str):
        # In a real app, this would connect to the database.
        self.sensor_df = pd.read_csv(sensor_data_path)
        self.logs_df = pd.read_csv(logs_data_path)
        
        # Ensure timestamps are parsed if needed, though exact string match works for our synthetic data
        self.sensor_df['timestamp'] = pd.to_datetime(self.sensor_df['timestamp'])
        self.logs_df['timestamp'] = pd.to_datetime(self.logs_df['timestamp'])

    def validate(self, heuristic: Heuristic) -> ValidationResult:
        # Filter data for the specific machine (or apply globally if heuristic applies to all)
        # We'll apply it globally for the machine model if machine is provided.
        # If machine is 'ALL', we use all data.
        s_df = self.sensor_df
        l_df = self.logs_df
        
        if heuristic.machine and heuristic.machine != "ALL":
            s_df = s_df[s_df['machine_id'] == heuristic.machine]
            l_df = l_df[l_df['machine_id'] == heuristic.machine]
            
        # Merge datasets: left join sensor history with maintenance logs
        # This aligns the hourly sensor readings with any failures that happened in that hour
        merged_df = pd.merge(s_df, l_df, on=['machine_id', 'timestamp'], how='left')
        
        # Target variable: Did the specified failure mode occur?
        merged_df['is_failure'] = (merged_df['failure_mode'] == heuristic.failure)
        
        # Evaluate conditions
        condition_str = " and ".join(heuristic.conditions)
        if not condition_str:
            # If no conditions provided, we can't validate properly.
            return self._build_rejected_result("No measurable conditions provided in heuristic.")
            
        try:
            # Pandas eval handles expressions like "humidity_percent > 80"
            merged_df['condition_met'] = merged_df.eval(condition_str)
        except Exception as e:
            return self._build_rejected_result(f"Failed to parse conditions '{condition_str}': {str(e)}")

        # 2x2 Contingency Table calculations
        # A: Condition Met, Failure Occurred (True Positives)
        A = len(merged_df[merged_df['condition_met'] & merged_df['is_failure']])
        # B: Condition Met, No Failure (False Positives)
        B = len(merged_df[merged_df['condition_met'] & ~merged_df['is_failure']])
        # C: Condition Not Met, Failure Occurred (False Negatives)
        C = len(merged_df[~merged_df['condition_met'] & merged_df['is_failure']])
        # D: Condition Not Met, No Failure (True Negatives)
        D = len(merged_df[~merged_df['condition_met'] & ~merged_df['is_failure']])
        
        support_count = A
        total_condition_met = A + B
        
        if total_condition_met == 0:
            return self._build_rejected_result("Condition was never met in historical data.")
            
        conditional_probability = A / total_condition_met
        
        # Pearson Correlation (phi coefficient for binary variables)
        x = merged_df['condition_met'].astype(int)
        y = merged_df['is_failure'].astype(int)
        
        if len(x.unique()) < 2 or len(y.unique()) < 2:
             pearson_corr = 0.0
             p_value = 1.0
             chi2 = 0.0
        else:
            pearson_corr, _ = pearsonr(x, y)
            
            # Chi-square test
            contingency_table = [[A, B], [C, D]]
            chi2, p_value, _, _ = chi2_contingency(contingency_table)

        # Decision Logic (Statistical Confidence)
        # We demand p < 0.05 for significance, and a positive correlation
        accepted = bool(p_value < 0.05 and pearson_corr > 0.1 and conditional_probability > 0.3)
        
        explanation = self._generate_explanation(
            accepted, A, total_condition_met, conditional_probability, p_value, heuristic.failure
        )

        return ValidationResult(
            accepted=accepted,
            support_count=support_count,
            conditional_probability=float(conditional_probability),
            pearson_correlation=float(pearson_corr),
            chi_square_stat=float(chi2),
            p_value=float(p_value),
            explanation=explanation
        )

    def _build_rejected_result(self, reason: str) -> ValidationResult:
        return ValidationResult(
            accepted=False,
            support_count=0,
            conditional_probability=0.0,
            pearson_correlation=0.0,
            chi_square_stat=0.0,
            p_value=1.0,
            explanation=reason
        )
        
    def _generate_explanation(self, accepted: bool, true_positives: int, total_condition: int, prob: float, p_val: float, failure: str) -> str:
        base = (
            f"The condition occurred {total_condition} times historically, "
            f"and was followed by '{failure}' {true_positives} times ({prob*100:.1f}% probability). "
        )
        if accepted:
            return base + f"With a p-value of {p_val:.4e}, this relationship is statistically significant and the heuristic is ACCEPTED as operational knowledge."
        else:
            return base + f"With a p-value of {p_val:.4e}, this relationship is NOT statistically significant. The heuristic is REJECTED as folklore."
