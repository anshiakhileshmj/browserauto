#!/usr/bin/env python3
"""
Test script for browser connector functionality
"""

import asyncio
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
sys.path.append('.')

from src.utils.browser_connector import browser_connector
from src.utils.auto_config import AutoConfig

async def test_browser_connector():
    """Test the browser connector functionality"""
    print("🔗 Testing Browser Connector")
    print("=" * 50)
    
    # Load auto-configuration
    config = AutoConfig.load_config()
    chrome_path = config.get("BROWSER_PATH")
    user_data_dir = config.get("BROWSER_USER_DATA")
    
    print(f"Chrome path: {chrome_path}")
    print(f"User data dir: {user_data_dir}")
    
    if not chrome_path or not user_data_dir:
        print("❌ Chrome not configured")
        return False
    
    try:
        # Test connection
        print("\n1. 🔗 Connecting to existing browser...")
        connected = await browser_connector.connect_to_existing_chrome(chrome_path, user_data_dir)
        
        if not connected:
            print("❌ Could not connect to browser")
            return False
        
        print("✅ Connected to browser successfully")
        
        # Test task execution
        print("\n2. 🎯 Testing task execution...")
        test_tasks = [
            "open google",
            "open youtube",
            "search python programming"
        ]
        
        for task in test_tasks:
            print(f"\n   Testing: {task}")
            result = await browser_connector.execute_task(task)
            
            if result["success"]:
                print(f"   ✅ Success: {result['message']}")
                print(f"   📍 URL: {result.get('url', 'N/A')}")
                print(f"   📄 Title: {result.get('title', 'N/A')}")
            else:
                print(f"   ❌ Failed: {result['message']}")
        
        # Clean up
        print("\n3. 🧹 Cleaning up...")
        await browser_connector.close()
        
        print("\n" + "=" * 50)
        print("✅ Browser connector test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_browser_connector())
    sys.exit(0 if success else 1) 