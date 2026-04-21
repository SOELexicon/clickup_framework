"""
Chrome Session Token Extractor

Utility to extract ClickUp session tokens from Chrome browser cookies/localStorage.
This allows using the web interface's v1 API endpoints that require session authentication.
"""

import os
import json
import sqlite3
import platform
from pathlib import Path
from typing import Optional, Dict, Any
import base64


def get_chrome_profile_path() -> Optional[Path]:
    """
    Get the default Chrome profile path based on the operating system.
    
    Returns:
        Path to Chrome profile directory, or None if not found
    """
    system = platform.system()
    
    if system == "Windows":
        # Windows Chrome profile path
        chrome_path = Path(os.path.expanduser("~")) / "AppData" / "Local" / "Google" / "Chrome" / "User Data"
        if chrome_path.exists():
            return chrome_path
    elif system == "Darwin":  # macOS
        chrome_path = Path(os.path.expanduser("~")) / "Library" / "Application Support" / "Google" / "Chrome"
        if chrome_path.exists():
            return chrome_path
    elif system == "Linux":
        chrome_path = Path(os.path.expanduser("~")) / ".config" / "google-chrome"
        if chrome_path.exists():
            return chrome_path
    
    return None


def get_chrome_cookies_db_path(profile: str = "Default") -> Optional[Path]:
    """
    Get the path to Chrome's cookies database.
    
    Args:
        profile: Chrome profile name (default: "Default")
    
    Returns:
        Path to cookies database, or None if not found
    """
    chrome_path = get_chrome_profile_path()
    if not chrome_path:
        return None
    
    cookies_path = chrome_path / profile / "Cookies"
    if cookies_path.exists():
        return cookies_path
    
    return None


def extract_clickup_session_token(profile: str = "Default") -> Optional[Dict[str, Any]]:
    """
    Extract ClickUp session token from Chrome cookies.
    
    Note: On Windows, Chrome encrypts cookies using Windows Data Protection API (DPAPI),
    so automatic extraction may not work. Manual extraction is recommended.
    
    The session token is stored in Chrome's cookies database. We need to:
    1. Find the cookies database
    2. Query for ClickUp cookies (app.clickup.com)
    3. Extract the session token and related authentication data
    
    Args:
        profile: Chrome profile name (default: "Default")
    
    Returns:
        Dictionary with session token info, or None if not found
        Format: {
            'session_token': 'JWT token',
            'sessionid': 'session ID',
            'workspace_id': 'workspace ID if available'
        }
    """
    cookies_path = get_chrome_cookies_db_path(profile)
    if not cookies_path:
        return None
    
    try:
        # Chrome locks the database when running, so we need to copy it first
        import tempfile
        import shutil
        
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        try:
            # Try to copy the database (will fail if Chrome is running)
            shutil.copy2(cookies_path, temp_db.name)
            
            conn = sqlite3.connect(temp_db.name)
            cursor = conn.cursor()
            
            # Query for ClickUp cookies
            # Look for cookies from app.clickup.com or clickup.com
            cursor.execute("""
                SELECT name, value, host_key, expires_utc
                FROM cookies
                WHERE host_key LIKE '%clickup.com%'
                AND (name LIKE '%session%' OR name LIKE '%token%' OR name LIKE '%auth%')
            """)
            
            cookies = cursor.fetchall()
            conn.close()
            
            # Parse cookies to find session token
            session_data = {}
            
            for name, value, host_key, expires_utc in cookies:
                name_lower = name.lower()
                # JWT tokens start with "eyJ" (base64 encoded JSON header)
                if value and isinstance(value, str) and value.startswith('eyJ'):
                    session_data['session_token'] = value
                elif 'session' in name_lower and value:
                    session_data['sessionid'] = value
            
            if session_data.get('session_token'):
                return session_data
            
        except PermissionError:
            # Chrome is likely running and has the database locked
            raise Exception(
                "Chrome is currently running. Please close Chrome and try again, "
                "or use manual extraction (cum extract_session_token --manual)"
            )
        except sqlite3.OperationalError as e:
            if "encrypted" in str(e).lower() or "unable to open" in str(e).lower():
                raise Exception(
                    "Chrome cookies are encrypted (Windows DPAPI). "
                    "Please use manual extraction (cum extract_session_token --manual)"
                )
            raise
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_db.name)
            except Exception:
                pass
                
    except Exception as e:
        # Re-raise with context
        if isinstance(e, Exception) and not isinstance(e, (PermissionError, sqlite3.OperationalError)):
            raise Exception(f"Failed to extract session token: {e}")
        raise
    
    return None


def extract_from_local_storage(profile: str = "Default") -> Optional[Dict[str, Any]]:
    """
    Extract session token from Chrome's Local Storage.
    
    Note: This is more complex and may require parsing Chrome's Local Storage files.
    For now, we'll focus on cookies as they're easier to access.
    
    Args:
        profile: Chrome profile name (default: "Default")
    
    Returns:
        Dictionary with session token info, or None if not found
    """
    # TODO: Implement Local Storage extraction if needed
    # Chrome stores Local Storage in: Profile/Default/Local Storage/leveldb/
    # This requires parsing LevelDB files which is more complex
    return None


def get_clickup_session_token(profile: str = "Default") -> Optional[str]:
    """
    Get ClickUp session token from Chrome.
    
    This is a convenience function that tries multiple methods to extract the token.
    
    Args:
        profile: Chrome profile name (default: "Default")
    
    Returns:
        Session token (JWT) as string, or None if not found
    """
    session_data = extract_clickup_session_token(profile)
    if session_data:
        return session_data.get('session_token')
    return None


def extract_from_network_request() -> str:
    """
    Get instructions for manual extraction from browser network requests.
    
    Returns:
        Instructions for manual extraction
    """
    return """
To extract your ClickUp session token manually from Chrome:

Method 1: From Network Tab (Easiest)
1. Open ClickUp in Chrome (app.clickup.com)
2. Open Chrome DevTools (F12 or Right-click > Inspect)
3. Go to the "Network" tab
4. Refresh the page or perform any action in ClickUp
5. Find any request to clickup.com (e.g., to "frontdoor-prod-eu-west-1-3.clickup.com")
6. Click on the request
7. In the "Headers" section, scroll to "Request Headers"
8. Find the "authorization" header
9. Copy the entire value (it starts with "Bearer " followed by a long JWT token)
10. Remove the "Bearer " prefix if present
11. Use: cum set_current session_token <token>

Method 2: From Application Tab
1. Open ClickUp in Chrome
2. Open Chrome DevTools (F12)
3. Go to the "Application" tab
4. In the left sidebar, expand "Cookies" > "https://app.clickup.com"
5. Look for cookies with names containing "session" or "token"
6. Copy the value (should be a JWT starting with "eyJ")
7. Use: cum set_current session_token <token>

Method 3: Copy from Fetch Request
If you see a fetch() request in the console or network tab:
1. Copy the entire authorization header value
2. Remove "Bearer " prefix if present
3. Use: cum set_current session_token <token>

Note: Session tokens expire, so you may need to extract a new one periodically.
"""

