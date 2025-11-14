"""
Auth API - Low-level API for ClickUp authentication endpoints.
"""

from typing import Dict, Any
from .base import BaseAPI


class AuthAPI(BaseAPI):
    """Low-level API for authentication operations."""

    def get_access_token(self, client_id: str, client_secret: str, code: str) -> Dict[str, Any]:
        """
        Get OAuth access token.

        Args:
            client_id: OAuth app client ID
            client_secret: OAuth app client secret
            code: Authorization code from OAuth flow

        Returns:
            Access token response with access_token field
        """
        return self._request("POST", "oauth/token", json={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code
        })

    def get_authorized_user(self) -> Dict[str, Any]:
        """
        Get currently authenticated user info.

        Returns:
            User object with id, username, email, etc.
        """
        return self._request("GET", "user")

