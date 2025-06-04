import sys
import os
import common
import core
import logging
import keyboard
import time
import threading
import signal
import mirror
import mirror_utils
import pyautogui

# Determine if running as executable or script
def get_base_path():
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        folder_path = os.path.dirname(os.path.abspath(__file__))
        # Check if we're in the src folder or main folder
        if os.path.basename(folder_path) == 'src':
            return os.path.dirname(folder_path)
        return folder_path

# Get base path for resource access
BASE_PATH = get_base_path()

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

# Read status and create Mirror instance globally
status_path = os.path.join(BASE_PATH, "config", "status_selection.txt")
try:
    with open(status_path) as f:
        status = f.read().strip().lower()
    m = mirror.Mirror(status)
    logger.info(f"Initialized Mirror with status: {status}")
except Exception as e:
    logger.error(f"Error initializing Mirror with status file: {e}")
    status = "poise"  # Default fallback
    m = mirror.Mirror(status)
    logger.info(f"Initialized Mirror with default status: {status}")

screenWidth, screenHeight = pyautogui.size()
logger.debug(f"Screen dimensions: {screenWidth}x{screenHeight}")

def click_matching_EXP(image_path, threshold=0.8, area="center", movewidth=0, moveheight=0,
                      move2width=0, move2height=0, dragwidth=0, dragheight=0,
                      drag2width=0, drag2height=0, dragspeed=1):
    """
    Find and click an image with fallback drag strategies if not found initially.
    
    Attempts to find an image on screen and click it. If the image isn't found or isn't 
    stable, tries two different drag operations to reveal the element.
    
    Args:
        image_path: Path to target image file
        threshold: Match confidence threshold (0.0-1.0)
        area: Screen area to search ("center", "bottom", etc.)
        movewidth/moveheight: First mouse move coordinates
        move2width/move2height: Second mouse move coordinates
        dragwidth/dragheight: First drag destination coordinates
        drag2width/drag2height: Second drag destination coordinates
        dragspeed: Speed of drag operations (lower is faster)
        
    Returns:
        bool: True if element was found and clicked, False otherwise
    """
    logger.info(f"Attempting to find and click: {os.path.basename(image_path)}")
    logger.debug(f"Click parameters - threshold: {threshold}, area: {area}")
    
    def verify_element_visible(image_path, threshold):
        """Check if element exists, wait 0.5 seconds, then check again for stability."""
        try:
            logger.debug(f"Verifying element stability with threshold {threshold}")
            if common.element_exist(image_path, threshold):
                time.sleep(0.5)  # Wait to verify stability
                
                if common.element_exist(image_path, threshold):
                    logger.debug(f"Element verified stable")
                    return True
                else:
                    logger.debug(f"Element disappeared during stability check")
                    return False
            else:
                logger.debug(f"Element not found in initial stability check")
                return False
        except Exception as e:
            logger.error(f"Exception during element verification: {e}")
            return False
    
    def try_click_element(image_path, threshold, area, attempt_name):
        """Try to get coordinates and click the element."""
        try:
            logger.debug(f"Getting coordinates for {attempt_name}")
            found = common.match_image(image_path, threshold, area)
            
            if found and len(found) > 0:
                x, y = found[0]
                logger.debug(f"Found at coordinates ({x}, {y}), clicking")
                common.mouse_move_click(x, y)
                logger.info(f"Successfully clicked element on {attempt_name}")
                return True
            else:
                logger.debug(f"No valid coordinates found on {attempt_name}")
                return False
        except Exception as e:
            logger.error(f"Exception during click attempt ({attempt_name}): {e}")
            return False
    
    # Attempt 1: Direct check and click
    logger.info(f"Attempt 1: Direct check")
    if verify_element_visible(image_path, threshold):
        if try_click_element(image_path, threshold, area, "initial check"):
            return True
    
    # Attempt 2: First drag
    try:
        logger.info(f"Attempt 2: First drag operation")
        common.mouse_move(movewidth, moveheight)
        common.mouse_drag(dragwidth, dragheight, dragspeed)
        time.sleep(0.5)  # Wait after drag
        
        if verify_element_visible(image_path, threshold):
            if try_click_element(image_path, threshold, area, "first drag"):
                return True
    except Exception as e:
        logger.error(f"Exception during first drag attempt: {e}")
    
    # Attempt 3: Second drag
    try:
        logger.info(f"Attempt 3: Second drag operation")
        common.mouse_move(move2width, move2height)
        common.mouse_drag(drag2width, drag2height, dragspeed)
        time.sleep(0.5)  # Wait after drag
        
        if verify_element_visible(image_path, threshold):
            if try_click_element(image_path, threshold, area, "second drag"):
                return True
    except Exception as e:
        logger.error(f"Exception during second drag attempt: {e}")
    
    logger.warning(f"All attempts to find {os.path.basename(image_path)} failed")
    return False

