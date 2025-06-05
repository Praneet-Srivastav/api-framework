# API Testing Framework

A modular Python-based API testing framework with comprehensive logging, configuration management, test utilities, and reporting capabilities.

## Features

- Support for all HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Automatic request/response logging with timestamps and execution time
- Environment-specific configuration management
- Authentication support (Basic Auth, Bearer Token)
- Comprehensive assertion utilities
- JSON schema validation
- Test decorators for simplified test case creation
- Thread-safe logging with non-blocking I/O
- Retry mechanism for failed requests
- Clear separation of concerns through modular architecture
- Advanced reporting and metrics tracking

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Example

```python
from api_framework.client import APIClient
from api_framework.config import Config
from api_framework.assertions import api_test, get_reporter

class TestAPI:
    def setup(self):
        self.config = Config("dev")
        self.client = APIClient(self.config)
    
    def teardown_method(self, method):
        # Generate reports after each test
        reporter = get_reporter()
        reporter.export_json(f"{method.__name__}_report.json")
        reporter.export_csv(f"{method.__name__}_report.csv")
    
    @api_test(
        endpoint="/users",
        method="POST",
        expected_status=201
    )
    def test_create_user(self):
        return {
            "json": {
                "username": "testuser",
                "email": "test@example.com"
            }
        }
```

### Configuration

Create environment-specific configuration files in `api_framework/config/`:

```json
{
    "base_url": "https://api.example.com",
    "timeout": 30,
    "retry_attempts": 3,
    "auth": {
        "type": "bearer",
        "token": "your-token-here"
    }
}
```

### Running Tests

```bash
pytest tests/ -v
```

## Logging

Logs are written to `api_logs.txt` by default. Example log entry:

```
[2023-11-15T14:30:45Z] REQUEST:
POST https://api.example.com/login
Authorization: Bearer *****
Content-Type: application/json
Body: {"username": "test", "password": "*****"}

[2023-11-15T14:30:46Z] RESPONSE (328ms):
Status: 200
Body: {"token": "abc123", "expiry": 3600}
----------------------------------------
```

## Test Reports

The framework includes comprehensive reporting capabilities that provide detailed insights into test execution:

### Metrics Tracked

- Total number of tests executed
- Pass/fail/error rates
- Execution times per endpoint
- Response time distributions
- Status code distributions
- Validation errors
- Detailed request/response information

### Report Formats

1. JSON Reports
```python
reporter = get_reporter()
reporter.export_json("test_report.json")
```

Example JSON report:
```json
{
    "metrics": {
        "total_tests": 10,
        "passed_tests": 8,
        "failed_tests": 1,
        "error_tests": 1,
        "success_rate": 80.0,
        "total_execution_time": 1.523,
        "average_response_times": {
            "GET /users": 0.125,
            "POST /users": 0.231
        },
        "status_code_distribution": {
            "200": 7,
            "201": 1,
            "400": 1,
            "500": 1
        }
    },
    "results": [
        {
            "test_name": "test_create_user",
            "test_class": "TestAPI",
            "status": "SUCCESS",
            "execution_time": 0.231,
            "endpoint": "/users",
            "method": "POST",
            "response_code": 201
        }
    ]
}
```

2. CSV Reports
```python
reporter = get_reporter()
reporter.export_csv("test_report.csv")
```

The CSV report includes columns for:
- Test name and class
- Status (SUCCESS/FAILED/ERROR)
- Execution time
- Timestamp
- Endpoint and method
- Response code
- Error messages

### Automatic Report Generation

You can automatically generate reports after each test method:

```python
def teardown_method(self, method):
    reporter = get_reporter()
    reporter.export_json(f"{method.__name__}_report.json")
    reporter.export_csv(f"{method.__name__}_report.csv")
```

### Thread-Safe Metrics Collection

The reporting system is thread-safe and uses non-blocking I/O for report generation, making it suitable for parallel test execution.

## Architecture

The framework consists of several modular components:

- `client.py`: HTTP client with retry logic and logging
- `config.py`: Environment-specific configuration management
- `logger.py`: Thread-safe request/response logging
- `assertions.py`: Test utilities and decorators
- `reporting.py`: Test reporting and metrics collection

## Features in Detail

### HTTP Methods

```python
# GET request
response = client.get("/users", params={"role": "admin"})

# POST request with JSON
response = client.post("/users", json={"username": "test"})

# PUT request
response = client.put("/users/1", json={"email": "new@example.com"})

# PATCH request
response = client.patch("/users/1", json={"status": "active"})

# DELETE request
response = client.delete("/users/1")
```

### Authentication

```python
# Basic Auth
config.set("auth", {
    "type": "basic",
    "username": "user",
    "password": "pass"
})

# Bearer Token
config.set("auth", {
    "type": "bearer",
    "token": "your-token-here"
})
```

### Assertions and Reporting

```python
from api_framework.assertions import (
    validate_status_code,
    validate_json_schema,
    validate_headers,
    validate_json_content,
    get_reporter
)

# Validate response
validate_status_code(response, 200)
validate_json_schema(response, schema)
validate_headers(response, {"Content-Type": "application/json"})
validate_json_content(response, expected_data)

# Get test reports
reporter = get_reporter()
reporter.export_json("test_report.json")
reporter.export_csv("test_report.csv")
metrics = reporter.metrics.get_metrics()
```

### Test Decorator

```python
@api_test(
    endpoint="/users/{user_id}",
    method="GET",
    expected_status=200,
    expected_schema=USER_SCHEMA,
    expected_headers={"Content-Type": "application/json"},
    expected_content={"id": 1, "username": "test"}
)
def test_get_user(self):
    return {"endpoint": "/users/1"}
```

## Best Practices

1. Create separate test files for different API resources
2. Use environment-specific configurations
3. Keep tests focused and independent
4. Use the provided decorators for consistent testing
5. Leverage JSON schema validation for response verification
6. Monitor test reports for performance and reliability insights
7. Generate reports after test execution for analysis
8. Track metrics over time to identify trends and issues

## Error Handling

The framework includes automatic retry logic for failed requests and comprehensive error handling for:

- Network issues
- Timeouts
- Invalid JSON responses
- Schema validation errors
- Authentication failures

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License