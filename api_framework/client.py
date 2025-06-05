"""HTTP client module for making API requests."""
import time
from typing import Any, Dict, Optional, Union
import requests
from requests.exceptions import RequestException

from .config import Config
from .logger import APILogger

class APIClient:
    """HTTP client for making API requests with logging and error handling."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize API client with configuration.
        
        Args:
            config: Configuration instance. If None, uses default config.
        """
        self.config = config or Config()
        self.logger = APILogger(self.config.get("log_file"))
        self.session = requests.Session()
        self._setup_auth()
        
    def _setup_auth(self) -> None:
        """Configure authentication based on config."""
        auth_config = self.config.get("auth", {})
        auth_type = auth_config.get("type")
        
        if auth_type == "basic":
            self.session.auth = (
                auth_config.get("username"),
                auth_config.get("password")
            )
        elif auth_type == "bearer":
            self.session.headers["Authorization"] = f"Bearer {auth_config.get('token')}"
            
    def _make_request(
        self,
        method: str,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> requests.Response:
        """
        Make HTTP request with retry logic and logging.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (will be joined with base_url)
            headers: Additional request headers
            params: Query parameters
            json_data: JSON request body
            data: Form data
            retry_count: Current retry attempt number
            
        Returns:
            Response object
            
        Raises:
            RequestException: If request fails after all retries
        """
        url = f"{self.config.get('base_url')}{endpoint}"
        request_headers = self.session.headers.copy()
        if headers:
            request_headers.update(headers)
            
        # Log request
        timestamp = self.logger.log_request(
            method,
            url,
            request_headers,
            json_data or data
        )
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=request_headers,
                params=params,
                json=json_data,
                data=data,
                timeout=self.config.get("timeout", 30)
            )
            
            # Log response
            self.logger.log_response(
                response.status_code,
                dict(response.headers),
                response.json() if response.content else None,
                timestamp
            )
            
            return response
            
        except RequestException as e:
            if retry_count < self.config.get("retry_attempts", 3):
                time.sleep(self.config.get("retry_delay", 1))
                return self._make_request(
                    method,
                    endpoint,
                    headers,
                    params,
                    json_data,
                    data,
                    retry_count + 1
                )
            raise
            
    def request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any
    ) -> requests.Response:
        """
        Make an HTTP request.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional arguments passed to requests
            
        Returns:
            Response object
        """
        return self._make_request(method, endpoint, **kwargs)
        
    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> requests.Response:
        """Send GET request."""
        return self.request("GET", endpoint, params=params, **kwargs)
        
    def post(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> requests.Response:
        """Send POST request."""
        return self.request("POST", endpoint, json=json_data, data=data, **kwargs)
        
    def put(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> requests.Response:
        """Send PUT request."""
        return self.request("PUT", endpoint, json=json_data, **kwargs)
        
    def patch(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> requests.Response:
        """Send PATCH request."""
        return self.request("PATCH", endpoint, json=json_data, **kwargs)
        
    def delete(
        self,
        endpoint: str,
        **kwargs: Any
    ) -> requests.Response:
        """Send DELETE request."""
        return self.request("DELETE", endpoint, **kwargs)