def click_continue():
    start_time = time.time()
    common.mouse_move(200,200)

    continue_clicked = False

    while time.time() - start_time < 60:  # 60 second maximum check time
        if common.element_exist("pictures/battle/winrate.png"):
            core.battle()
            return
        if common.element_exist("pictures/CustomAdded1080p/luxcavation/thread/confirminverted.png"):
            logger.info(f"Confirmation dialog found, clicking it")
            common.click_matching("pictures/CustomAdded1080p/luxcavation/thread/confirminverted.png")
            common.mouse_move(200,200)
            logger.info(f"clicked comfirm")
            continue_clicked = True
        elif common.element_exist("pictures/general/confirm_w.png"):
            logger.info(f"Manager Level Up")
            common.click_matching("pictures/general/confirm_w.png")
            time.sleep(0.5)
            if common.element_exist("pictures/CustomAdded1080p/luxcavation/thread/confirminverted.png"):
                logger.info(f"Confirmation dialog found, clicking it")
                common.click_matching("pictures/CustomAdded1080p/luxcavation/thread/confirminverted.png")
                common.mouse_move(200,200)
                logger.info(f"clicked comfirm")
                continue_clicked = True
                time.sleep(0.7)
        if not common.element_exist("pictures/CustomAdded1080p/luxcavation/thread/confirminverted.png") and continue_clicked:
            logger.info(f"not on confirm screen anymore, exitting loop")
            break
        time.sleep(0.5)
            
    if time.time() - start_time >= 60:
        logger.debug(f"No confirmation dialog detected within timeout period")

def squad_select_lux(mirror_instance):
    """
    Select squad members and initiate battle.
    
    Selects sinners according to squad order in configuration,
    initiates battle, and waits for battle screen to appear before
    calling the battle function.
    """
    logger.info(f"Selecting squad for battle")
    
    common.click_matching("pictures/CustomAdded1080p/general/clear_selection.png")
    if common.element_exist("pictures/CustomAdded1080p/general/confirm.png"):
        common.click_matching("pictures/CustomAdded1080p/general/confirm.png")
            
    # Click squad members according to the configuration
    for i, position in enumerate(mirror_instance.squad_order):
        x, y = position
        logger.debug(f"Selecting squad member {i+1} at ({x}, {y})")
        common.mouse_move_click(x, y)

#    if (not common.element_exist("pictures/CustomAdded1080p/general/half_squad.png") and
#        not common.element_exist("pictures/CustomAdded1080p/general/five_squad.png")):
#        common.click_matching("pictures/CustomAdded1080p/general/clear_selection.png")
#       if common.element_exist("pictures/CustomAdded1080p/general/confirm.png"):
#           common.click_matching("pictures/CustomAdded1080p/general/confirm.png")
#           
        # Click squad members according to the configuration
#       for i, position in enumerate(mirror_instance.squad_order):
#           x, y = position
#           logger.debug(f"Selecting squad member {i+1} at ({x}, {y})")
#           common.mouse_move_click(x, y)
        
    # Start battle
    logger.info(f"Starting battle")
    common.click_matching("pictures/CustomAdded1080p/general/to_battle.png")
    
    # Wait for battle screen
    logger.debug(f"Waiting for battle screen")
    while not common.element_exist("pictures/battle/winrate.png"):
        common.sleep(0.5)
        
    logger.info(f"Battle screen detected, entering battle")
    core.battle()
    common.mouse_move(200,200)
    if common.element_exist("pictures/battle/winrate.png"):
        core.battle()
        return
    # After squad selection and battle finished:
    logger.info(f"Battle completed, checking for confirmation dialog")
    click_continue()

