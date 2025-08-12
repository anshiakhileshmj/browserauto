import os
import json
import logging
from typing import Dict, Optional
from .chrome_detector import ChromeDetector

logger = logging.getLogger(__name__)

class AutoConfig:
    """Automatically configure Chrome settings on project startup"""
    
    CONFIG_FILE = "chrome_auto_config.json"
    
    @staticmethod
    def auto_detect_and_configure() -> Dict[str, str]:
        """Automatically detect Chrome and configure settings without launching it"""
        config = {}
        
        try:
            # Detect Chrome path
            chrome_path = ChromeDetector.get_best_chrome_path()
            if chrome_path:
                config['BROWSER_PATH'] = chrome_path
                logger.info(f"Auto-detected Chrome path: {chrome_path}")
                
                # Only do basic verification without launching Chrome
                if ChromeDetector.test_chrome_basic(chrome_path):
                    config['USE_OWN_BROWSER'] = 'true'
                    logger.info("Chrome executable verified - will use local browser")
                else:
                    config['USE_OWN_BROWSER'] = 'false'
                    logger.warning("Chrome executable not accessible, falling back to Playwright")
            else:
                config['USE_OWN_BROWSER'] = 'false'
                logger.warning("No Chrome installation found, using Playwright")
            
            # Detect Chrome user data directory
            user_data_dir = ChromeDetector.get_chrome_user_data_dir()
            if user_data_dir:
                config['BROWSER_USER_DATA'] = user_data_dir
                logger.info(f"Auto-detected Chrome user data directory: {user_data_dir}")
            
            # Save configuration
            AutoConfig.save_config(config)
            
            return config
            
        except Exception as e:
            logger.error(f"Error in auto-configuration: {e}")
            return {'USE_OWN_BROWSER': 'false'}
    
    @staticmethod
    def save_config(config: Dict[str, str]) -> None:
        """Save configuration to file"""
        try:
            with open(AutoConfig.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Configuration saved to {AutoConfig.CONFIG_FILE}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    @staticmethod
    def load_config() -> Dict[str, str]:
        """Load configuration from file"""
        try:
            if os.path.exists(AutoConfig.CONFIG_FILE):
                with open(AutoConfig.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                logger.info(f"Configuration loaded from {AutoConfig.CONFIG_FILE}")
                return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
        
        return {}
    
    @staticmethod
    def update_env_vars(config: Dict[str, str]) -> None:
        """Update environment variables with configuration"""
        for key, value in config.items():
            if value:  # Only set non-empty values
                os.environ[key] = value
                logger.info(f"Set environment variable {key}={value}")
    
    @staticmethod
    def get_chrome_status() -> Dict[str, any]:
        """Get current Chrome configuration status without launching Chrome"""
        config = AutoConfig.load_config()
        
        status = {
            'chrome_detected': False,
            'chrome_path': None,
            'user_data_dir': None,
            'use_own_browser': False,
            'executable_verified': False
        }
        
        if config.get('BROWSER_PATH'):
            status['chrome_detected'] = True
            status['chrome_path'] = config['BROWSER_PATH']
            
            # Only check if executable exists, don't launch
            if os.path.exists(config['BROWSER_PATH']):
                status['executable_verified'] = ChromeDetector.test_chrome_basic(config['BROWSER_PATH'])
        
        if config.get('BROWSER_USER_DATA'):
            status['user_data_dir'] = config['BROWSER_USER_DATA']
        
        if config.get('USE_OWN_BROWSER') == 'true':
            status['use_own_browser'] = True
        
        return status 