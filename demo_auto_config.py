#!/usr/bin/env python3
"""
Demonstration script showing auto-configuration with browser automation
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
sys.path.append('.')

from src.utils.auto_config import AutoConfig
from src.utils.chrome_detector import ChromeDetector
from src.browser.custom_browser import CustomBrowser
from src.browser.custom_context import CustomBrowserContext
from browser_use.browser.browser import BrowserConfig
from browser_use.browser.context import BrowserContextConfig

async def demo_auto_configuration():
    """Demonstrate auto-configuration with browser automation"""
    print("🚀 Auto-Configuration Demo")
    print("=" * 50)
    
    # Step 1: Auto-configure Chrome
    print("\n1. 🔍 Auto-detecting Chrome...")
    config = AutoConfig.auto_detect_and_configure()
    AutoConfig.update_env_vars(config)
    
    print(f"   ✅ Chrome path: {config.get('BROWSER_PATH', 'Not found')}")
    print(f"   ✅ Use own browser: {config.get('USE_OWN_BROWSER', 'false')}")
    print(f"   ✅ User data directory: {config.get('BROWSER_USER_DATA', 'Not found')}")
    
    # Step 2: Create browser instance
    print("\n2. 🌐 Creating browser instance...")
    
    browser_binary_path = os.getenv("BROWSER_PATH")
    browser_user_data = os.getenv("BROWSER_USER_DATA")
    use_own_browser = os.getenv("USE_OWN_BROWSER", "false").lower() == "true"
    
    extra_args = []
    if use_own_browser and browser_binary_path:
        if browser_user_data:
            extra_args.append(f"--user-data-dir={browser_user_data}")
        print(f"   ✅ Using local Chrome: {browser_binary_path}")
    else:
        browser_binary_path = None
        print("   📱 Using Playwright browser")
    
    # Create browser
    browser = CustomBrowser(
        config=BrowserConfig(
            headless=False,  # Show the browser window
            browser_binary_path=browser_binary_path,
            extra_browser_args=extra_args,
            new_context_config=BrowserContextConfig(
                window_width=1280,
                window_height=1100,
            )
        )
    )
    
    # Step 3: Create browser context
    print("\n3. 📱 Creating browser context...")
    browser_context = await browser.new_context(
        config=BrowserContextConfig(
            window_width=1280,
            window_height=1100,
        )
    )
    
    # Step 4: Navigate to a website
    print("\n4. 🌍 Navigating to Google...")
    page = await browser_context.new_page()
    await page.goto("https://www.google.com")
    
    print("   ✅ Successfully navigated to Google!")
    print("   📍 Current URL:", await page.url())
    print("   📍 Page title:", await page.title())
    
    # Step 5: Take a screenshot
    print("\n5. 📸 Taking screenshot...")
    screenshot_path = "demo_screenshot.png"
    await page.screenshot(path=screenshot_path)
    print(f"   ✅ Screenshot saved to: {screenshot_path}")
    
    # Step 6: Clean up
    print("\n6. 🧹 Cleaning up...")
    await browser_context.close()
    await browser.close()
    
    print("\n" + "=" * 50)
    print("✅ Demo completed successfully!")
    print("🎉 Your local Chrome browser was used for automation!")
    print(f"📸 Check the screenshot: {screenshot_path}")

if __name__ == "__main__":
    asyncio.run(demo_auto_configuration()) 