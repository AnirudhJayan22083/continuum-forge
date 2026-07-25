import json
from pathlib import Path
from continuum.utils.llm import LLMInterface
from continuum.models.maintenance import MaintenanceLog

class ElicitationAgent:
    def __init__(self, llm: LLMInterface):
        self.llm = llm
        self.system_prompt = (
            "You are an expert industrial maintenance interviewer. Your job is to extract tacit knowledge "
            "from experienced technicians regarding a specific machine failure incident. "
            "Ask grounded, specific questions to figure out the exact triggers, conditions, and symptoms "
            "that the technician uses as rules of thumb."
        )

    def generate_initial_question(self, incident: dict) -> str:
        prompt = (
            f"We are investigating an incident: {incident['log_id']} on {incident['machine_id']}. "
            f"Component: {incident['component']}, Failure: {incident['failure_mode']}, Action: {incident['action_taken']}. "
            "Generate the first interview question to ask the technician about what they noticed before this failure."
        )
        return self.llm.generate_response(prompt, system_instruction=self.system_prompt)

    def generate_followup(self, transcript_history: str) -> str:
        prompt = (
            "Here is the transcript so far:\n"
            f"{transcript_history}\n\n"
            "Generate one intelligent follow-up question to dig deeper into the specific conditions and symptoms."
        )
        return self.llm.generate_response(prompt, system_instruction=self.system_prompt)

    def save_transcript(self, technician_id: str, incident_id: str, transcript_text: str, output_dir: str = "continuum/data"):
        file_path = Path(output_dir) / f"transcript_{technician_id}_{incident_id}.json"
        data = {
            "technician": technician_id,
            "incident": incident_id,
            "transcript": transcript_text
        }
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
        return str(file_path)
