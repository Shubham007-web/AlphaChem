"""Load a chat model through the Azure OpenAI API using LangChain.

All secrets are read from the gitignored .env file:
    AZURE_OPENAI_API_KEY
    AZURE_OPENAI_ENDPOINT
    AZURE_OPENAI_DEPLOYMENT
    OPENAI_API_VERSION
"""
import os

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

load_dotenv()


def _get(name, default=None):
    # .strip() guards against stray spaces after '=' in the .env file
    value = os.environ.get(name, default)
    return value.strip() if isinstance(value, str) else value


def load_azure_llm(temperature=0.7, max_tokens=8192):
    """Build and return an AzureChatOpenAI chat model."""
    endpoint = _get("AZURE_OPENAI_ENDPOINT")
    deployment = _get("AZURE_OPENAI_DEPLOYMENT")
    api_key = _get("AZURE_OPENAI_API_KEY")
    api_version = _get("OPENAI_API_VERSION", "2024-10-21")

    missing = [n for n, v in [
        ("AZURE_OPENAI_ENDPOINT", endpoint),
        ("AZURE_OPENAI_DEPLOYMENT", deployment),
        ("AZURE_OPENAI_API_KEY", api_key),
    ] if not v]
    if missing:
        raise RuntimeError(f"Missing Azure settings in .env: {', '.join(missing)}")

    return AzureChatOpenAI(
        azure_endpoint=endpoint,
        azure_deployment=deployment,
        api_key=api_key,
        api_version=api_version,
        temperature=temperature,
        max_tokens=max_tokens,
    )


if __name__ == "__main__":
    llm = load_azure_llm(max_tokens=20)
    print(f"Loaded Azure deployment: {_get('AZURE_OPENAI_DEPLOYMENT')}")
    print("Test response:", repr(llm.invoke("Reply with the single word: ready").content))
