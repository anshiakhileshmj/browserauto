import gradio as gr
from gradio.components import Component
from functools import partial

from src.webui.webui_manager import WebuiManager
from src.utils import config
import logging
import os
from typing import Any, Dict, AsyncGenerator, Optional, Tuple, Union
import asyncio
import json
from src.agent.deep_research.deep_research_agent import DeepResearchAgent
from src.utils import llm_provider

logger = logging.getLogger(__name__)

async def _initialize_llm(
    provider: Optional[str], model_name: Optional[str], temperature: float,
    base_url: Optional[str], api_key: Optional[str], num_ctx: Optional[int] = None
):
    """Initializes Google Gemini 1.5 Flash LLM (ignores other providers/models)."""
    provider = "google"
    model_name = "gemini-1.5-flash"
    try:
        logger.info(f"Initializing LLM: Provider={provider}, Model={model_name}, Temp={temperature}")
        llm = llm_provider.get_llm_model(
            provider=provider,
            model_name=model_name,
            temperature=temperature,
            base_url=base_url or None,
            api_key=api_key or None,
        )
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize Gemini LLM: {e}", exc_info=True)
        gr.Warning(
            f"Failed to initialize Gemini LLM. Please check settings. Error: {e}")
        return None

def _read_file_safe(file_path: str) -> Optional[str]:
    """Safely read a file, returning None if it doesn't exist or on error."""
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None

# --- Deep Research Agent Specific Logic ---

