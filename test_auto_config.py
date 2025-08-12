#!/usr/bin/env python3
"""
Test script to verify auto-configuration is working
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
sys.path.append('.')

from src.utils.auto_config import AutoConfig
from src.utils.chrome_detector import ChromeDetector

def test_auto_configuration():
    """Test the auto-configuration system"""
    print("🔍 Testing Auto-Configuration System")
    print("=" * 50)
    
    # Test Chrome detection
    print("\n1. Testing Chrome Detection:")
    chrome_paths = ChromeDetector.get_chrome_paths()
    print(f"   Found Chrome paths: {chrome_paths}")
    
    best_path = ChromeDetector.get_best_chrome_path()
    print(f"   Best Chrome path: {best_path}")
    
    user_data_dir = ChromeDetector.get_chrome_user_data_dir()
    print(f"   Chrome user data directory: {user_data_dir}")
    
    # Test Chrome basic functionality
    if best_path:
        print(f"\n2. Testing Chrome Basic Functionality:")
        basic_test = ChromeDetector.test_chrome_basic(best_path)
        print(f"   Chrome basic test: {'✅ PASS' if basic_test else '❌ FAIL'}")
    
    # Test auto-configuration
    print(f"\n3. Testing Auto-Configuration:")
    config = AutoConfig.auto_detect_and_configure()
    print(f"   Auto-config result: {config}")
    
    # Test environment variables
    print(f"\n4. Testing Environment Variables:")
    print(f"   BROWSER_PATH: {os.getenv('BROWSER_PATH', 'Not set')}")
    print(f"   USE_OWN_BROWSER: {os.getenv('USE_OWN_BROWSER', 'Not set')}")
    print(f"   BROWSER_USER_DATA: {os.getenv('BROWSER_USER_DATA', 'Not set')}")
    
    # Test status
    print(f"\n5. Testing Status:")
    status = AutoConfig.get_chrome_status()
    print(f"   Chrome detected: {status['chrome_detected']}")
    print(f"   Chrome path: {status['chrome_path']}")
    print(f"   User data dir: {status['user_data_dir']}")
    print(f"   Use own browser: {status['use_own_browser']}")
    print(f"   Connection tested: {status['connection_tested']}")
    
    print("\n" + "=" * 50)
    if status['use_own_browser']:
        print("✅ Auto-configuration is working! Your local Chrome will be used for automation.")
    else:
        print("⚠️ Auto-configuration failed. Playwright browser will be used instead.")
    
    return status['use_own_browser']

if __name__ == "__main__":
    success = test_auto_configuration()
    sys.exit(0 if success else 1) 