def navigate_to_lux():
    """
    Navigate to Luxcavation from the main menu.
    
    Checks if already on Luxcavation screen, and if not,
    navigates through the menu system to reach it.
    """
    logger.info(f"Navigating to Luxcavation")
    
    if common.element_exist("pictures/CustomAdded1080p/luxcavation/luxcavation.png"):
        logger.debug(f"Luxcavation icon found, clicking directly")
        common.click_matching("pictures/CustomAdded1080p/luxcavation/luxcavation.png")
        return
    
    # Only execute this section if not already on the correct screen
    logger.debug(f"Luxcavation icon not found, navigating through menus")
    attempts = 0
    max_attempts = 5
    
    while not common.element_exist("pictures/CustomAdded1080p/luxcavation/luxcavation.png"):
        attempts += 1
        if attempts > max_attempts:
            logger.warning(f"Failed to find Luxcavation after {max_attempts} attempts")
            break
            
        logger.debug(f"Navigation attempt {attempts}/{max_attempts}")
        common.click_matching("pictures/general/window.png")
        common.click_matching("pictures/general/drive.png")
        time.sleep(0.5)
        
    common.click_matching("pictures/CustomAdded1080p/luxcavation/luxcavation.png")
    logger.info(f"Navigation to Luxcavation complete")

def pre_exp_setup(Stage):
    """
    Perform setup before Luxcavation missions.
    
    Refills enkephalin and navigates to the specified exp stage.
    
    Args:
        Stage: The exp stage number to navigate to (1-7)
    """
    logger.info(f"Setting up for Luxcavation Stage {Stage}")
    core.refill_enkephalin()
    navigate_to_exp(Stage)

def pre_threads_setup(Difficulty):
    """
    Perform setup before Luxcavation missions.
    
    Refills enkephalin and navigates to the specified threads stage.
    
    Args:
        Stage: The exp stage number to navigate to (20,30,40,50)
    """
    logger.info(f"Setting up for Luxcavation Stage {Difficulty}")
    core.refill_enkephalin()
    navigate_to_threads(Difficulty)

def navigate_to_exp(Stage):
    """
    Navigate to a specific Exp stage in Luxcavation.
    
    Checks if already on Luxcavation screen, navigates there if needed,
    then finds and clicks the specified exp stage. Handles squad selection
    and battle process, including confirming any post-battle dialogs.
    
    Args:
        Stage: The exp stage number to navigate to (1-7)
    """
    logger.info(f"Navigating to Exp Stage {Stage}")
    
    # Check if already on Luxcavation screen
    already_on_lux_screen = common.element_exist("pictures/CustomAdded1080p/luxcavation/luxcavation_brown.png")
    
    if not already_on_lux_screen:
        logger.debug(f"Not on Luxcavation screen, navigating there first")
        navigate_to_lux()
    else:
        logger.debug(f"Already on Luxcavation screen, clicking exp")
        common.click_matching("pictures/CustomAdded1080p/luxcavation/exp/exp.png", 0.8)
    
    # latest stage check
    if Stage == "latest":
        logger.info(f"clicking latest using coordinates")
        common.mouse_move_click(screenWidth * 0.8401, screenHeight * 0.6616)
        success = True
    else:
        # Stage-specific thresholds
        thresholds = {
            1: 0.95, 2: 0.95, 3: 0.95, 4: 0.97, 
            5: 0.95, 6: 0.95, 7: 0.99
        }
        # Get threshold and construct image path
        threshold = thresholds[Stage]
        stage_image = f"pictures/CustomAdded1080p/luxcavation/exp/stage{Stage}.png"
        
        # Attempt to click the stage
        logger.info(f"Attempting to click Stage {Stage} with threshold {threshold}")
        success = click_matching_EXP(
            stage_image, 
            threshold, 
            "bottom",
            screenWidth * 0.2068, screenHeight * 0.0444,
            screenWidth * 1.0, screenHeight * 0.0444,
            screenWidth * 1.0, screenHeight * 0.0444,
            screenWidth * 0.6, screenHeight * 0.0444,
            0.3
        )
    
    # Handle failure by going back and retrying
    if not success:
        logger.warning(f"Failed to click Stage {Stage}, retrying")
        if common.element_exist("pictures/battle/winrate.png"):
            logger.info(f"Battle screen detected, entering battle")
            core.battle()
            logger.info(f"Battle completed, checking for confirmation dialog")
            click_continue()
            logger.info(f"Exp Stage {Stage} navigation and battle complete")
            return

        common.click_matching("pictures/CustomAdded1080p/general/goback.png")
        navigate_to_exp(Stage)
        return
    
    # Add a delay to allow UI to settle after successful click
    logger.debug(f"Click successful, waiting for UI to settle...")
    time.sleep(0.5)  # Wait 0.5 seconds for UI transition
    
    # Check if we're in squad select
    if common.element_exist("pictures/mirror/general/squad_select.png"):
        logger.info(f"Squad select screen detected")
        squad_select_lux(m)
        common.key_press(Key="esc",presses=2)
    else:
        logger.warning(f"Squad select screen not detected, retrying")
        common.key_press(Key="esc",presses=2)
        time.sleep(1)
        common.key_press(Key="esc",presses=2)
        navigate_to_exp(Stage)
        return
    
    logger.info(f"Exp Stage {Stage} navigation and battle complete")

