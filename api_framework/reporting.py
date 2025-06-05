"""Reporting module for API test results and metrics."""
import csv
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import threading
from queue import Queue

@dataclass
class TestResult:
    """Data structure for test execution results."""
    test_name: str
    test_class: str
    status: str  # SUCCESS, FAILED, ERROR
    execution_time: float
    timestamp: datetime
    endpoint: str
    method: str
    response_code: Optional[int] = None
    error_message: Optional[str] = None
    request_headers: Optional[Dict[str, str]] = None
    response_headers: Optional[Dict[str, str]] = None
    validation_errors: Optional[List[str]] = None

class MetricsCollector:
    """Collects and aggregates test metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.error_tests = 0
        self.total_execution_time = 0.0
        self.response_times: Dict[str, List[float]] = {}
        self.status_codes: Dict[int, int] = {}
        self._lock = threading.Lock()

    def add_result(self, result: TestResult) -> None:
        """
        Add test result and update metrics.
        
        Args:
            result: TestResult instance to process
        """
        with self._lock:
            self.total_tests += 1
            self.total_execution_time += result.execution_time
            
            if result.status == "SUCCESS":
                self.passed_tests += 1
            elif result.status == "FAILED":
                self.failed_tests += 1
            else:
                self.error_tests += 1
                
            endpoint_key = f"{result.method} {result.endpoint}"
            if endpoint_key not in self.response_times:
                self.response_times[endpoint_key] = []
            self.response_times[endpoint_key].append(result.execution_time)
            
            if result.response_code:
                self.status_codes[result.response_code] = (
                    self.status_codes.get(result.response_code, 0) + 1
                )

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics summary."""
        with self._lock:
            metrics = {
                "total_tests": self.total_tests,
                "passed_tests": self.passed_tests,
                "failed_tests": self.failed_tests,
                "error_tests": self.error_tests,
                "success_rate": (
                    (self.passed_tests / self.total_tests * 100)
                    if self.total_tests > 0 else 0
                ),
                "total_execution_time": self.total_execution_time,
                "average_response_times": {
                    endpoint: sum(times) / len(times)
                    for endpoint, times in self.response_times.items()
                },
                "status_code_distribution": self.status_codes
            }
            return metrics

class ReportGenerator:
    """Generates test reports in various formats."""
    
    def __init__(self, output_dir: str = "reports"):
        """
        Initialize report generator.
        
        Args:
            output_dir: Directory for saving reports
        """
        self.output_dir = output_dir
        self.results: List[TestResult] = []
        self.metrics = MetricsCollector()
        self._queue: Queue = Queue()
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._process_queue)
        self._worker_thread.daemon = True
        self._worker_thread.start()
        
    def _process_queue(self) -> None:
        """Process queued test results."""
        while not self._stop_event.is_set() or not self._queue.empty():
            try:
                result = self._queue.get(timeout=1.0)
                self.results.append(result)
                self.metrics.add_result(result)
                self._queue.task_done()
            except Exception:  # Queue.Empty or IOError
                continue

    def add_result(self, result: TestResult) -> None:
        """
        Add test result for reporting.
        
        Args:
            result: TestResult instance to add
        """
        self._queue.put(result)

    def export_csv(self, filename: str = "test_report.csv") -> str:
        """
        Export test results to CSV.
        
        Args:
            filename: Output filename
            
        Returns:
            Path to generated CSV file
        """
        os.makedirs(self.output_dir, exist_ok=True)
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    'test_name', 'test_class', 'status',
                    'execution_time', 'timestamp', 'endpoint',
                    'method', 'response_code', 'error_message'
                ]
            )
            writer.writeheader()
            for result in self.results:
                row = asdict(result)
                row['timestamp'] = row['timestamp'].isoformat()
                writer.writerow(row)
                
        return filepath

    def export_json(self, filename: str = "test_report.json") -> str:
        """
        Export test results and metrics to JSON.
        
        Args:
            filename: Output filename
            
        Returns:
            Path to generated JSON file
        """
        os.makedirs(self.output_dir, exist_ok=True)
        filepath = os.path.join(self.output_dir, filename)
        
        report = {
            "metrics": self.metrics.get_metrics(),
            "results": [
                {
                    **asdict(result),
                    "timestamp": result.timestamp.isoformat()
                }
                for result in self.results
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
            
        return filepath

    def __del__(self) -> None:
        """Ensure background thread is stopped on deletion."""
        self._stop_event.set()
        if hasattr(self, '_worker_thread'):
            self._worker_thread.join()