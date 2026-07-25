import json
from pathlib import Path
from continuum.utils.llm import LLMInterface

class MentorAgent:
    def __init__(self, llm: LLMInterface, knowledge_base_path: str = "continuum/data/knowledge_base.json"):
        self.llm = llm
        self.kb_path = Path(knowledge_base_path)
        
    def advise(self, user_query: str) -> str:
        knowledge = []
        if self.kb_path.exists():
            with open(self.kb_path, 'r') as f:
                knowledge = json.load(f)
                
        system_prompt = (
            "You are Continuum, a Mentor Agent advising junior technicians. "
            "You have access to a statistically validated knowledge base of historical maintenance rules. "
            "Answer the user's question based ONLY on the provided knowledge base rules. "
            "If the knowledge base does not contain the answer, say you don't know."
        )
        
        prompt = (
            f"Knowledge Base Data:\n{json.dumps(knowledge, indent=2)}\n\n"
            f"Technician Query: {user_query}\n\n"
            "Provide your advice based on the knowledge base."
        )
        
        return self.llm.generate_response(prompt, system_instruction=system_prompt)
