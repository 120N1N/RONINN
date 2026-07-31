import subprocess
import time
import logging
import os
import threading
import json
from datetime import datetime
from typing import List, Optional
import redis
from backend.config import settings

try:
    redis_client_exec = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception:
    redis_client_exec = None

logger = logging.getLogger("corvus.executor")

class ToolError(Exception):
    pass

class Executor:
    """
    Executes external tools with timeout, resource limits, and error handling.
    """
    
    @staticmethod
    def run(command: List[str], timeout: int = 300, cwd: Optional[str] = None, scan_id: str = None, tool_name: str = None) -> str:
        """
        Runs a command and returns its stdout. Optionally saves output to file.
        """
        try:
            logger.info(f"Executing command: {' '.join(command)}")
            start_time = time.time()
            
            import signal
            from backend.db.database import SessionLocal
            from backend.db.models import Scan
            
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            stdout_lines = []
            stderr_lines = []
            
            def read_stream(stream, is_stderr=False):
                for line in iter(stream.readline, ""):
                    if not is_stderr:
                        stdout_lines.append(line)
                        if scan_id and redis_client_exec:
                            try:
                                redis_client_exec.publish(f"scan_logs:{scan_id}", json.dumps({
                                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                                    "phase": tool_name if tool_name else "System",
                                    "message": line.strip()
                                }))
                            except Exception:
                                pass
                    else:
                        stderr_lines.append(line)
                stream.close()

            import threading
            t_out = threading.Thread(target=read_stream, args=(process.stdout, False))
            t_err = threading.Thread(target=read_stream, args=(process.stderr, True))
            t_out.daemon = True
            t_err.daemon = True
            t_out.start()
            t_err.start()
            
            # Polling to check DB for cancellation
            if scan_id:
                db = SessionLocal()
                # we will poll every 2 seconds
                poll_interval = 2
                elapsed = 0
                while process.poll() is None:
                    if elapsed >= timeout:
                        if os.name != 'nt':
                            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                        else:
                            process.terminate()
                        raise subprocess.TimeoutExpired(command, timeout)
                        
                    # Check DB status
                    db.expire_all()
                    scan = db.query(Scan).filter(Scan.id == scan_id).first()
                    if scan and scan.status.upper() == "CANCELLED":
                        logger.warning(f"Scan {scan_id} cancelled. Terminating subprocess.")
                        if os.name != 'nt':
                            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                        else:
                            process.terminate()
                        db.close()
                        raise ToolError("Scan was cancelled by user.")
                    
                    time.sleep(poll_interval)
                    elapsed += poll_interval
                
                db.close()
            
            t_out.join()
            t_err.join()
            
            stdout_content = "".join(stdout_lines)
            stderr_content = "".join(stderr_lines)
            
            duration = time.time() - start_time
            logger.debug(f"Command finished in {duration:.2f}s with exit code {process.returncode}")
            
            if process.returncode != 0:
                logger.warning(f"Command '{' '.join(command)}' failed with exit code {process.returncode}")
            
            # Save raw output if requested
            if scan_id and tool_name:
                output_dir = os.path.join("tools_output", str(scan_id))
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"{tool_name}.txt")
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(f"Command: {' '.join(command)}\n")
                    f.write(f"Exit Code: {process.returncode}\n")
                    f.write(f"Duration: {duration:.2f}s\n")
                    f.write("-" * 40 + "\n")
                    f.write(stdout_content)
                    if stderr_content:
                        f.write("\n" + "=" * 20 + " STDERR " + "=" * 20 + "\n")
                        f.write(stderr_content)
            
            return stdout_content
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout}s: {' '.join(command)}")
            raise ToolError(f"Tool timeout: {' '.join(command)}")
        except Exception as e:
            logger.error(f"Unexpected error executing tool: {str(e)}")
            raise ToolError(f"Execution error: {str(e)}")

    @staticmethod
    def run_to_file(command: List[str], output_file: str, timeout: int = 300):
        """
        Runs a command and redirects output to a file.
        """
        try:
            with open(output_file, 'w') as f:
                subprocess.run(
                    command,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    timeout=timeout,
                    check=False
                )
        except Exception as e:
            logger.error(f"Failed to run command to file: {str(e)}")
            raise ToolError(str(e))
