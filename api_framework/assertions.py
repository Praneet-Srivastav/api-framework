"""Assertion utilities for API testing."""
import functools
import json
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union
import jsonschema
from requests import Response

from .reporting import TestResult, ReportGenerator

# Global report generator instance
_reporter = ReportGenerator()

def get_reporter() -> ReportGenerator:
    """Get the global reporter instance."""
    return _reporter

def validate_status_code(response: Response, expected_code: int) -> None:
    """
    Validate HTTP status code.
    
    Args:
        response: Response object to validate
        expected_code: Expected HTTP status code
        
    Raises:
        AssertionError: If status code doesn't match
    """
    assert response.status_code == expected_code, (
        f"Expected status code {expected_code}, got {response.status_code}"
    )

def validate_json_schema(response: Response, schema: Dict[str, Any]) -> None:
    """
    Validate response JSON against schema.
    
    Args:
        response: Response object to validate
        schema: JSON schema to validate against
        
    Raises:
        AssertionError: If validation fails
    """
    try:
        json_data = response.json()
    except json.JSONDecodeError:
        raise AssertionError("Response is not valid JSON")
        
    try:
        jsonschema.validate(instance=json_data, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        raise AssertionError(f"JSON schema validation failed: {e.message}")

def validate_headers(
    response: Response,
    expected_headers: Dict[str, str]
) -> None:
    """
    Validate response headers.
    
    Args:
        response: Response object to validate
        expected_headers: Dictionary of expected headers
        
    Raises:
        AssertionError: If headers don't match
    """
    for header, value in expected_headers.items():
        assert header in response.headers, f"Header '{header}' not found in response"
        assert response.headers[header] == value, (
            f"Expected header '{header}' to be '{value}', "
            f"got '{response.headers[header]}'"
        )

def validate_json_content(
    response: Response,
    expected_content: Union[Dict[str, Any], List[Any]]
) -> None:
    """
    Validate response JSON content.
    
    Args:
        response: Response object to validate
        expected_content: Expected JSON content
        
    Raises:
        AssertionError: If content doesn't match
    """
    try:
        json_data = response.json()
    except json.JSONDecodeError:
        raise AssertionError("Response is not valid JSON")
        
    assert json_data == expected_content, (
        f"Expected content {expected_content}, got {json_data}"
    )

def api_test(
    endpoint: str,
    method: str = "GET",
    expected_status: int = 200,
    expected_schema: Optional[Dict[str, Any]] = None,
    expected_headers: Optional[Dict[str, str]] = None,
    expected_content: Optional[Union[Dict[str, Any], List[Any]]] = None
) -> Callable:
    """
    Decorator for API test cases.
    
    Args:
        endpoint: API endpoint to test
        method: HTTP method to use
        expected_status: Expected HTTP status code
        expected_schema: Expected JSON schema
        expected_headers: Expected response headers
        expected_content: Expected response content
        
    Returns:
        Decorated test function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args: Any, **kwargs: Any) -> None:
            # Get client from test class
            client = getattr(self, 'client', None)
            if not client:
                raise ValueError("Test class must have 'client' attribute")
                
            # Initialize test result
            test_result = TestResult(
                test_name=func.__name__,
                test_class=self.__class__.__name__,
                status="SUCCESS",
                execution_time=0.0,
                timestamp=datetime.utcnow(),
                endpoint=endpoint,
                method=method
            )
            
            start_time = time.time()
            validation_errors = []
            
            try:
                # Call the test function to get request parameters
                request_params = func(self, *args, **kwargs) or {}
                
                # Make the request
                response = getattr(client, method.lower())(endpoint, **request_params)
                
                # Store response details
                test_result.response_code = response.status_code
                test_result.request_headers = dict(response.request.headers)
                test_result.response_headers = dict(response.headers)
                
                # Perform validations
                try:
                    validate_status_code(response, expected_status)
                except AssertionError as e:
                    validation_errors.append(str(e))
                    
                if expected_schema:
                    try:
                        validate_json_schema(response, expected_schema)
                    except AssertionError as e:
                        validation_errors.append(str(e))
                        
                if expected_headers:
                    try:
                        validate_headers(response, expected_headers)
                    except AssertionError as e:
                        validation_errors.append(str(e))
                        
                if expected_content:
                    try:
                        validate_json_content(response, expected_content)
                    except AssertionError as e:
                        validation_errors.append(str(e))
                        
                if validation_errors:
                    test_result.status = "FAILED"
                    test_result.error_message = "\n".join(validation_errors)
                    test_result.validation_errors = validation_errors
                    raise AssertionError("\n".join(validation_errors))
                    
                return response
                
            except Exception as e:
                if not isinstance(e, AssertionError):
                    test_result.status = "ERROR"
                    test_result.error_message = str(e)
                raise
                
            finally:
                test_result.execution_time = time.time() - start_time
                get_reporter().add_result(test_result)
                
        return wrapper
    return decorator