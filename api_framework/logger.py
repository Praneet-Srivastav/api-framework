"""Logging module for API requests and responses."""
import datetime
import json
import os
import threading
from queue import Queue
from typing import Any, Dict, Optional

class APILogger:
    """Thread-safe logger for API requests and responses."""
    
    def __init__(self, log_file: str = "api_logs.txt"):
        """
        Initialize logger with specified log file.
        
        Args:
            log_file: Path to log file. Defaults to "api_logs.txt".
        """
        self.log_file = log_file
        self._log_queue: Queue = Queue()
        self._stop_event = threading.Event()
        self._writer_thread = threading.Thread(target=self._log_writer)
        self._writer_thread.daemon = True
        self._writer_thread.start()
        
    def _log_writer(self) -> None:
        """Background thread that processes log queue and writes to file."""
        while not self._stop_event.is_set() or not self._log_queue.empty():
            try:
                log_entry = self._log_queue.get(timeout=1.0)
                self._write_to_file(log_entry)
                self._log_queue.task_done()
            except Exception:  # Queue.Empty or IOError
                continue
                
    def _write_to_file(self, content: str) -> None:
        """Write content to log file with error handling."""
        try:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(content + '\n')
        except IOError as e:
            print(f"Error writing to log file: {e}")
            
    def _format_headers(self, headers: Dict[str, str]) -> str:
        """Format headers for logging, masking sensitive information."""
        formatted = []
        for key, value in headers.items():
            if key.lower() in {'authorization', 'cookie', 'x-api-key'}:
                value = '*****'
            formatted.append(f"{key}: {value}")
        return '\n'.join(formatted)
        
    def _format_body(self, body: Any) -> str:
        """Format request/response body for logging."""
        if not body:
            return ''
            
        if isinstance(body, (dict, list)):
            # Mask sensitive fields in JSON
            if isinstance(body, dict):
                body = body.copy()
                for key in ['password', 'token', 'api_key']:
                    if key in body:
                        body[key] = '*****'
            return json.dumps(body, indent=2)
        
        return str(body)
        
    def log_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        body: Any = None
    ) -> datetime.datetime:
        """
        Log API request details.
        
        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            body: Request body
            
        Returns:
            Timestamp of the request
        """
        timestamp = datetime.datetime.utcnow()
        
        log_entry = (
            f"[{timestamp.isoformat()}Z] REQUEST:\n"
            f"{method} {url}\n"
        )
        
        if headers:
            log_entry += f"{self._format_headers(headers)}\n"
            
        if body:
            log_entry += f"Body: {self._format_body(body)}\n"
            
        self._log_queue.put(log_entry)
        return timestamp
        
    def log_response(
        self,
        status_code: int,
        headers: Optional[Dict[str, str]],
        body: Any,
        request_timestamp: datetime.datetime
    ) -> None:
        """
        Log API response details.
        
        Args:
            status_code: HTTP status code
            headers: Response headers
            body: Response body
            request_timestamp: Timestamp from the request
        """
        timestamp = datetime.datetime.utcnow()
        duration_ms = int((timestamp - request_timestamp).total_seconds() * 1000)
        
        log_entry = (
            f"[{timestamp.isoformat()}Z] RESPONSE ({duration_ms}ms):\n"
            f"Status: {status_code}\n"
        )
        
        if headers:
            log_entry += f"{self._format_headers(headers)}\n"
            
        if body:
            log_entry += f"Body: {self._format_body(body)}\n"
            
        log_entry += "-" * 40 + "\n"
        self._log_queue.put(log_entry)
        
    def __del__(self) -> None:
        """Ensure background thread is stopped on deletion."""
        self._stop_event.set()
        if hasattr(self, '_writer_thread'):
            self._writer_thread.join()