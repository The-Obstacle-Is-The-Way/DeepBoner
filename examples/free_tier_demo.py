"""
Demo of the Free Tier (HuggingFace Inference) capability.
This script demonstrates running the full search-judge loop WITHOUT an OpenAI key.
"""

import asyncio
import os

from dotenv import load_dotenv
from pydantic_ai.models.huggingface import HuggingFaceModel

from src.agent_factory.judges import JudgeHandler
from src.orchestrator_factory import create_orchestrator
from src.tools.pubmed import PubMedTool
from src.tools.search_handler import SearchHandler
from src.utils.models import OrchestratorConfig

# Load env but DON'T require OPENAI_API_KEY
load_dotenv()


async def main():
    print("🚀 Starting Free Tier Demo (No OpenAI Key Required)")

    # 1. Configure explicitly for HuggingFace
    # Using a known good model for free inference
    model_name = "meta-llama/Llama-3.1-8B-Instruct"
    print(f"🤗 Using HuggingFace Model: {model_name}")

    try:
        model = HuggingFaceModel(model_name)
    except Exception as e:
        print(f"❌ Error creating HF model (Token issue?): {e}")
        return

    # 2. Create Handlers
    judge_handler = JudgeHandler(model=model)
    search_handler = SearchHandler(
        tools=[PubMedTool()],  # Just PubMed for speed
        timeout=10,
    )

    # 3. Create Orchestrator
    orchestrator = create_orchestrator(
        search_handler=search_handler,
        judge_handler=judge_handler,
        config=OrchestratorConfig(max_iterations=2),  # Short run
    )

    # 4. Run it
    query = "What is the mechanism of action of Metformin in cancer?"
    print(f"\n🔎 Query: {query}")

    async for event in orchestrator.run(query):
        print(f"\n[Event: {event.type}]")
        print(event.message)

        if event.type == "complete":
            print("\n✅ SUCCESS: Pipeline completed using Free Tier!")
            # print(event.data)


if __name__ == "__main__":
    # Unset OpenAI key to prove we aren't using it
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]
        print("[INFO] Unset OPENAI_API_KEY for this demo to ensure free tier usage.")

    asyncio.run(main())
