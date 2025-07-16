import sys
import logging
import os
import threading
import json
import mirror

logger = None

def get_base_path():
    """Get the correct base path for the application"""
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        base_path = os.path.dirname(sys.executable)
        return base_path
    else:
        # Running as script - go up one level to reach the "all data" directory
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return base_path

def setup_paths_and_imports():
    """Set up paths and import required modules"""
    BASE_PATH = get_base_path()
    
    # Add necessary paths
    src_path = os.path.join(BASE_PATH, 'src')
    sys.path.append(src_path)
    sys.path.append(BASE_PATH)
    
    # Verify config file exists
    config_path = os.path.join(BASE_PATH, "config")
    status_json_path = os.path.join(config_path, "status_selection.json")
    
    if os.path.exists(status_json_path):
        status_path = status_json_path
    else:
        # Use basic logging since custom logger not initialized yet
        basic_logger = logging.getLogger(__name__)
        basic_logger.critical(f"Status selection file not found at: {status_json_path}")
        raise FileNotFoundError(f"Status selection file not found: {status_json_path}")
    
    # Import modules
    
    try:
        # Import common FIRST to set up DirtyLogger before other modules
        import common
        from core import pre_md_setup, reconnect
        from common import error_screenshot, element_exist
        import mirror
        
        # Initialize logger after importing common (which sets up DirtyLogger)
        global logger
        logger = logging.getLogger(__name__)
        
        return BASE_PATH, status_path
    except ImportError as e:
        # Create a basic logger for error reporting if imports fail
        basic_logger = logging.getLogger(__name__)
        basic_logger.critical(f"Failed to import modules: {e}")
        raise

def load_status_list(status_path):
    try:
        with open(status_path, "r") as f:
            data = json.load(f)
            # Handle numbered priority format: {"1": "burn", "2": "poise"}
            if all(key.isdigit() for key in data.keys()):
                # Sort by number and extract values in priority order
                sorted_items = sorted(data.items(), key=lambda x: int(x[0]))
                statuses = [item[1] for item in sorted_items]
            else:
                # Fallback to old format: {"selected_statuses": [...]}
                statuses = data.get("selected_statuses", [])
            return [status.strip().lower() for status in statuses if status.strip()]
    except Exception as e:
        logger.critical(f"Error reading status selection file: {e}")
        raise

class ConnectionManager:
    """Manages connection checking and reconnection"""
    
    def __init__(self):
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
                logger.error(f"Error in connection check: {e}")
    
    def handle_reconnection(self):
        """Handle reconnection when needed"""
        try:
            from core import reconnect
            from common import element_exist
            
            logger.warning(f"Server error detected")
            self.connection_event.clear()
            
            connection_listener_thread = threading.Thread(target=reconnect)
            connection_listener_thread.start()
            connection_listener_thread.join()
            
            self.connection_event.set()
        except Exception as e:
            logger.error(f"Error in reconnection: {e}")

def mirror_dungeon_run(num_runs, status_list_file, connection_manager, shared_vars):
    """Main mirror dungeon run logic"""
    try:
        from core import pre_md_setup
        from common import element_exist, error_screenshot
        
        run_count = 0
        win_count = 0
        lose_count = 0
        
        # Ensure we have status selections
        if not status_list_file:
            logger.critical(f"Status list file is empty, cannot proceed")
            return
            
        # Create status list for runs
        status_list = (status_list_file * ((num_runs // len(status_list_file)) + 1))[:num_runs]
        logger.info(f"Starting Run with statuses: {status_list}")
        
        for i in range(num_runs):
            logger.info(f"Run {run_count + 1}")
            
            try:
                if pre_md_setup():

                    logger.info(f"Current Team: " + status_list[i])
                    run_complete = 0
                    
                    MD = mirror.Mirror(status_list[i])
                    
                    MD.setup_mirror()
                
                while run_complete != 1:
                    if connection_manager.connection_event.is_set():
                        win_flag, run_complete = MD.mirror_loop()
                    else:
                        # Connection lost, wait for it to be restored
                        connection_manager.connection_event.wait()
                    
                    if element_exist("pictures/general/server_error.png"):
                        connection_manager.handle_reconnection()

                if win_flag == 1:
                    win_count += 1
                    logger.info(f"Run {run_count + 1} completed with a win")
                else:
                    lose_count += 1
                    logger.info(f"Run {run_count + 1} completed with a loss")
                run_count += 1
                
            except Exception as e:
                logger.exception(f"Error in run {run_count + 1}: {e}")
                error_screenshot()
                # Continue with next run instead of breaking out
                run_count += 1
        
        logger.info(f'Completed all runs. Won: {win_count}, Lost: {lose_count}')
        
        import battlepass_runner
        battlepass_runner.main()
        
    except Exception as e:
        logger.exception(f"Critical error in mirror_dungeon_run: {e}")
        from common import error_screenshot
        error_screenshot()

def setup_logging(base_path):
    """Logging configuration is handled by common.py"""
    pass

def main(num_runs, shared_vars):
    try:
        base_path, status_path = setup_paths_and_imports()
        
        setup_logging(base_path)
        
        logger.info(f"compiled_runner.py main function started with {num_runs} runs")
        
        status_list_file = load_status_list(status_path)
        
        connection_manager = ConnectionManager()
        connection_manager.start_connection_monitor()
        
        mirror_dungeon_run(num_runs, status_list_file, connection_manager, shared_vars)
        logger.info(f"mirror_dungeon_run completed successfully")
        
    except Exception as e:
        logger.critical(f"Unhandled exception in compiled_runner main: {e}")
        try:
            from common import error_screenshot
            error_screenshot()
        except:
            pass  # Don't let screenshot errors crash the main error handler
        return  # Return instead of sys.exit for multiprocessing

if __name__ == "__main__":
    """Legacy support for command line execution"""
    
    try:
        base_path, status_path = setup_paths_and_imports()
        
        setup_logging(base_path)
        
        logger.info(f"compiled_runner.py main execution started")
        
        # Get run count from command line
        if len(sys.argv) > 1:
            try:
                count = int(sys.argv[1])
                logger.info(f"Run count from arguments: {count}")
            except ValueError:
                count = 1
                logger.warning(f"Invalid run count argument: {sys.argv[1]}, using default 1")
        else:
            count = 1
            logger.info(f"No run count specified, using default 1")
        
        class FakeSharedVars:
            def __init__(self):
                x_offset = 0
                y_offset = 0
                if len(sys.argv) > 2:
                    try:
                        x_offset = int(sys.argv[2])
                    except ValueError:
                        pass
                if len(sys.argv) > 3:
                    try:
                        y_offset = int(sys.argv[3])
                    except ValueError:
                        pass
                
                # Create fake Value objects
                from multiprocessing import Value
                self.x_offset = Value('i', x_offset)
                self.y_offset = Value('i', y_offset)
                # Add other default values
                self.debug_mode = Value('b', False)
                self.click_delay = Value('f', 0.5)
        
        fake_shared_vars = FakeSharedVars()
        logger.info(f"Created fake shared vars for command line execution")
        
        status_list_file = load_status_list(status_path)
        
        connection_manager = ConnectionManager()
        connection_manager.start_connection_monitor()
        
        mirror_dungeon_run(count, status_list_file, connection_manager, fake_shared_vars)
        logger.info(f"mirror_dungeon_run completed successfully")
        
    except Exception as e:
        logger.critical(f"Unhandled exception in compiled_runner main: {e}")
        try:
            from common import error_screenshot
            error_screenshot()
        except:
            pass
        sys.exit(1)  # Exit with error code for command line
    
    logger.info(f"compiled_runner.py completed successfully")
