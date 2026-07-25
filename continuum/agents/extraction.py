import json
from continuum.utils.llm import LLMInterface
from continuum.models.heuristic import Heuristic

class KnowledgeExtractionAgent:
    def __init__(self, llm: LLMInterface):
        self.llm = llm
        self.system_prompt = (
            "You are an expert industrial knowledge extraction engine. "
            "Your job is to read an interview transcript between an interviewer and a technician, "
            "and extract the tacit knowledge into a structured heuristic. "
            "Return ONLY a valid JSON object matching the requested schema without any markdown formatting."
        )
        self.schema_definition = """
{
    "machine": "string (e.g., MACH-A)",
    "component": "string (e.g., Bearing)",
    "failure": "string (e.g., Bearing Failure)",
    "trigger": "string (The core underlying trigger)",
    "conditions": ["string (e.g., 'humidity_percent > 80')", "string (e.g., 'vibration_mm_s > 3.0')"],
    "symptoms": ["string", "string"],
    "recommended_action": "string",
    "expert_confidence": float (0.0 to 1.0)
}
IMPORTANT: The 'conditions' array MUST be formatted as valid Pandas queries using ONLY the variables 'humidity_percent' and 'vibration_mm_s'. Do NOT use natural language for conditions, use exact math expressions. For example, 'humidity_percent > 80'.
"""

    def extract_heuristic(self, transcript: str) -> Heuristic:
        prompt = (
            "Extract the heuristic from the following transcript.\n\n"
            f"TRANSCRIPT:\n{transcript}\n\n"
            "OUTPUT FORMAT:\n"
            f"{self.schema_definition}\n"
            "Respond strictly with the raw JSON string."
        )
        
        response_text = self.llm.generate_response(prompt, system_instruction=self.system_prompt)
        
        # Clean up possible markdown wrappers if the LLM ignores instructions
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        data = json.loads(response_text.strip())
        return Heuristic(**data)
