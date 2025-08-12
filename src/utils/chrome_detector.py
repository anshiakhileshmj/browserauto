import os
import winreg
import subprocess
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class ChromeDetector:
    """Utility to automatically detect Chrome installation paths on Windows"""
    
    @staticmethod
    def get_chrome_paths() -> List[str]:
        """Get all possible Chrome installation paths"""
        paths = []
        
        # Common Chrome installation paths
        common_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME', '')),
            r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USER', '')),
        ]
        
        # Check common paths
        for path in common_paths:
            if os.path.exists(path):
                paths.append(path)
                logger.info(f"Found Chrome at: {path}")
        
        # Try to find Chrome via registry
        registry_paths = ChromeDetector._get_chrome_from_registry()
        for path in registry_paths:
            if path not in paths and os.path.exists(path):
                paths.append(path)
                logger.info(f"Found Chrome via registry at: {path}")
        
        # Try to find Chrome via where command
        where_paths = ChromeDetector._get_chrome_via_where()
        for path in where_paths:
            if path not in paths and os.path.exists(path):
                paths.append(path)
                logger.info(f"Found Chrome via where command at: {path}")
        
        return paths
    
    @staticmethod
    def _get_chrome_from_registry() -> List[str]:
        """Get Chrome path from Windows registry"""
        paths = []
        try:
            # Try different registry keys
            registry_keys = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
            ]
            
            for hkey, subkey in registry_keys:
                try:
                    with winreg.OpenKey(hkey, subkey) as key:
                        path, _ = winreg.QueryValueEx(key, "")
                        if path and os.path.exists(path):
                            paths.append(path)
                except (FileNotFoundError, OSError):
                    continue
                    
        except Exception as e:
            logger.warning(f"Error reading Chrome from registry: {e}")
        
        return paths
    
    @staticmethod
    def _get_chrome_via_where() -> List[str]:
        """Get Chrome path using 'where' command"""
        paths = []
        try:
            result = subprocess.run(['where', 'chrome'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    path = line.strip()
                    if path and os.path.exists(path):
                        paths.append(path)
        except Exception as e:
            logger.warning(f"Error finding Chrome via where command: {e}")
        
        return paths
    
    @staticmethod
    def get_best_chrome_path() -> Optional[str]:
        """Get the best Chrome path (prefer Program Files over AppData)"""
        paths = ChromeDetector.get_chrome_paths()
        
        if not paths:
            logger.warning("No Chrome installation found")
            return None
        
        # Prefer Program Files over AppData
        for path in paths:
            if "Program Files" in path:
                logger.info(f"Selected Chrome from Program Files: {path}")
                return path
        
        # Fallback to first available path
        logger.info(f"Selected Chrome: {paths[0]}")
        return paths[0]
    
    @staticmethod
    def get_chrome_user_data_dir() -> Optional[str]:
        """Get Chrome user data directory"""
        username = os.getenv('USERNAME') or os.getenv('USER', '')
        if not username:
            return None
        
        user_data_dir = os.path.join(os.getenv('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data')
        if os.path.exists(user_data_dir):
            logger.info(f"Found Chrome user data directory: {user_data_dir}")
            return user_data_dir
        
        logger.warning("Chrome user data directory not found")
        return None
    
    @staticmethod
    def test_chrome_basic(chrome_path: str) -> bool:
        """Basic test to check if Chrome executable exists without launching it"""
        try:
            # Only check if the executable exists and is accessible
            if os.path.exists(chrome_path) and os.access(chrome_path, os.X_OK):
                logger.info(f"Chrome executable verified: {chrome_path}")
                return True
            else:
                logger.warning(f"Chrome executable not accessible: {chrome_path}")
                return False
        except Exception as e:
            logger.error(f"Error in Chrome basic test: {e}")
            return False 