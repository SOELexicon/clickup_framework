"""
Base API class for all ClickUp API classes.

Provides common functionality and request delegation.
"""

from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import ClickUpClient


class BaseAPI:
    """
    Base class for all ClickUp API classes.
    
    Provides the _request method that delegates to the client's _request method.
    """

    def __init__(self, client: "ClickUpClient"):
        """
        Initialize the API class.
        
        Args:
            client: ClickUpClient instance to delegate requests to
        """
        self.client = client

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Dict[str, Any] = None,
        json: Dict[str, Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make an API request through the client.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            json: JSON body
            **kwargs: Additional arguments for requests
            
        Returns:
            API response as dictionary
        """
        return self.client._request(method, endpoint, params=params, json=json, **kwargs)

