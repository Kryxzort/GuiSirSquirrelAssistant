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

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Set up paths
BASE_PATH = get_base_path()
sys.path.append(BASE_PATH)
sys.path.append(os.path.join(BASE_PATH, 'src'))

import luxcavation_functions

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

def signal_handler(sig, frame):
    """Handle termination signals"""
    logger.warning(f"Termination signal received, shutting down...")
    sys.exit(0)

def main(runs, stage, x_offset_shared=None, y_offset_shared=None):
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
            logger.info(f"Starting Exp automation for {runs} runs on Stage {stage}")
        else:
            # Convert to integer for numeric stages
            stage = int(stage_arg)
            logger.info(f"Starting Exp automation for {runs} runs on Stage {stage}")
       
        for i in range(runs):
            logger.info(f"Starting Exp run {i+1}/{runs} for Stage {stage}")
           
            try:
                # Call pre_exp_setup to run one iteration
                luxcavation_functions.pre_exp_setup(stage)
                logger.info(f"Completed Exp run {i+1}/{runs}")
            except Exception as e:
                logger.error(f"Error during Exp run {i+1}: {e}")
                # Continue with next run instead of crashing completely
           
            time.sleep(2)
       
        logger.info(f"All {runs} Exp runs completed successfully")
    except Exception as e:
        logger.critical(f"Critical error in Exp runner: {e}")
        return 1
   
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.warning(f"Interrupted by user, shutting down...")
        sys.exit(0)