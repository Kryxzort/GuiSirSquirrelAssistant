import sys
import logging
import os
import threading
import mirror

logger = logging.getLogger(__name__)

def get_base_path():
    """Get the correct base path for the application"""
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        base_path = os.path.dirname(sys.executable)
        logger.debug(f"Running as frozen executable, base path: {base_path}")
        return base_path
    else:
        # Running as script - go up one level to reach the "all data" directory
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logger.debug(f"Running as script, base path: {base_path}")
        return base_path

def setup_paths_and_imports():
    """Set up paths and import required modules"""
    # Set up paths
    BASE_PATH = get_base_path()
    logger.debug(f"Final BASE_PATH: {BASE_PATH}")
    
    # Add necessary paths
    src_path = os.path.join(BASE_PATH, 'src')
    logger.debug(f"Adding src path: {src_path}")
    sys.path.append(src_path)
    sys.path.append(BASE_PATH)
    
    # Verify config file exists
    config_path = os.path.join(BASE_PATH, "config")
    status_path = os.path.join(config_path, "status_selection.txt")
    logger.debug(f"Status selection path: {status_path}")
    
    if not os.path.exists(status_path):
        logger.critical(f"Status selection file not found at: {status_path}")
        raise FileNotFoundError(f"Status selection file not found: {status_path}")
    
    # Import modules
    logger.debug(f"Importing modules...")
    
    try:
        from core import pre_md_setup, reconnect
        from common import error_screenshot, element_exist
        import mirror
        logger.debug(f"Successfully imported all modules")
        return BASE_PATH, status_path
    except ImportError as e:
        logger.critical(f"Failed to import modules: {e}")
        raise

def load_status_list(status_path):
    """Load status list from file"""
    try:
        logger.debug(f"Opening status selection file: {status_path}")
        with open(status_path, "r") as f:
            status_list_file = [i.strip().lower() for i in f.readlines()]
        logger.debug(f"Status list loaded: {status_list_file}")
        return status_list_file
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
        logger.debug(f"Starting connection check thread")
        connection_thread = threading.Thread(target=self._connection_check, daemon=True)
        connection_thread.start()
    
    def _connection_check(self):
        """Monitor connection status"""
        from common import element_exist
        
        while True:
            try:
                if element_exist("pictures/general/connection.png"):
                    self.connection_event.clear()
                    logger.debug(f"Connection check: connection issue found")
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
            logger.debug(f"Disconnected, Pausing")
            
            connection_listener_thread = threading.Thread(target=reconnect)
            connection_listener_thread.start()
            connection_listener_thread.join()
            
            logger.debug(f"Reconnected, Resuming")
            self.connection_event.set()
        except Exception as e:
            logger.error(f"Error in reconnection: {e}")

def mirror_dungeon_run(num_runs, status_list_file, connection_manager, shared_vars):
    """Main mirror dungeon run logic"""
    try:
        from core import pre_md_setup
        from common import element_exist, error_screenshot, update_from_shared_vars
        
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
                # ✅ UPDATE SHARED VARIABLES AT START OF EACH RUN
                update_from_shared_vars(shared_vars)
                logger.debug(f"Updated shared variables for run {run_count + 1}")
                
                pre_md_setup()
                logger.info(f"Current Team: " + status_list[i])
                run_complete = 0
                
                # Create Mirror instance
                logger.debug(f"Creating Mirror instance with status: {status_list[i]}")
                MD = mirror.Mirror(status_list[i])
                
                # Set up mirror
                logger.debug(f"Setting up mirror")
                MD.setup_mirror()
                
                # Main loop for this run
                while run_complete != 1:
                    if connection_manager.connection_event.is_set():
                        logger.debug(f"Connection is set, running mirror loop")
                        win_flag, run_complete = MD.mirror_loop()
                        logger.debug(f"Mirror loop returned: win_flag={win_flag}, run_complete={run_complete}")
                    
                    if element_exist("pictures/general/server_error.png"):
                        connection_manager.handle_reconnection()

                # Update counters
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
        
    except Exception as e:
        logger.exception(f"Critical error in mirror_dungeon_run: {e}")
        from common import error_screenshot
        error_screenshot()

def setup_logging(base_path):
    """Set up logging configuration"""
    LOG_FILENAME = os.path.join(base_path, "Pro_Peepol's.log")
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILENAME)
        ]
    )

def main(num_runs, shared_vars):
    """Main function for multiprocessing - UPDATED FOR SHAREDVARS SYSTEM"""
    try:
        logger.info(f"compiled_runner.py main function started with {num_runs} runs")
        
        # Set up paths and imports
        base_path, status_path = setup_paths_and_imports()
        
        # Set up logging
        setup_logging(base_path)
        
        # ✅ UPDATE SHARED VARIABLES FROM GUI
        import common
        common.update_from_shared_vars(shared_vars)
        logger.info(f"Initialized with shared variables from GUI")
        
        # Load status list
        status_list_file = load_status_list(status_path)
        
        # Set up connection manager
        connection_manager = ConnectionManager()
        connection_manager.start_connection_monitor()
        
        # Start mirror dungeon automation
        logger.info(f"Starting mirror_dungeon_run with {num_runs} runs")
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
    logger.info(f"compiled_runner.py main execution started")
    
    try:
        # Set up paths and imports
        base_path, status_path = setup_paths_and_imports()
        
        # Set up logging
        setup_logging(base_path)
        
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
        
        # ✅ FOR COMMAND LINE: Create fake shared_vars for backward compatibility
        class FakeSharedVars:
            """Fake shared vars for command line execution"""
            def __init__(self):
                # Get offsets from command line arguments
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
        
        # Load status list
        status_list_file = load_status_list(status_path)
        
        # Set up connection manager
        connection_manager = ConnectionManager()
        connection_manager.start_connection_monitor()
        
        # ✅ UPDATE COMMON.PY WITH FAKE SHARED VARS
        import common
        common.update_from_shared_vars(fake_shared_vars)
        
        # Start mirror dungeon
        logger.info(f"Starting mirror_dungeon_run with {count} runs")
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