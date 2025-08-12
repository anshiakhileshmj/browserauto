from dotenv import load_dotenv
load_dotenv()
import argparse
import logging
import os
from src.webui.interface import theme_map, create_ui
from src.utils.auto_config import AutoConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Gradio WebUI for Browser Agent")
    parser.add_argument("--ip", type=str, default="127.0.0.1", help="IP address to bind to")
    parser.add_argument("--port", type=int, default=7788, help="Port to listen on")
    parser.add_argument("--theme", type=str, default="Ocean", choices=theme_map.keys(), help="Theme to use for the UI")
    parser.add_argument("--no-auto-config", action="store_true", help="Disable automatic Chrome configuration")
    args = parser.parse_args()

    # Auto-configure Chrome if not disabled
    if not args.no_auto_config:
        logger.info("Starting automatic Chrome configuration...")
        config = AutoConfig.auto_detect_and_configure()
        AutoConfig.update_env_vars(config)
        
        # Verify environment variables are set
        logger.info("Verifying environment variables:")
        logger.info(f"   BROWSER_PATH: {os.getenv('BROWSER_PATH', 'Not set')}")
        logger.info(f"   USE_OWN_BROWSER: {os.getenv('USE_OWN_BROWSER', 'Not set')}")
        logger.info(f"   BROWSER_USER_DATA: {os.getenv('BROWSER_USER_DATA', 'Not set')}")
        
        # Log configuration status
        status = AutoConfig.get_chrome_status()
        if status['chrome_detected']:
            logger.info(f"✅ Chrome detected at: {status['chrome_path']}")
            if status['use_own_browser']:
                logger.info("✅ Using local Chrome browser for automation")
            else:
                logger.info("⚠️ Using Playwright browser (Chrome connection failed)")
        else:
            logger.info("⚠️ No Chrome detected, using Playwright browser")
    else:
        logger.info("Auto-configuration disabled")

    demo = create_ui(theme_name=args.theme)
    demo.queue().launch(server_name=args.ip, server_port=args.port)


if __name__ == '__main__':
    main()
