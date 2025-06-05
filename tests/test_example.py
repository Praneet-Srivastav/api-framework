"""Example test cases demonstrating framework usage with reporting."""
import json
import pytest
from api_framework.client import APIClient
from api_framework.config import Config
from api_framework.assertions import api_test, get_reporter

class TestExampleAPI:
    """Example test suite for demonstrating framework features."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test configuration and client."""
        self.config = Config("dev")
        self.config.set_defaults()
        self.client = APIClient(self.config)
        
    def teardown_method(self, method):
        """Generate reports after each test method."""
        reporter = get_reporter()
        reporter.export_json(f"{method.__name__}_report.json")
        reporter.export_csv(f"{method.__name__}_report.csv")
        
    @api_test(
        endpoint="/users",
        method="POST",
        expected_status=201,
        expected_schema={
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "username": {"type": "string"},
                "email": {"type": "string", "format": "email"}
            },
            "required": ["id", "username", "email"]
        }
    )
    def test_create_user(self):
        """Test user creation endpoint."""
        return {
            "json": {
                "username": "testuser",
                "email": "test@example.com",
                "password": "secretpass123"
            }
        }
        
    @api_test(
        endpoint="/users/{user_id}",
        expected_status=200,
        expected_content={
            "id": 1,
            "username": "testuser",
            "email": "test@example.com"
        }
    )
    def test_get_user(self):
        """Test get user endpoint."""
        return {"endpoint": "/users/1"}
        
    @api_test(
        endpoint="/auth/login",
        method="POST",
        expected_status=200,
        expected_headers={"Content-Type": "application/json"}
    )
    def test_login(self):
        """Test login endpoint."""
        return {
            "json": {
                "username": "testuser",
                "password": "secretpass123"
            }
        }
        
    def test_custom_request_with_reporting(self):
        """Test making custom request with manual assertions and reporting."""
        reporter = get_reporter()
        
        # Test getting user list
        try:
            start_time = pytest.approx(time.time())
            response = self.client.get(
                "/users",
                params={"role": "admin", "active": "true"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0
            
            reporter.add_result(TestResult(
                test_name="test_get_users_list",
                test_class=self.__class__.__name__,
                status="SUCCESS",
                execution_time=time.time() - start_time,
                timestamp=datetime.utcnow(),
                endpoint="/users",
                method="GET",
                response_code=response.status_code,
                request_headers=dict(response.request.headers),
                response_headers=dict(response.headers)
            ))
            
        except Exception as e:
            reporter.add_result(TestResult(
                test_name="test_get_users_list",
                test_class=self.__class__.__name__,
                status="ERROR" if not isinstance(e, AssertionError) else "FAILED",
                execution_time=time.time() - start_time,
                timestamp=datetime.utcnow(),
                endpoint="/users",
                method="GET",
                error_message=str(e)
            ))
            raise

if __name__ == "__main__":
    pytest.main([__file__, "-v"])