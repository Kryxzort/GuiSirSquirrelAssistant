import sys
import os
import json
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
import shared_vars

# Determine if running as executable or script
def get_base_path():
    """Get the base directory path"""
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

# Logging configuration is handled by common.py
logger = logging.getLogger(__name__)

# Function to create Mirror instance based on config type
def get_mirror_instance(config_type="status_selection"):
    """Get Mirror instance for specific config type"""
    status = "poise"  # Default fallback
    
    try:
        # Use cached config instead of file I/O
        data = shared_vars.ConfigCache.get_config(config_type)
        if data:
            # Handle numbered priority format: {"1": "burn", "2": "poise"}
            if all(key.isdigit() for key in data.keys()):
                # Sort by number and extract values in priority order
                sorted_items = sorted(data.items(), key=lambda x: int(x[0]))
                statuses = [item[1] for item in sorted_items]
            else:
                # Fallback to old format: {"selected_statuses": [...]}
                statuses = data.get("selected_statuses", [])
            if statuses:
                status = statuses[0].strip().lower()
        
        mirror_instance = mirror.Mirror(status)
        logger.info(f"Initialized Mirror with {config_type} status: {status}")
        return mirror_instance
    except Exception as e:
        logger.exception(f"Error initializing Mirror with {config_type}: {e}")
        return mirror.Mirror("poise")  # Default fallback

# Create default mirror instance for backwards compatibility (mirror dungeon)
m = get_mirror_instance("status_selection")

screen_width, screen_height = common.get_resolution()
logger.debug(f"Screen dimensions: {screen_width}x{screen_height}")

def click_matching_EXP(image_path, threshold=0.8, area="center", 
                      movewidth=0, moveheight=0, move2width=0, move2height=0,
                      dragwidth=0, dragheight=0, drag2width=0, drag2height=0,
                      dragspeed=1):
    """Advanced image matching with drag capabilities for EXP stage selection"""
    
    def verify_element_visible(image_path, threshold):
        try:
            if common.element_exist(image_path, threshold):
                time.sleep(0.5)  # Wait to verify stability
                
                if common.element_exist(image_path, threshold):
                    return True
                else:
                    return False
            else:
                return False
        except Exception as e:
            logger.exception(f"Exception during element verification: {e}")
            return False
    
    def try_click_element(image_path, threshold, area, attempt_name):
        try:
            found = common.match_image(image_path, threshold, area)
            
            if found and len(found) > 0:
                x, y = found[0]
                common.mouse_move_click(x, y)
                return True
            else:
                return False
        except Exception as e:
            logger.exception(f"Exception during click attempt ({attempt_name}): {e}")
            return False
    
    # Attempt 1: Direct check and click
    if verify_element_visible(image_path, threshold):
        if try_click_element(image_path, threshold, area, "initial check"):
            return True
    
    # Attempt 2: First drag
    try:
        common.mouse_move(movewidth, moveheight)
        common.mouse_drag(dragwidth, dragheight, dragspeed)
        time.sleep(0.5)  # Wait after drag
        
        if verify_element_visible(image_path, threshold):
            if try_click_element(image_path, threshold, area, "first drag"):
                return True
    except Exception as e:
        logger.exception(f"Exception during first drag attempt: {e}")
    
    # Attempt 3: Second drag
    try:
        common.mouse_move(move2width, move2height)
        common.mouse_drag(drag2width, drag2height, dragspeed)
        time.sleep(0.5)  # Wait after drag
        
        if verify_element_visible(image_path, threshold):
            if try_click_element(image_path, threshold, area, "second drag"):
                return True
    except Exception as e:
        logger.exception(f"Exception during second drag attempt: {e}")
    
    logger.warning(f"All attempts to find {os.path.basename(image_path)} failed")
    return False

def click_continue():
    """Wait for and click confirmation dialogs after battle completion"""
    start_time = time.time()

    continue_clicked = False

    while time.time() - start_time < 60:  # 60 second maximum check time
        
        if common.click_matching("pictures/CustomAdded1080p/luxcavation/thread/confirminverted.png", recursive=False):
            logger.info(f"Confirmation dialog found, clicked it")
            common.mouse_move_to_empty_area()
            logger.info(f"clicked comfirm")
            continue_clicked = True
        elif common.click_matching("pictures/general/confirm_w.png", recursive=False):
            pass
            time.sleep(0.5)
        elif common.element_exist("pictures/CustomAdded1080p/battle/in_battle_area.png"):
            logger.info(f"tried to click continue but battle ongoing")
            common.error_screenshot()
            core.battle()
        if not common.element_exist("pictures/CustomAdded1080p/luxcavation/thread/confirminverted.png") and continue_clicked:
            break
        time.sleep(0.5)
            
    if time.time() - start_time >= 60:
        return

