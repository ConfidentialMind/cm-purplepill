"""
Utility functions for CM PurplePill
"""

import logging
import os
import subprocess
import sys
from typing import Dict, List, Optional, Tuple, Union


def setup_logging(log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configure logging for the application
    
    Args:
        log_file: Path to log file, if None logs to stderr
        level: Logging level
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger("cmpp")
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', 
                                 datefmt='%Y-%m-%d %H:%M:%S')
    
    # Always add stderr handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (IOError, PermissionError) as e:
            logger.warning(f"Cannot write to log file {log_file}: {e}")
            if not os.access(os.path.dirname(log_file) or '.', os.W_OK):
                fallback_log = "/tmp/cm-purplepill.log"
                logger.warning(f"Using fallback log file: {fallback_log}")
                try:
                    file_handler = logging.FileHandler(fallback_log)
                    file_handler.setFormatter(formatter)
                    logger.addHandler(file_handler)
                except Exception as e:
                    logger.warning(f"Cannot write to fallback log file: {e}")
    
    return logger


def execute_command(command: List[str], timeout: int = 10) -> Tuple[bool, str]:
    """
    Execute a shell command and return its output
    
    Args:
        command: List containing the command and its arguments
        timeout: Timeout in seconds
        
    Returns:
        Tuple of (success, output)
    """
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, f"Command failed with error: {result.stderr}"
            
    except subprocess.TimeoutExpired:
        return False, f"Command timed out after {timeout} seconds"
    except Exception as e:
        return False, f"Error executing command: {str(e)}"


def is_numeric(value: str) -> bool:
    """
    Check if a string represents a numeric value
    
    Args:
        value: String to check
        
    Returns:
        True if numeric, False otherwise
    """
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def write_atomic(file_path: str, content: str) -> bool:
    """
    Write content to a file atomically using a temporary file
    
    Args:
        file_path: Path to the file to write
        content: Content to write
        
    Returns:
        True if successful, False otherwise
    """
    temp_path = f"{file_path}.new"
    try:
        # Write content to temporary file
        with open(temp_path, 'w') as f:
            f.write(content)
        
        # Atomically replace the target file
        os.replace(temp_path, file_path)
        return True
    except Exception as e:
        logger = logging.getLogger("cmpp")
        logger.error(f"Failed to write {file_path}: {e}")
        
        # Clean up temp file if it exists
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception:
            pass
            
        return False


def check_nvidia_tools() -> bool:
    """
    Check if NVIDIA tools are available
    
    Returns:
        True if nvidia-smi is available, False otherwise
    """
    success, _ = execute_command(["nvidia-smi", "--version"])
    return success
