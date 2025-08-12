import os
import json
import logging
import asyncio
import subprocess
import time
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)

class BrowserConnector:
    """Connects to existing browser sessions for automation"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self._chrome_process = None  # Track Chrome process
        self._is_connected = False   # Track connection status
        
    async def connect_to_existing_chrome(self, chrome_path: str, user_data_dir: str) -> bool:
        """Connect to existing Chrome browser session - only launches once"""
        try:
            # If already connected, return success
            if self._is_connected and self.browser:
                logger.info("✅ Already connected to Chrome browser")
                return True
                
            logger.info("🔗 Attempting to connect to existing Chrome browser...")
            
            # Start Chrome with remote debugging if not already running
            await self._ensure_chrome_debugging(chrome_path, user_data_dir)
            
            # Connect to Chrome via CDP
            self.playwright = await async_playwright().start()
            
            # Try to connect to existing Chrome instance
            self.browser = await self.playwright.chromium.connect_over_cdp("http://localhost:9222")
            
            if self.browser:
                self._is_connected = True
                logger.info("✅ Successfully connected to existing Chrome browser")
                return True
            else:
                logger.warning("⚠️ Could not connect to existing Chrome, will launch new instance")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error connecting to existing Chrome: {e}")
            return False
    
    async def _ensure_chrome_debugging(self, chrome_path: str, user_data_dir: str):
        """Ensure Chrome is running with remote debugging enabled - only launches once"""
        try:
            # Check if Chrome is already running with debugging
            if await self._is_chrome_debugging_running():
                logger.info("✅ Chrome with debugging already running")
                return
            
            # Check if we already launched Chrome
            if self._chrome_process and self._chrome_process.poll() is None:
                logger.info("✅ Chrome already launched by this connector")
                return
            
            # Launch Chrome with remote debugging
            logger.info("🚀 Launching Chrome with remote debugging...")
            
            cmd = [
                chrome_path,
                "--remote-debugging-port=9222",
                "--user-data-dir=" + user_data_dir,
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-default-apps",
                "--disable-popup-blocking",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-features=TranslateUI",
                "--disable-ipc-flooding-protection"
            ]
            
            # Launch Chrome in background and track the process
            self._chrome_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Wait for Chrome to start
            await asyncio.sleep(3)
            
            # Wait for debugging port to be available
            max_attempts = 10
            for attempt in range(max_attempts):
                if await self._is_chrome_debugging_running():
                    logger.info("✅ Chrome with debugging started successfully")
                    return
                await asyncio.sleep(1)
            
            logger.warning("⚠️ Chrome debugging port not available after timeout")
            
        except Exception as e:
            logger.error(f"❌ Error launching Chrome with debugging: {e}")
    
    async def _is_chrome_debugging_running(self) -> bool:
        """Check if Chrome is running with remote debugging"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:9222/json/version", timeout=2) as response:
                    return response.status == 200
        except:
            return False
    
    async def get_or_create_context(self) -> BrowserContext:
        """Get existing context or create new one"""
        if not self.browser:
            raise Exception("Browser not connected")
        
        # Try to get existing context
        contexts = self.browser.contexts
        if contexts:
            self.context = contexts[0]
            logger.info("✅ Using existing browser context")
        else:
            # Create new context
            self.context = await self.browser.new_context()
            logger.info("✅ Created new browser context")
        
        return self.context
    
    async def get_or_create_page(self) -> Page:
        """Get existing page or create new one"""
        if not self.context:
            await self.get_or_create_context()
        
        # Try to get existing page
        pages = self.context.pages
        if pages:
            self.page = pages[0]
            logger.info("✅ Using existing browser page")
        else:
            # Create new page
            self.page = await self.context.new_page()
            logger.info("✅ Created new browser page")
        
        return self.page
    
    async def execute_task(self, task: str) -> Dict[str, Any]:
        """Execute automation task in the connected browser"""
        try:
            page = await self.get_or_create_page()
            
            logger.info(f"🎯 Executing task: {task}")
            
            # Simple task execution - can be enhanced with LLM
            if "open google" in task.lower():
                await page.goto("https://www.google.com")
                return {
                    "success": True,
                    "message": "Opened Google successfully",
                    "url": await page.url(),
                    "title": await page.title()
                }
            elif "open youtube" in task.lower():
                await page.goto("https://www.youtube.com")
                return {
                    "success": True,
                    "message": "Opened YouTube successfully",
                    "url": await page.url(),
                    "title": await page.title()
                }
            elif "search" in task.lower():
                # Extract search query
                search_query = task.lower().replace("search", "").strip()
                await page.goto(f"https://www.google.com/search?q={search_query}")
                return {
                    "success": True,
                    "message": f"Searched for: {search_query}",
                    "url": await page.url(),
                    "title": await page.title()
                }
            else:
                # Default: try to navigate to the task as URL
                if task.startswith("http"):
                    await page.goto(task)
                else:
                    await page.goto(f"https://www.google.com/search?q={task}")
                
                return {
                    "success": True,
                    "message": f"Navigated to: {task}",
                    "url": await page.url(),
                    "title": await page.title()
                }
                
        except Exception as e:
            logger.error(f"❌ Error executing task: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    async def close(self):
        """Close browser connection but leave Chrome running for user to close manually"""
        try:
            if self.playwright:
                await self.playwright.stop()
                self._is_connected = False
                logger.info("✅ Browser connection closed (Chrome left running for user)")
        except Exception as e:
            logger.error(f"❌ Error closing browser connection: {e}")
    
    def force_close_chrome(self):
        """Force close Chrome process (use only when user wants to close browser)"""
        try:
            if self._chrome_process and self._chrome_process.poll() is None:
                self._chrome_process.terminate()
                logger.info("✅ Chrome process terminated")
        except Exception as e:
            logger.error(f"❌ Error terminating Chrome process: {e}")

# Global instance
browser_connector = BrowserConnector() 