import os
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from src.constants import ENV
from src.helper import convert_str_to_bool, get_env_value_or_raise

logger = logging.getLogger("LogShared")

def shared_log() -> None:
    """Start a web server to share log files if enabled in environment."""
    if not convert_str_to_bool(os.getenv(ENV.WEB_LOG)):
        logger.info("Shared log is disabled! nothing to do!")
        return

    try:
        log_path = get_env_value_or_raise(ENV.LOG_PATH)
        log_port = int(get_env_value_or_raise(ENV.WEB_LOG_PORT))
        
        if not os.path.exists(log_path):
            raise FileNotFoundError(f"Log directory not found: {log_path}")
            
        logger.info(f"Shared log is enabled! all logs can be found on port '{log_port}'")
        
        server = create_log_server(log_path, log_port)
        server.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start log server: {str(e)}")
        raise

def create_log_server(log_path: str, port: int) -> HTTPServer:
    """Create and configure the log server.
    
    Args:
        log_path: Directory path where log files are stored
        port: Port number to run the server on
        
    Returns:
        Configured HTTPServer instance
    """
    def handler_factory(*args, **kwargs):
        return LogSharedHandler(*args, log_path=log_path, **kwargs)
    
    return HTTPServer(('0.0.0.0', port), handler_factory)

class LogSharedHandler(BaseHTTPRequestHandler):
    """HTTP request handler for serving log files via web interface."""
    
    def __init__(self, *args, log_path: str, **kwargs) -> None:
        """Initialize the handler with the log directory path.
        
        Args:
            log_path: Directory path where log files are stored
        """
        self.log_path = log_path
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:
        """Handle GET requests to serve log files or directory listing."""
        if self.path == "/":
            self._serve_directory_listing()
        else:
            self._serve_log_file()

    def _serve_directory_listing(self) -> None:
        """Serve HTML page with links to available log files."""
        html = "<html><body>"
        for filename in os.listdir(self.log_path):
            html += f"<p><a href=\"{filename}\">{filename}</a></p>"
        html += "</body></html>"

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def _serve_log_file(self) -> None:
        """Serve the requested log file content."""
        file_path = os.path.join(self.log_path, self.path.lstrip("/"))
        try:
            with open(file_path, "rb") as file:
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(file.read())
        except FileNotFoundError:
            self.send_error(404, "Log file not found")
        except PermissionError:
            self.send_error(403, "Permission denied to access log file")
        except Exception as e:
            logger.error(f"Error serving log file: {str(e)}")
            self.send_error(500, "Internal server error")


