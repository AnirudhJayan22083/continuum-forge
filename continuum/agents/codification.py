import json
from pathlib import Path
from continuum.models.heuristic import Heuristic
from continuum.models.validation import ValidationResult

class CodificationAgent:
    def __init__(self, output_file: str = "continuum/data/knowledge_base.json"):
        self.output_file = Path(output_file)
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
    def codify(self, heuristic: Heuristic, validation: ValidationResult):
        # We only codify accepted heuristics
        if not validation.accepted:
            return None
            
        data = {
            "machine": heuristic.machine,
            "component": heuristic.component,
            "failure_mode": heuristic.failure,
            "trigger": heuristic.trigger,
            "conditions": heuristic.conditions,
            "symptoms": heuristic.symptoms,
            "confidence_score": validation.conditional_probability,
            "p_value": validation.p_value,
            "explanation": validation.explanation
        }
        
        knowledge_base = []
        if self.output_file.exists():
            try:
                with open(self.output_file, 'r') as f:
                    knowledge_base = json.load(f)
            except Exception:
                pass
                
        knowledge_base.append(data)
        
        with open(self.output_file, 'w') as f:
            json.dump(knowledge_base, f, indent=4)
            
        return data