def navigate_to_threads(Difficulty):
    """
    Navigate to a specific Thread difficulty in Luxcavation.
    
    Navigates to the Thread section, selects the specified difficulty level,
    handles squad selection, and manages post-battle confirmations.
    
    Args:
        Difficulty: The thread difficulty level to navigate to (20, 30, 40, or 50)
    """
    logger.info(f"Navigating to Thread difficulty {Difficulty}")
    
    # Validate input
    if Difficulty not in [20, 30, 40, 50]:
        logger.error(f"Invalid thread difficulty: {Difficulty}")
        return
        
    # Check if already on Luxcavation screen
    already_on_lux_screen = common.element_exist("pictures/CustomAdded1080p/luxcavation/luxcavation_brown.png")
    
    # Navigate to Luxcavation if needed and click on thread
    if not already_on_lux_screen:
        logger.debug(f"Not on Luxcavation screen, navigating there first")
        navigate_to_lux()
        
    logger.info(f"Clicking Thread option")
    common.click_matching("pictures/CustomAdded1080p/luxcavation/thread/thread.png")
    
    # Check if we can enter thread
    if not common.element_exist("pictures/CustomAdded1080p/luxcavation/thread/enter.png"):
        logger.warning(f"Enter button not found, retrying")
        navigate_to_threads(Difficulty)
        return
        
    # Click enter
    logger.debug(f"Enter button found, clicking it")
    common.click_matching("pictures/CustomAdded1080p/luxcavation/thread/enter.png")
    
    # Construct the difficulty-specific image path
    difficulty_image = f"pictures/CustomAdded1080p/luxcavation/thread/difficulty{Difficulty}.png"
    
    # Check if the difficulty is immediately visible
    logger.info(f"Checking for Thread difficulty {Difficulty}")
    if common.element_exist(difficulty_image, 0.95):
        logger.debug(f"Difficulty {Difficulty} found, clicking directly")
        common.click_matching(difficulty_image, 0.95, area="center", mousegoto200="0")
    else:
        # Scroll to find the difficulty
        logger.info(f"Difficulty not immediately visible, scrolling to find it")
        for i in range(7):
            found_matches = common.match_image("pictures/CustomAdded1080p/luxcavation/thread/difficulty.png", 0.95, area="left")
            if found_matches:
                x, y = found_matches[0]
                common.mouse_move(x, y)
                common.mouse_scroll(1000)
                logger.debug(f"Scroll attempt {i+1}/7")
                
        logger.info(f"Attempting to click difficulty {Difficulty} after scrolling")
        common.click_matching(difficulty_image, 0.95, area="center", mousegoto200="0")
        
    logger.debug(f"Click successful, waiting for UI to settle...")
    time.sleep(0.5)  # Wait 0.5 seconds for UI transition
        
    if common.element_exist("pictures/mirror/general/squad_select.png"):
        logger.info(f"Squad select screen detected")
        squad_select_lux(m)
        logger.info(f"Difficulty {Difficulty} navigation and battle complete")
        common.key_press(Key="esc",presses=2)
    else:
        logger.warning(f"Squad select screen not detected, retrying")
        common.key_press(Key="esc",presses=2)
        time.sleep(1)
        common.key_press(Key="esc",presses=2)
        navigate_to_threads(Difficulty)
        return