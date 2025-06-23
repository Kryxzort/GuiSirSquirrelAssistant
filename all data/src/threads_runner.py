#!/usr/bin/env python
import sys
import os
import time
import logging
import signal

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Set up paths
BASE_PATH = get_base_path()
sys.path.append(BASE_PATH)
sys.path.append(os.path.join(BASE_PATH, 'src'))

# Setting up basic logging configuration
LOG_FILENAME = os.path.join(BASE_PATH, "Pro_Peepol's.log")
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILENAME)
    ]
)
logger = logging.getLogger(__name__)

# Signal handler for clean shutdown
def signal_handler(sig, frame):
    """Handle termination signals"""
    logger.warning(f"Termination signal received, shutting down...")
    sys.exit(0)

def main(runs=None, difficulty=None, x_offset_shared=None, y_offset_shared=None):
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
            difficulty = int(sys.argv[2])
        except (ValueError, IndexError) as e:
            logger.error(f"Invalid command line arguments: {e}")
            return 1
    
    try:
        logger.info(f"Starting Threads automation with {runs} runs on difficulty {difficulty}")
        
        # Import here to ensure correct path initialization
        import luxcavation_functions
        
        for i in range(runs):
            try:
                logger.info(f"Starting run {i+1}/{runs}")
                luxcavation_functions.pre_threads_setup(difficulty)
                logger.info(f"Completed run {i+1}/{runs}")
            except Exception as e:
                logger.error(f"Error during run {i+1}: {e}")
            
            # Short delay between runs
            time.sleep(2)
        
        logger.info(f"Threads automation completed")
        return 0
    except Exception as e:
        logger.critical(f"Critical error in Threads runner: {e}")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.warning(f"Interrupted by user, shutting down...")
        sys.exit(0)