import os
from langchain_core.messages import HumanMessage, SystemMessage

from src.utils.llm_provider import get_llm_model

def create_message_content(text, image_path=None):
    # Simple Gemini prompt formatting
    return text if not image_path else f"{text} [image: {image_path}]"

def get_env_value(key, provider):
    # Only for Gemini, just fetch from environment
    return os.getenv("GOOGLE_API_KEY", "")

def test_llm(config, query, image_path=None, system_message=None):
    llm = get_llm_model(
        provider="google",
        model_name="gemini-1.5-flash",
        temperature=config.get("temperature", 0.0),
        base_url=config.get("base_url", None),
        api_key=config.get("api_key", get_env_value("api_key", "google")),
    )

    messages = []
    if system_message:
        messages.append(SystemMessage(content=create_message_content(system_message)))
    messages.append(HumanMessage(content=create_message_content(query, image_path)))
    ai_msg = llm.invoke(messages)
    print(ai_msg.content)

if __name__ == "__main__":
    config = {
        "api_key": get_env_value("api_key", "google"),
        "temperature": 0.0,
        "base_url": None,
    }
    test_llm(config, "Describe this image", "assets/examples/test.png", system_message="You are a helpful AI assistant.")