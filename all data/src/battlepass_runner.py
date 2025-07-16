#!/usr/bin/env python
import threading
import sys
import os
import common
import logging
import time
import signal

# Determine if running as executable or script
def get_base_path():
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        return os.path.dirname(sys.executable)
    else:
        # Running as script
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
    """
    Handle termination signals
    """
    logger.warning(f"Termination signal received, shutting down...")
    sys.exit(0)




#Not gonna lie, I have no clue what most of the code above this comment does. Im pretty all of it, save logging, can be removed
#But my code works, so im not gonna bother with that




def navigate_to_battlepass():
    """
    Navigate to Battlepass missions from the main menu.
    """
    logger.info(f"Navigating to Battlepass")
    
    while not common.element_exist("pictures/CustomAdded1080p/battlepass/battlepass_icon.png"):
        logger.info(f"Battlepass icon not found, navigating to home screen")
        common.click_matching("pictures/general/window.png")
        time.sleep(0.5)

    time.sleep(0.5)
    
    while common.element_exist("pictures/CustomAdded1080p/battlepass/battlepass_icon.png"):
        logger.info(f"Clicking Battlepass icon")
        common.click_matching("pictures/CustomAdded1080p/battlepass/battlepass_icon.png")
        time.sleep(0.5)
        
    logger.info(f"Navigating to Battlepass missions")    
    
    while not common.element_exist("pictures/CustomAdded1080p/battlepass/pass_missions.png"):
        time.sleep(0.5)
    common.click_matching("pictures/CustomAdded1080p/battlepass/pass_missions.png")
    logger.info(f"Navigation to Battlepass complete")

def click_completed_missions():
    """
    Recursively clicks all completed missions
    
    Note, does not work for seasonal ones. I am too lasy to implement the scrolling for something that is done once a month
    """
    
    logger.info(f"Clicking daily missions")
    
    while common.element_exist("pictures/CustomAdded1080p/battlepass/completed_mission.png", threshold=0.9):
        logger.info(f"Completed mission found")
        common.click_matching("pictures/CustomAdded1080p/battlepass/completed_mission.png", threshold=0.9)
        time.sleep(0.5)
     
    logger.info(f"Clicking weekly missions")
    
    common.click_matching("pictures/CustomAdded1080p/battlepass/weekly.png")
    time.sleep(3)
    
    while common.element_exist("pictures/CustomAdded1080p/battlepass/completed_mission.png", threshold=0.9):
        logger.info(f"Completed mission found")
        common.click_matching("pictures/CustomAdded1080p/battlepass/completed_mission.png", threshold=0.9)
        time.sleep(0.5)
        
    logger.info(f"Finished clicking missions")
    
    common.click_matching("pictures/CustomAdded1080p/battlepass/exit.png")


def main():
    """Main function for battlepass runner"""
    # Register signal handlers for clean exit if it is being run in the main thread
    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    try:
        logger.info(f"Starting battlepass rewards automation")
       
        navigate_to_battlepass()
        click_completed_missions()
        
        logger.info(f"Battlepass automation completed")
        return 0
    except Exception as e:
        logger.critical(f"Critical error in Battlepass runner: {e}")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.warning(f"Interrupted by user, shutting down...")
        sys.exit(0)