async def run_deep_research(webui_manager: WebuiManager, components: Dict[Component, Any]) -> AsyncGenerator[
    Dict[Component, Any], None]:
    """Handles initializing and running the DeepResearchAgent."""

    # --- Get Components ---
    research_task_comp = webui_manager.get_component_by_id("deep_research_agent.research_task")
    resume_task_id_comp = webui_manager.get_component_by_id("deep_research_agent.resume_task_id")
    parallel_num_comp = webui_manager.get_component_by_id("deep_research_agent.parallel_num")
    save_dir_comp = webui_manager.get_component_by_id("deep_research_agent.max_query")
    start_button_comp = webui_manager.get_component_by_id("deep_research_agent.start_button")
    stop_button_comp = webui_manager.get_component_by_id("deep_research_agent.stop_button")
    markdown_display_comp = webui_manager.get_component_by_id("deep_research_agent.markdown_display")
    markdown_download_comp = webui_manager.get_component_by_id("deep_research_agent.markdown_download")
    mcp_server_config_comp = webui_manager.get_component_by_id("deep_research_agent.mcp_server_config")

    # --- 1. Get Task and Settings ---
    task_topic = components.get(research_task_comp, "").strip()
    task_id_to_resume = components.get(resume_task_id_comp, "").strip() or None
    max_parallel_agents = int(components.get(parallel_num_comp, 1))
    base_save_dir = components.get(save_dir_comp, "./tmp/deep_research").strip()
    safe_root_dir = "./tmp/deep_research"
    normalized_base_save_dir = os.path.abspath(os.path.normpath(base_save_dir))
    if os.path.commonpath([normalized_base_save_dir, os.path.abspath(safe_root_dir)]) != os.path.abspath(safe_root_dir):
        logger.warning(f"Unsafe base_save_dir detected: {base_save_dir}. Using default directory.")
        normalized_base_save_dir = os.path.abspath(safe_root_dir)
    base_save_dir = normalized_base_save_dir
    mcp_server_config_str = components.get(mcp_server_config_comp)
    mcp_config = json.loads(mcp_server_config_str) if mcp_server_config_str else None

    if not task_topic:
        gr.Warning("Please enter a research task.")
        yield {start_button_comp: gr.update(interactive=True)}
        return

    # Store base save dir for stop handler
    webui_manager.dr_save_dir = base_save_dir
    os.makedirs(base_save_dir, exist_ok=True)

    # --- 2. Initial UI Update ---
    yield {
        start_button_comp: gr.update(value="⏳ Running...", interactive=False),
        stop_button_comp: gr.update(interactive=True),
        research_task_comp: gr.update(interactive=False),
        resume_task_id_comp: gr.update(interactive=False),
        parallel_num_comp: gr.update(interactive=False),
        save_dir_comp: gr.update(interactive=False),
        markdown_display_comp: gr.update(value="Starting research..."),
        markdown_download_comp: gr.update(value=None, interactive=False)
    }

    agent_task = None
    running_task_id = None
    plan_file_path = None
    report_file_path = None
    last_plan_content = None
    last_plan_mtime = 0

    try:
        # --- 3. Get LLM and Browser Config from other tabs ---
        def get_setting(tab: str, key: str, default: Any = None):
            comp = webui_manager.id_to_component.get(f"{tab}.{key}")
            return components.get(comp, default) if comp else default

        # LLM Config (from agent_settings tab)
        llm_temperature = max(get_setting("agent_settings", "llm_temperature", 0.5), 0.5)
        llm_base_url = get_setting("agent_settings", "llm_base_url")
        llm_api_key = get_setting("agent_settings", "llm_api_key")
        ollama_num_ctx = get_setting("agent_settings", "ollama_num_ctx")

        llm = await _initialize_llm(
            None, None, llm_temperature, llm_base_url, llm_api_key, None
        )
        if not llm:
            raise ValueError("LLM Initialization failed. Please check Agent Settings.")

        browser_config_dict = {
            "headless": get_setting("browser_settings", "headless", False),
            "disable_security": get_setting("browser_settings", "disable_security", False),
            "browser_binary_path": get_setting("browser_settings", "browser_binary_path"),
            "user_data_dir": get_setting("browser_settings", "browser_user_data_dir"),
            "window_width": int(get_setting("browser_settings", "window_w", 1280)),
            "window_height": int(get_setting("browser_settings", "window_h", 1100)),
        }

        # --- 4. Initialize or Get Agent ---
        if not webui_manager.dr_agent:
            webui_manager.dr_agent = DeepResearchAgent(
                llm=llm,
                browser_config=browser_config_dict,
                mcp_server_config=mcp_config
            )
            logger.info("DeepResearchAgent initialized.")

        # --- 5. Start Agent Run ---
        agent_run_coro = webui_manager.dr_agent.run(
            topic=task_topic,
            task_id=task_id_to_resume,
            save_dir=base_save_dir,
            max_parallel_browsers=max_parallel_agents
        )
        agent_task = asyncio.create_task(agent_run_coro)
        webui_manager.dr_current_task = agent_task

        await asyncio.sleep(1.0)

        running_task_id = webui_manager.dr_agent.current_task_id
        if not running_task_id:
            running_task_id = task_id_to_resume
            if not running_task_id:
                logger.warning("Could not determine running task ID immediately.")
            else:
                logger.info(f"Assuming task ID based on resume ID: {running_task_id}")
        else:
            logger.info(f"Agent started with Task ID: {running_task_id}")

        webui_manager.dr_task_id = running_task_id

        if running_task_id:
            task_specific_dir = os.path.join(base_save_dir, str(running_task_id))
            plan_file_path = os.path.join(task_specific_dir, "research_plan.md")
            report_file_path = os.path.join(task_specific_dir, "report.md")
            logger.info(f"Monitoring plan file: {plan_file_path}")
        else:
            logger.warning("Cannot monitor plan file: Task ID unknown.")
            plan_file_path = None
        last_plan_content = None
        while not agent_task.done():
            update_dict = {}
            update_dict[resume_task_id_comp] = gr.update(value=running_task_id)
            agent_stopped = getattr(webui_manager.dr_agent, 'stopped', False)
            if agent_stopped:
                logger.info("Stop signal detected from agent state.")
                break

            if plan_file_path:
                try:
                    current_mtime = os.path.getmtime(plan_file_path) if os.path.exists(plan_file_path) else 0
                    if current_mtime > last_plan_mtime:
                        logger.info(f"Detected change in {plan_file_path}")
                        plan_content = _read_file_safe(plan_file_path)
                        if last_plan_content is None or (
                                plan_content is not None and plan_content != last_plan_content):
                            update_dict[markdown_display_comp] = gr.update(value=plan_content)
                            last_plan_content = plan_content
                            last_plan_mtime = current_mtime
                        elif plan_content is None:
                            last_plan_mtime = 0
                except Exception as e:
                    logger.warning(f"Error checking/reading plan file {plan_file_path}: {e}")
                    await asyncio.sleep(2.0)

            if update_dict:
                yield update_dict

            await asyncio.sleep(1.0)

        logger.info("Agent task processing finished. Awaiting final result...")
        final_result_dict = await agent_task
        logger.info(f"Agent run completed. Result keys: {final_result_dict.keys() if final_result_dict else 'None'}")

        if not running_task_id and final_result_dict and 'task_id' in final_result_dict:
            running_task_id = final_result_dict['task_id']
            webui_manager.dr_task_id = running_task_id
            task_specific_dir = os.path.join(base_save_dir, str(running_task_id))
            report_file_path = os.path.join(task_specific_dir, "report.md")
            logger.info(f"Task ID confirmed from result: {running_task_id}")

        final_ui_update = {}
        if report_file_path and os.path.exists(report_file_path):
            logger.info(f"Loading final report from: {report_file_path}")
            report_content = _read_file_safe(report_file_path)
            if report_content:
                final_ui_update[markdown_display_comp] = gr.update(value=report_content)
                final_ui_update[markdown_download_comp] = gr.File(value=report_file_path,
                                                                  label=f"Report ({running_task_id}.md)",
                                                                  interactive=True)
            else:
                final_ui_update[markdown_display_comp] = gr.update(
                    value="# Research Complete\n\n*Error reading final report file.*")
        elif final_result_dict and 'report' in final_result_dict:
            logger.info("Using report content directly from agent result.")
            final_ui_update[markdown_display_comp] = gr.update(value=final_result_dict['report'])
            final_ui_update[markdown_download_comp] = gr.update(value=None, label="Download Research Report",
                                                                interactive=False)
        else:
            logger.warning("Final report file not found and not in result dict.")
            final_ui_update[markdown_display_comp] = gr.update(value="# Research Complete\n\n*Final report not found.*")

        yield final_ui_update

    except Exception as e:
        logger.error(f"Error during Deep Research Agent execution: {e}", exc_info=True)
        gr.Error(f"Research failed: {e}")
        yield {markdown_display_comp: gr.update(value=f"# Research Failed\n\n**Error:**\n```\n{e}\n```")}

    finally:
        webui_manager.dr_current_task = None
        webui_manager.dr_task_id = None

        yield {
            start_button_comp: gr.update(value="▶️ Run", interactive=True),
            stop_button_comp: gr.update(interactive=False),
            research_task_comp: gr.update(interactive=True),
            resume_task_id_comp: gr.update(value="", interactive=True),
            parallel_num_comp: gr.update(interactive=True),
            save_dir_comp: gr.update(interactive=True),
            markdown_download_comp: gr.update() if report_file_path and os.path.exists(report_file_path) else gr.update(
                interactive=False)
        }

