#!/usr/bin/env python
import sys
import os
import time
import logging
import signal
import threading

def get_base_path():
    """Get the base directory path"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Set up paths
BASE_PATH = get_base_path()
sys.path.append(BASE_PATH)
sys.path.append(os.path.join(BASE_PATH, 'src'))

import common

# Logging configuration is handled by common.py
logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages connection checking and reconnection"""
    
    def __init__(self):
        """Initialize connection manager"""
        self.connection_event = threading.Event()
        self.connection_event.set()  # Start with connection assumed good
    
    def start_connection_monitor(self):
        """Start the connection monitoring thread"""
        try:
            connection_thread = threading.Thread(target=self._connection_check, daemon=True)
            connection_thread.start()
        except RuntimeError as e:
            if "main thread is not in main loop" in str(e):
                logger.warning("Cannot start connection monitor thread in subprocess, using polling instead")
                self._connection_check_polling()
            else:
                raise
    
    def _connection_check(self):
        """Monitor connection status"""
        from common import element_exist
        
        while True:
            try:
                if element_exist("pictures/general/connection.png", quiet_failure=True):
                    self.connection_event.clear()
                else:
                    self.connection_event.set()
            except Exception as e:
                logger.exception(f"Error in connection check: {e}")
    
    def _connection_check_polling(self):
        """Simplified connection check without threading"""
        from common import element_exist
        
        try:
            if element_exist("pictures/general/connection.png", quiet_failure=True):
                self.connection_event.clear()
            else:
                self.connection_event.set()
        except Exception as e:
            logger.exception(f"Error in connection check: {e}")
    
    def handle_reconnection(self):
        """Handle reconnection when needed"""
        try:
            from core import reconnect
            from common import element_exist
            
            self.connection_event.clear()
            
            try:
                connection_listener_thread = threading.Thread(target=reconnect)
                connection_listener_thread.start()
                connection_listener_thread.join()
            except RuntimeError as e:
                if "main thread is not in main loop" in str(e):
                    logger.warning("Cannot start reconnection thread in subprocess, using direct call")
                    reconnect()
                else:
                    raise
            
            self.connection_event.set()
        except Exception as e:
            logger.exception(f"Error in reconnection: {e}")

# Signal handler for clean shutdown
def signal_handler(sig, frame):
    """Handle termination signals"""
    logger.warning(f"Termination signal received, shutting down...")
    sys.exit(0)

def main(runs=None, difficulty=None, shared_vars=None):
    """Main function for threads runner"""
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # If parameters were not passed directly, try to get them from command line
    if runs is None or difficulty is None:
        if len(sys.argv) != 3:
            logger.error(f"Usage: threads_runner.py <runs> <difficulty>")
            return 1
            
        try:
            runs = int(sys.argv[1])
            difficulty_arg = sys.argv[2]
        except (ValueError, IndexError) as e:
            logger.exception(f"Invalid command line arguments: {e}")
            return 1
    else:
        difficulty_arg = difficulty
    
    # Handle "latest" vs numeric difficulties
    if difficulty_arg == "latest":
        difficulty = "latest"
    else:
        # Convert to integer for numeric difficulties
        difficulty = int(difficulty_arg)
    
    try:
        
        # Import here to ensure correct path initialization
        import luxcavation_functions
        
        # Initialize connection manager
        connection_manager = ConnectionManager()
        connection_manager.start_connection_monitor()
        
        # First run with SelectTeam=True
        luxcavation_functions.pre_threads_setup(difficulty, SelectTeam=True, config_type="threads_team_selection")
        
        # Remaining runs with SelectTeam=False
        for i in range(runs - 1):
            try:
                time.sleep(1)
                # Wait for connection before proceeding (copied from compiled_runner logic)
                while True:
                    if connection_manager.connection_event.is_set():
                        # Connection is good, proceed with run
                        luxcavation_functions.pre_threads_setup(difficulty, config_type="threads_team_selection")
                        break
                    else:
                        # Connection lost, wait for it to be restored
                        connection_manager.connection_event.wait()
                    
                    # Check for server errors (copied from compiled_runner)
                    try:
                        from common import element_exist
                        if element_exist("pictures/general/server_error.png"):
                            connection_manager.handle_reconnection()
                    except ImportError:
                        # Handle case where common module isn't available
                        pass
                    except Exception as e:
                                logger.exception(f"Error checking for server error: {e}")
                        
            except Exception as e:
                logger.exception(f"Error during Threads run {i+1}: {e}")
            
            # Short delay between runs
            time.sleep(2)
        
        return 0
    except Exception as e:
        logger.exception(f"Critical error in Threads runner: {e}")
        return 1

if __name__ == "__main__":
    try:
        # Get parameters from command line arguments
        if len(sys.argv) >= 3:
            runs = int(sys.argv[1])
            difficulty = sys.argv[2]
        else:
            logger.error("Usage: threads_runner.py <runs> <difficulty>")
            sys.exit(1)
            
        sys.exit(main(runs, difficulty))
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Critical error in threads_runner main: {e}")
        sys.exit(1)