def squad_select_lux(mirror_instance, SelectTeam=False):
    """Handle squad selection for luxcavation battles"""
    
    if SelectTeam:
        status = mirror_utils.squad_choice(mirror_instance.status)
        if status is None:
            status = "poise"
        else:
            if not common.click_matching(status, recursive=False):
                found = common.match_image("pictures/CustomAdded1080p/general/squads/squad_select.png")
                x,y = found[0]
                offset_x, offset_y = common.scale_coordinates_1440p(90, 90)
                common.mouse_move(x + offset_x, y + offset_y)
                for i in range(30):
                    common.mouse_scroll(1000)
                common.sleep(1)
                for _ in range(4):
                    if not common.element_exist(status):
                        for i in range(7):
                            common.mouse_scroll(-1000)
                        common.sleep(1)
                        if common.click_matching(status, recursive=False):
                            break
                        continue
                    else:
                        common.click_matching(status)
                        break
    if SelectTeam or not (common.element_exist("pictures/CustomAdded1080p/general/squads/five_squad.png") or common.element_exist("pictures/CustomAdded1080p/general/squads/full_squad.png")):
        common.click_matching("pictures/CustomAdded1080p/general/squads/clear_selection.png", mousegoto200=True)
        common.click_matching("pictures/CustomAdded1080p/general/confirm.png", recursive=False)
        for i, position in enumerate(mirror_instance.squad_order):
            x, y = position
            common.mouse_move_click(x, y)
        
    common.click_matching("pictures/CustomAdded1080p/general/squads/to_battle.png")
    
    while not common.element_exist("pictures/battle/winrate.png"):
        common.sleep(0.5)
        
    logger.info(f"Battle screen detected, entering battle")
    core.battle()
    common.mouse_move_to_empty_area()
    logger.info(f"Battle completed, checking for confirmation dialog")
    core.check_loading()
    click_continue()

def navigate_to_lux():
    """Navigate to the luxcavation menu"""
    
    if common.click_matching("pictures/CustomAdded1080p/luxcavation/luxcavation.png", recursive=False):
        return
    
    attempts = 0
    max_attempts = 5
    
    while not common.element_exist("pictures/CustomAdded1080p/luxcavation/luxcavation.png"):
        attempts += 1
        if attempts > max_attempts:
            logger.warning(f"Failed to find Luxcavation after {max_attempts} attempts")
            break
            
        common.click_matching("pictures/general/window.png")
        common.click_matching("pictures/general/drive.png")
        time.sleep(0.5)
        
    common.click_matching("pictures/CustomAdded1080p/luxcavation/luxcavation.png")

def pre_exp_setup(Stage, SelectTeam=False, config_type="exp_team_selection"):
    """Setup for EXP farming run"""
    logger.info(f"Starting EXP farming setup for stage: {Stage} with config: {config_type}")
    core.refill_enkephalin()
    navigate_to_exp(Stage, SelectTeam, config_type)

def pre_threads_setup(Difficulty, SelectTeam=False, config_type="threads_team_selection"):
    """Setup for thread farming run"""
    logger.info(f"Starting Thread farming setup for difficulty: {Difficulty} with config: {config_type}")
    core.refill_enkephalin()
    navigate_to_threads(Difficulty, SelectTeam, config_type)

