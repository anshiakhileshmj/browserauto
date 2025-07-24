import os
from typing import Any, Optional

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langchain_core.language_models.base import BaseLanguageModel, LanguageModelInput, RunnableConfig

# If you use langchain-google-genai or a similar SDK, import it here:
# from langchain_google_genai import ChatGoogleGenerativeAI

class ChatGeminiFlash(BaseLanguageModel):
    def __init__(self, model_name="gemini-1.5-flash", temperature=0.0, api_key=None, base_url=None, **kwargs):
        super().__init__()
        self.model_name = model_name
        self.temperature = temperature
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.base_url = base_url

    def invoke(self, input: LanguageModelInput, config: Optional[RunnableConfig] = None, **kwargs) -> AIMessage:
        # Replace below with actual Gemini API call (this is a stub)
        # If using SDK, call it here.
        prompt = ""
        if isinstance(input, list):
            prompt = "\n".join(m.content for m in input if hasattr(m, "content"))
        elif hasattr(input, "content"):
            prompt = input.content
        else:
            prompt = str(input)
        response_content = f"[Gemini 1.5 Flash stub] Response to: {prompt}"
        return AIMessage(content=response_content)

    async def ainvoke(self, input: LanguageModelInput, config: Optional[RunnableConfig] = None, **kwargs) -> AIMessage:
        # Replace below with actual Gemini API call (async)
        prompt = ""
        if isinstance(input, list):
            prompt = "\n".join(m.content for m in input if hasattr(m, "content"))
        elif hasattr(input, "content"):
            prompt = input.content
        else:
            prompt = str(input)
        response_content = f"[Gemini 1.5 Flash stub (async)] Response to: {prompt}"
        return AIMessage(content=response_content)

def get_llm_model(provider: str = None, **kwargs):
    """
    Always returns Gemini 1.5 Flash LLM.
    Ignores provider/model_name, uses only Gemini 1.5 Flash.
    """
    api_key = kwargs.get("api_key", "") or os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        raise ValueError("💥 Google Gemini API key not found! 🔑 Please set the `GOOGLE_API_KEY` environment variable or provide it in the UI.")

    model_name = "gemini-1.5-flash"
    temperature = kwargs.get("temperature", 0.0)
    base_url = kwargs.get("base_url", None)

    return ChatGeminiFlash(
        model_name=model_name,
        temperature=temperature,
        api_key=api_key,
        base_url=base_url,
    )