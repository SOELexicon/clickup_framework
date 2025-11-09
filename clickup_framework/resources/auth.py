"""
AuthAPI - High-level API for ClickUp authentication and authorization

Provides convenient methods for OAuth and user authentication operations.
"""

from typing import Dict, Any


class AuthAPI:
    """
    High-level API for ClickUp authentication and authorization.

    Wraps ClickUpClient methods for OAuth token exchange and user info.

    Usage:
        from clickup_framework import ClickUpClient
        from clickup_framework.resources import AuthAPI

        client = ClickUpClient()
        auth = AuthAPI(client)

        # Exchange OAuth code for access token
        token = auth.get_access_token(client_id, client_secret, code)

        # Get current user info
        user = auth.get_user()
    """

    def __init__(self, client):
        """
        Initialize AuthAPI.

        Args:
            client: ClickUpClient instance
        """
        self.client = client

    def get_access_token(self, client_id: str, client_secret: str, code: str) -> Dict[str, Any]:
        """
        Exchange OAuth authorization code for access token.

        Args:
            client_id: OAuth app client ID
            client_secret: OAuth app client secret
            code: Authorization code from OAuth flow

        Returns:
            Token response with access_token field (raw dict)

        Example:
            # After user authorizes your app and you receive the code
            token_data = auth.get_access_token(
                client_id="YOUR_CLIENT_ID",
                client_secret="YOUR_CLIENT_SECRET",
                code="authorization_code_from_redirect"
            )
            access_token = token_data['access_token']
        """
        return self.client.get_access_token(client_id, client_secret, code)

    def get_user(self) -> Dict[str, Any]:
        """
        Get currently authenticated user information.

        Returns:
            User object with id, username, email, etc. (raw dict)

        Example:
            user = auth.get_user()
            print(f"Logged in as: {user['username']} ({user['email']})")
        """
        return self.client.get_authorized_user()