async def stop_deep_research(webui_manager: WebuiManager) -> Dict[Component, Any]:
    """Handles the Stop button click."""
    logger.info("Stop button clicked for Deep Research.")
    agent = webui_manager.dr_agent
    task = webui_manager.dr_current_task
    task_id = webui_manager.dr_task_id
    base_save_dir = webui_manager.dr_save_dir

    stop_button_comp = webui_manager.get_component_by_id("deep_research_agent.stop_button")
    start_button_comp = webui_manager.get_component_by_id("deep_research_agent.start_button")
    markdown_display_comp = webui_manager.get_component_by_id("deep_research_agent.markdown_display")
    markdown_download_comp = webui_manager.get_component_by_id("deep_research_agent.markdown_download")

    final_update = {
        stop_button_comp: gr.update(interactive=False, value="⏹️ Stopping...")
    }

    if agent and task and not task.done():
        logger.info("Signalling DeepResearchAgent to stop.")
        try:
            await agent.stop()
        except Exception as e:
            logger.error(f"Error calling agent.stop(): {e}")

        await asyncio.sleep(1.5)
        report_file_path = None
        if task_id and base_save_dir:
            report_file_path = os.path.join(base_save_dir, str(task_id), "report.md")

        if report_file_path and os.path.exists(report_file_path):
            report_content = _read_file_safe(report_file_path)
            if report_content:
                final_update[markdown_display_comp] = gr.update(
                    value=report_content + "\n\n---\n*Research stopped by user.*")
                final_update[markdown_download_comp] = gr.File(value=report_file_path, label=f"Report ({task_id}.md)",
                                                               interactive=True)
            else:
                final_update[markdown_display_comp] = gr.update(
                    value="# Research Stopped\n\n*Error reading final report file after stop.*")
        else:
            final_update[markdown_display_comp] = gr.update(value="# Research Stopped by User")

        final_update[start_button_comp] = gr.update(interactive=False)

    else:
        logger.warning("Stop clicked but no active research task found.")
        final_update = {
            start_button_comp: gr.update(interactive=True),
            stop_button_comp: gr.update(interactive=False),
            webui_manager.get_component_by_id("deep_research_agent.research_task"): gr.update(interactive=True),
            webui_manager.get_component_by_id("deep_research_agent.resume_task_id"): gr.update(interactive=True),
            webui_manager.get_component_by_id("deep_research_agent.max_iteration"): gr.update(interactive=True),
            webui_manager.get_component_by_id("deep_research_agent.max_query"): gr.update(interactive=True),
        }

    return final_update

