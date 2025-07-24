import os
import sys
import asyncio
from pprint import pprint

from dotenv import load_dotenv
load_dotenv()
sys.path.append(".")

from browser_use.agent.views import AgentHistoryList
from src.utils import llm_provider

async def test_browser_use_agent():
    from browser_use.browser.browser import BrowserConfig
    from browser_use.browser.context import BrowserContextConfig
    from src.browser.custom_browser import CustomBrowser
    from src.controller.custom_controller import CustomController
    from src.agent.browser_use.browser_use_agent import BrowserUseAgent

    llm = llm_provider.get_llm_model(
        provider="google",
        model_name="gemini-1.5-flash",
        temperature=0.6,
        api_key=os.getenv("GOOGLE_API_KEY", "")
    )

    window_w, window_h = 1280, 1100

    mcp_server_config = {
        "mcpServers": {
            "desktop-commander": {
                "command": "npx",
                "args": [
                    "-y",
                    "@wonderwhy-er/desktop-commander"
                ]
            },
        }
    }
    controller = CustomController()
    await controller.setup_mcp_client(mcp_server_config)
    use_own_browser = True
    use_vision = True

    max_actions_per_step = 10
    browser = None
    browser_context = None

    try:
        extra_browser_args = []
        if use_own_browser:
            browser_binary_path = os.getenv("BROWSER_PATH", None)
            if browser_binary_path == "":
                browser_binary_path = None
            browser_user_data = os.getenv("BROWSER_USER_DATA", None)
            if browser_user_data:
                extra_browser_args += [f"--user-data-dir={browser_user_data}"]
        else:
            browser_binary_path = None
        browser = CustomBrowser(
            config=BrowserConfig(
                headless=False,
                browser_binary_path=browser_binary_path,
                extra_browser_args=extra_browser_args,
                new_context_config=BrowserContextConfig(
                    window_width=window_w,
                    window_height=window_h,
                )
            )
        )
        browser_context = await browser.new_context(
            config=BrowserContextConfig(
                trace_path=None,
                save_recording_path=None,
                save_downloads_path="./tmp/downloads",
                window_height=window_h,
                window_width=window_w,
            )
        )
        agent = BrowserUseAgent(
            task="give me nvidia stock price",
            llm=llm,
            browser=browser,
            browser_context=browser_context,
            controller=controller,
            use_vision=use_vision,
            max_actions_per_step=max_actions_per_step,
            generate_gif=True
        )
        history: AgentHistoryList = await agent.run(max_steps=100)

        print("Final Result:")
        pprint(history.final_result(), indent=4)

        print("\nErrors:")
        pprint(history.errors(), indent=4)

    except Exception:
        import traceback
        traceback.print_exc()
    finally:
        if browser_context:
            await browser_context.close()
        if browser:
            await browser.close()
        if controller:
            await controller.close_mcp_client()

async def test_deep_research_agent():
    from src.agent.deep_research.deep_research_agent import DeepResearchAgent, PLAN_FILENAME, REPORT_FILENAME
    from src.utils import llm_provider

    llm = llm_provider.get_llm_model(
        provider="google",
        model_name="gemini-1.5-flash",
        temperature=0.5,
        api_key=os.getenv("GOOGLE_API_KEY", "")
    )

    mcp_server_config = {
        "mcpServers": {
            "desktop-commander": {
                "command": "npx",
                "args": [
                    "-y",
                    "@wonderwhy-er/desktop-commander"
                ]
            },
        }
    }

    browser_config = {"headless": False, "window_width": 1280, "window_height": 1100, "use_own_browser": False}
    agent = DeepResearchAgent(llm=llm, browser_config=browser_config, mcp_server_config=mcp_server_config)
    research_topic = "Give me investment advices of nvidia and tesla."
    task_id_to_resume = ""  # Set this to resume a previous task ID

    print(f"Starting research on: {research_topic}")

    try:
        result = await agent.run(research_topic,
                                 task_id=task_id_to_resume,
                                 save_dir="./tmp/deep_research",
                                 max_parallel_browsers=1,
                                 )

        print("\n--- Research Process Ended ---")
        print(f"Status: {result.get('status')}")
        print(f"Message: {result.get('message')}")
        print(f"Task ID: {result.get('task_id')}")

        final_state = result.get('final_state', {})
        if final_state:
            print("\n--- Final State Summary ---")
            print(
                f"  Plan Steps Completed: {sum(1 for item in final_state.get('research_plan', []) if item.get('status') == 'completed')}")
            print(f"  Total Search Results Logged: {len(final_state.get('search_results', []))}")
            if final_state.get("final_report"):
                print("  Final Report: Generated (content omitted). You can find it in the output directory.")
            else:
                print("  Final Report: Not generated.")
        else:
            print("Final state information not available.")

    except Exception as e:
        print(f"\n--- An unhandled error occurred outside the agent run ---")
        print(e)

if __name__ == "__main__":
    asyncio.run(test_browser_use_agent())
    # asyncio.run(test_deep_research_agent())