import os
import json
from abc import ABC, abstractmethod
from google import genai
from dotenv import load_dotenv

load_dotenv()

class LLMInterface(ABC):
    @abstractmethod
    def generate_response(self, prompt: str, system_instruction: str = "") -> str:
        pass

class RealGemini(LLMInterface):
    def __init__(self, model_name: str = "gemini-3-flash-preview"):
        self.model_name = model_name
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    def generate_response(self, prompt: str, system_instruction: str = "") -> str:
        # Note: The google-genai library uses the 'gemini-3-flash' model family.
        # We will pass the model_name provided.
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
            )
        )
        return response.text

class MockGemini(LLMInterface):
    def __init__(self, predefined_responses: dict = None):
        self.responses = predefined_responses or {}

    def generate_response(self, prompt: str, system_instruction: str = "") -> str:
        # In a real test, you'd match prompt keywords to responses
        return self.responses.get(prompt, "This is a mock response from the LLM.")