def navigate_to_exp(Stage, SelectTeam=False, config_type="exp_team_selection"):
    """Navigate to and start specific EXP stage"""
    logger.info(f"Navigating to EXP stage: {Stage} with config: {config_type}")
    
    already_on_lux_screen = common.element_exist("pictures/CustomAdded1080p/luxcavation/luxcavation_brown.png")
    
    if not already_on_lux_screen:
        logger.debug(f"Not on Luxcavation screen, navigating there first")
        navigate_to_lux()
    else:
        logger.debug("Already on Luxcavation screen, clicking EXP tab")
        common.click_matching("pictures/CustomAdded1080p/luxcavation/exp/exp.png", 0.8)
    
    if Stage == "latest":
        logger.debug("Clicking latest stage using coordinates")
        # Use pre-calculated latest stage coordinates
        lux_coords = shared_vars.ScaledCoordinates.get_scaled_coords("luxcavation_coords")
        latest_x, latest_y = lux_coords["latest_stage"]
        common.mouse_move_click(latest_x, latest_y)
        success = True
    else:
        thresholds = {
            1: 0.95, 2: 0.95, 3: 0.95, 4: 0.97, 
            5: 0.95, 6: 0.95, 7: 0.99
        }
        threshold = thresholds[Stage]
        stage_image = f"pictures/CustomAdded1080p/luxcavation/exp/stage{Stage}.png"
        
        # Use pre-calculated EXP drag coordinates
        lux_coords = shared_vars.ScaledCoordinates.get_scaled_coords("luxcavation_coords")
        drag_start_x, drag_start_y = lux_coords["exp_drag_start"]
        drag_end_x, drag_end_y = lux_coords["exp_drag_end"]
        drag_middle_x, drag_middle_y = lux_coords["exp_drag_middle"]
        
        success = click_matching_EXP(
            stage_image, 
            threshold, 
            "bottom",
            drag_start_x, drag_start_y,
            drag_end_x, drag_end_y,
            drag_end_x, drag_end_y,
            drag_middle_x, drag_middle_y,
            0.3
        )
    
    if not success:
        logger.warning(f"Failed to click Stage {Stage}")
        if common.element_exist("pictures/battle/winrate.png"):
            core.battle()
            click_continue()
            return

        common.click_matching("pictures/CustomAdded1080p/general/goback.png")
        navigate_to_exp(Stage, SelectTeam, config_type)
        return
    
    logger.debug(f"Click successful, waiting for UI to settle...")
    time.sleep(0.5)  # Wait 0.5 seconds for UI transition
    
    if common.element_exist("pictures/CustomAdded1080p/general/squads/squad_select.png"):
        logger.info(f"Squad select screen detected")
        # Get mirror instance for this config type
        mirror_instance = get_mirror_instance(config_type)
        squad_select_lux(mirror_instance, SelectTeam)
        common.key_press(Key="esc", presses=2)
    else:
        logger.warning(f"Squad select screen not detected, retrying")
        common.key_press(Key="esc", presses=2)
        time.sleep(1)
        common.key_press(Key="esc", presses=2)
        navigate_to_exp(Stage, SelectTeam, config_type)
        return
    

def navigate_to_threads(Difficulty, SelectTeam=False, config_type="threads_team_selection"):
    """Navigate to and start specific thread difficulty"""
    
    if Difficulty != "latest" and Difficulty not in [20, 30, 40, 50]:
        logger.error(f"Invalid thread difficulty: {Difficulty}")
        return
        
    already_on_lux_screen = common.element_exist("pictures/CustomAdded1080p/luxcavation/luxcavation_brown.png")
    
    if not already_on_lux_screen:
        logger.debug(f"Not on Luxcavation screen, navigating there first")
        navigate_to_lux()
        
    common.click_matching("pictures/CustomAdded1080p/luxcavation/thread/thread.png")
    
    if not common.element_exist("pictures/CustomAdded1080p/luxcavation/thread/enter.png"):
        logger.warning("Enter button not found")
        navigate_to_threads(Difficulty, SelectTeam, config_type)
        return
        
    # Use pre-calculated thread select coordinates
    lux_coords = shared_vars.ScaledCoordinates.get_scaled_coords("luxcavation_coords")
    thread_x, thread_y = lux_coords["thread_select"]
    common.mouse_move_click(thread_x, thread_y)
    time.sleep(0.5)
    
    if Difficulty == "latest":
        logger.info(f"clicking latest using coordinates")
        # Use pre-calculated latest difficulty coordinates
        lux_coords = shared_vars.ScaledCoordinates.get_scaled_coords("luxcavation_coords")
        latest_diff_x, latest_diff_y = lux_coords["latest_difficulty"]
        common.mouse_move_click(latest_diff_x, latest_diff_y)
        success = True
    else:
        difficulty_image = f"pictures/CustomAdded1080p/luxcavation/thread/difficulty{Difficulty}.png"
        
        if common.click_matching(difficulty_image, threshold=0.97, area="center", mousegoto200=False, recursive=False):
            success = True
        else:
            for i in range(7):
                found_matches = common.match_image("pictures/CustomAdded1080p/luxcavation/thread/difficulty.png", 0.97, area="left")
                if found_matches:
                    x, y = found_matches[0]
                    common.mouse_move(x, y)
                    common.mouse_scroll(1000)
                    
            common.click_matching(difficulty_image, 0.97, area="center", mousegoto200=False)
            success = True
        
    logger.debug(f"Click successful, waiting for UI to settle...")
    time.sleep(0.5)  # Wait 0.5 seconds for UI transition
        
    if common.element_exist("pictures/CustomAdded1080p/general/squads/squad_select.png"):
        logger.info(f"Squad select screen detected")
        # Get mirror instance for this config type
        mirror_instance = get_mirror_instance(config_type)
        squad_select_lux(mirror_instance, SelectTeam)
        common.key_press(Key="esc", presses=2)
    else:
        logger.warning(f"Squad select screen not detected, retrying")
        common.key_press(Key="esc", presses=2)
        time.sleep(1)
        common.key_press(Key="esc", presses=2)
        navigate_to_threads(Difficulty, SelectTeam, config_type)
        return