async def update_mcp_server(mcp_file: str, webui_manager: WebuiManager):
    """
    Update the MCP server.
    """
    if hasattr(webui_manager, "dr_agent") and webui_manager.dr_agent:
        logger.warning("⚠️ Close controller because mcp file has changed!")
        await webui_manager.dr_agent.close_mcp_client()

    if not mcp_file or not os.path.exists(mcp_file) or not mcp_file.endswith('.json'):
        logger.warning(f"{mcp_file} is not a valid MCP file.")
        return None, gr.update(visible=False)

    with open(mcp_file, 'r') as f:
        mcp_server = json.load(f)

    return json.dumps(mcp_server, indent=2), gr.update(visible=True)

def create_deep_research_agent_tab(webui_manager: WebuiManager):
    """
    Creates a deep research agent tab
    """
    input_components = set(webui_manager.get_components())
    tab_components = {}

    with gr.Group():
        with gr.Row():
            mcp_json_file = gr.File(label="MCP server json", interactive=True, file_types=[".json"])
            mcp_server_config = gr.Textbox(label="MCP server", lines=6, interactive=True, visible=False)

    with gr.Group():
        research_task = gr.Textbox(label="Research Task", lines=5,
                                   value="Give me a detailed travel plan to Switzerland from June 1st to 10th.",
                                   interactive=True)
        with gr.Row():
            resume_task_id = gr.Textbox(label="Resume Task ID", value="",
                                        interactive=True)
            parallel_num = gr.Number(label="Parallel Agent Num", value=1,
                                     precision=0,
                                     interactive=True)
            max_query = gr.Textbox(label="Research Save Dir", value="./tmp/deep_research",
                                   interactive=True)
    with gr.Row():
        stop_button = gr.Button("⏹️ Stop", variant="stop", scale=2)
        start_button = gr.Button("▶️ Run", variant="primary", scale=3)
    with gr.Group():
        markdown_display = gr.Markdown(label="Research Report")
        markdown_download = gr.File(label="Download Research Report", interactive=False)
    tab_components.update(
        dict(
            research_task=research_task,
            parallel_num=parallel_num,
            max_query=max_query,
            start_button=start_button,
            stop_button=stop_button,
            markdown_display=markdown_display,
            markdown_download=markdown_download,
            resume_task_id=resume_task_id,
            mcp_json_file=mcp_json_file,
            mcp_server_config=mcp_server_config,
        )
    )
    webui_manager.add_components("deep_research_agent", tab_components)
    webui_manager.init_deep_research_agent()

    async def update_wrapper(mcp_file):
        update_dict = await update_mcp_server(mcp_file, webui_manager)
        yield update_dict

    mcp_json_file.change(
        update_wrapper,
        inputs=[mcp_json_file],
        outputs=[mcp_server_config, mcp_server_config]
    )

    dr_tab_outputs = list(tab_components.values())
    all_managed_inputs = set(webui_manager.get_components())

    async def start_wrapper(comps: Dict[Component, Any]) -> AsyncGenerator[Dict[Component, Any], None]:
        async for update in run_deep_research(webui_manager, comps):
            yield update

    async def stop_wrapper() -> AsyncGenerator[Dict[Component, Any], None]:
        update_dict = await stop_deep_research(webui_manager)
        yield update_dict

    start_button.click(
        fn=start_wrapper,
        inputs=all_managed_inputs,
        outputs=dr_tab_outputs
    )

    stop_button.click(
        fn=stop_wrapper,
        inputs=None,
        outputs=dr_tab_outputs
    )
