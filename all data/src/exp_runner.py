#!/usr/bin/env python
"""
Exp Runner Script - Runs Luxcavation Exp automation
This script is called by the GUI and runs as a separate process
"""
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

import luxcavation_functions
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
        connection_thread = threading.Thread(target=self._connection_check, daemon=True)
        connection_thread.start()
    
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
    
    def handle_reconnection(self):
        """Handle reconnection when needed"""
        try:
            from core import reconnect
            from common import element_exist
            
            self.connection_event.clear()
            
            connection_listener_thread = threading.Thread(target=reconnect)
            connection_listener_thread.start()
            connection_listener_thread.join()
            
            self.connection_event.set()
        except Exception as e:
            logger.exception(f"Error in reconnection: {e}")

def signal_handler(sig, frame):
    """Handle termination signals"""
    logger.warning(f"Termination signal received, shutting down...")
    sys.exit(0)

def main(runs, stage, shared_vars=None):
    """Main function for exp runner"""
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
   
    try:
        # Use the parameters passed to the function
        stage_arg = stage  # Instead of sys.argv[2]
        
        # Handle "latest" as a special case
        if stage_arg == "latest":
            stage = "latest"
        else:
            # Convert to integer for numeric stages
            stage = int(stage_arg)
        
        # Initialize connection manager
        connection_manager = ConnectionManager()
        connection_manager.start_connection_monitor()
       
        luxcavation_functions.pre_exp_setup(stage, SelectTeam=True, config_type="exp_team_selection")
        runs = runs - 1
        for i in range(runs):
           
            try:
                time.sleep(1)
                # Wait for connection before proceeding (copied from compiled_runner logic)
                while True:
                    if connection_manager.connection_event.is_set():
                        # Connection is good, proceed with run
                        luxcavation_functions.pre_exp_setup(stage, config_type="exp_team_selection")
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
                logger.exception(f"Error during Exp run {i+1}: {e}")
                # Continue with next run instead of crashing completely
           
            time.sleep(2)
       
        
    except Exception as e:
        logger.exception(f"Critical error in Exp runner: {e}")
        return 1
   
    return 0

if __name__ == "__main__":
    try:
        # Get parameters from command line arguments
        if len(sys.argv) >= 3:
            runs = int(sys.argv[1])
            stage = sys.argv[2]
        else:
            logger.error("Usage: exp_runner.py <runs> <stage>")
            sys.exit(1)
            
        sys.exit(main(runs, stage))
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Critical error in exp_runner main: {e}")
        sys.exit(1)
