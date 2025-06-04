import sys
import os
from sys import exit
import logging
import time
import pyautogui

screenWidth, screenHeight = pyautogui.size()

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

# Import after setting up paths
import common

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

def refill_enkephalin():
    """Converts to Module (Runs from the main menu)"""
    logger.info(f"Converting Enkephalin to Modules")
    common.click_matching("pictures/general/module.png")
    common.click_matching("pictures/general/right_arrow.png")
    common.click_matching("pictures/general/confirm_w.png")
    common.click_matching("pictures/general/cancel.png")

def navigate_to_md():
    """Navigates to the Mirror Dungeon from the menu"""
    logger.info(f"Navigating to Mirror Dungeon")
    while(not common.element_exist("pictures/general/MD.png")):
        common.click_matching("pictures/general/window.png")
        common.click_matching("pictures/general/drive.png")
    common.click_matching("pictures/general/MD.png")

def pre_md_setup():
    if common.element_exist("pictures/mirror/general/md.png"):
        return
    else:
        refill_enkephalin()
        navigate_to_md()

def check_loading():
    """Handles the loading screen transitions"""
    common.sleep(2) #Handles fade to black
    logger.info(f"Loading")
    while(common.element_exist("pictures/general/loading.png")): #checks for loading screen bar
        common.sleep(0.5) #handles the remaining loading

def transition_loading():
    """Theres a load that occurs while transitioning to the next floor"""
    logger.info(f"Moving to Next Floor")
    common.sleep(5)

def post_run_load():
    """There is some oddity in the loading time for this that makes it annoying to measure so this is a blanket wait for main menu stall"""
    while(not common.element_exist("pictures/general/module.png")):
        common.sleep(1)
    logger.info(f"Loaded back to Main Menu")

def reconnect():
    while(common.element_exist("pictures/general/server_error.png")):
        common.sleep(6)
        common.click_matching("pictures/general/retry.png")
        common.mouse_move(200,200)
    if common.element_exist("pictures/general/no_op.png"):
        common.click_matching("pictures/general/close.png")
        logger.info(f"COULD NOT RECONNECT TO THE SERVER. SHUTTING DOWN!")
        os._exit(0)

def battle():
    """Handles battles by mashing winrate, also handles skill checks and end of battle loading"""
    logger.info(f"Starting Battle")
    battle_finished = 0
    winrate_visible_start = None
    winrate_timeout = 5
    winrate_invisible_start = None
    winrate_invisible_timeout = 30
    
    while(battle_finished != 1):
        if common.element_exist("pictures/general/loading.png"): #Checks for loading screen to end the while loop
            common.mouse_up()
            if common.element_exist("pictures/battle/winrate.png"):
                battle()
                return
            logger.info(f"Loading")
            battle_finished = 1
            common.sleep(3)
            logger.debug(f"finished battle")
            return
        if common.element_exist("pictures/events/skip.png"): #Checks for special battle skill checks prompt then calls skill check functions
            common.mouse_up()
            while(True):
                common.click_skip(1)
                if common.element_exist("pictures/mirror/general/event.png"):
                    battle_check()
                    break
                if common.element_exist("pictures/events/skill_check.png"):
                    skill_check()
                    break
                    
        if common.element_exist("pictures/battle/winrate.png"):
            winrate_invisible_start = None
            current_time = time.time()
            if winrate_visible_start is None:
                winrate_visible_start = current_time
            
            # Check if winrate has been visible for too long and might be stuck
            elif current_time - winrate_visible_start > winrate_timeout:
                logger.warning(f"Winrate screen stuck for {winrate_timeout} seconds, attempting direct click")
                common.mouse_up()
                common.click_matching("pictures/battle/winrate.png")
                common.key_press("enter")
                winrate_visible_start = None
        else: # Check if winrate hasn't been visible for too long and battle might have ended or winrate might be covered
            if common.element_exist("pictures/CustomAdded1080p/mirror/general/InMirrorSelectCheck.png"): #checks for a special button in the mirror select menu to stop the battle.
                battle_finished = 1
                logger.debug(f"finished battle")
                return
        
            winrate_visible_start = None
            current_time = time.time()
            if winrate_invisible_start is None:
                winrate_invisible_start = current_time
            
            elif current_time - winrate_invisible_start > winrate_invisible_timeout:
                logger.warning(f"didnt see winrate for {winrate_invisible_timeout} seconds, clicking middle of the screen")
                common.mouse_up()
                common.mouse_move_click(screenWidth * 0.5,screenHeight * 0.5)
                winrate_invisible_start = None
            
        # Normal winrate handling
        common.mouse_up()
        x,y = common.uniform_scale_coordinates(2165,1343)
        common.mouse_move_click(x,y)
        common.key_press("p")
        ego_check()
        common.key_press("enter")
        common.mouse_down()

        if common.element_exist("pictures/general/server_error.png"):
            common.mouse_up()
            logger.info(f"Lost Connection to Server, Reconnecting")
            reconnect()

def ego_check():
    """Checks for hopeless/struggling clashes and uses E.G.O if possible"""
    bad_clashes = []
    if common.element_exist("pictures/battle/ego/hopeless.png",0.79):
        logger.debug(f"HOPELESS FOUND")
        bad_clashes += common.match_image("pictures/battle/ego/hopeless.png",0.79)
        
    if common.element_exist("pictures/battle/ego/struggling.png",0.79):
        logger.debug(f"STRUGGLING FOUND")
        bad_clashes += common.match_image("pictures/battle/ego/struggling.png",0.79)
    
    bad_clashes = [i for i in bad_clashes if i]
    if len(bad_clashes):
        bad_clashes = [x for x in bad_clashes if x[1] > common.scale_y(1023)] # this is to remove any false positives
        logger.debug(bad_clashes)
        logger.debug(f"BAD CLASHES FOUND")
        for x,y in bad_clashes:
            usable_ego = []
            common.mouse_move(x-common.scale_x(55),y+common.scale_y(100))
            common.mouse_hold()
            egos = common.match_image("pictures/battle/ego/sanity.png")
            for i in egos:
                x,y = i
                logger.debug(common.luminence(x,y))
                if common.luminence(x,y) > 100:#Sanity icon
                    usable_ego.append(i)
            if len(usable_ego):
                logger.debug(f"EGO USABLE")
                ego = common.random_choice(usable_ego)
                x,y = ego
                if common.element_exist("pictures/battle/ego/sanity.png"):
                    common.mouse_move_click(x + common.scale_x(30), y+common.scale_y(30))
                    common.sleep(0.3)
                    common.mouse_click()
                    common.sleep(1)
            else:
                logger.debug(f"EGO UNUSABLE")
                if common.element_exist("pictures/battle/ego/sanity.png"):
                    common.mouse_move_click(200,200)
                    common.sleep(1)
        common.key_press("p") #Change to Damage
        common.key_press("p") #Deselects
        common.key_press("p") #Back to winrate
    return
    
def battle_check(): #pink shoes, woppily, doomsday clock
    logger.info(f"Battle Event Check")
    common.sleep(1)
    if common.element_exist("pictures/battle/investigate.png"): #Woppily
        logger.debug(f"WOPPILY")
        common.click_matching("pictures/battle/investigate.png")
        common.wait_skip("pictures/events/continue.png")
        return 0
        
    elif common.element_exist("pictures/battle/NO.png"): #Woppily
        logger.info(f"WOPPILY PT2")
        for i in range(3):
            common.click_matching("pictures/battle/NO.png")
            common.mouse_move_click(common.scale_x(1193),common.scale_y(623))
            while(not common.element_exist("pictures/events/proceed.png")):
                if common.element_exist("pictures/events/continue.png"):
                    common.click_matching("pictures/events/continue.png")
                    return 0
                common.mouse_click()
            common.click_matching("pictures/events/proceed.png")
            common.mouse_move_click(common.scale_x(1193),common.scale_y(623))
            while(not common.element_exist("pictures/battle/NO.png")):
                common.mouse_click()

    elif common.element_exist("pictures/battle/refuse.png"): # Pink Shoes
        logger.info(f"PINK SHOES")
        common.click_matching("pictures/battle/refuse.png")
        common.wait_skip("pictures/events/proceed.png")
        skill_check()
        return 0
    
    elif common.element_exist("pictures/battle/shield_passive.png"): #Hohenheim
        logger.info(f"Hohenheim")
        options = ["pictures/battle/shield_passive.png","pictures/battle/poise_passive.png", "pictures/battle/sp_passive.png"]
        for option in options:
            if option == "pictures/battle/sp_passive.png":
                common.click_matching("pictures/battle/small_scroll.png")
                for i in range(5):
                    common.mouse_scroll(-1000)
            common.click_matching(option)
            common.sleep(0.5)
            if not common.element_exist("pictures/events/result.png",0.9):
                continue
            else:
                break
        common.wait_skip("pictures/events/continue.png")
        return 0
    
    elif common.element_exist("pictures/battle/offer_sinner.png"): #Doomsday Clock
        logger.info(f"DOOMSDAY CLOCK")
        found = common.match_image("pictures/battle/offer_clay.png")
        if found:
            x,y = found[0]
            logger.info(f"Found Clay Option")
            logger.debug(common.luminence(x,y-common.uniform_scale_single(72)))
            if common.luminence(x,y-common.uniform_scale_single(72)) < 195:
                logger.info(f"Offer Clay")
                common.click_matching("pictures/battle/offer_clay.png")
                common.wait_skip("pictures/events/continue.png")
                return 0

        logger.info(f"Using Sinner")
        common.click_matching("pictures/battle/offer_sinner.png")
        common.wait_skip("pictures/events/proceed.png")
        skill_check()
        return 0

    elif common.element_exist("pictures/battle/hug_bear.png"):
        logger.info(f"TEDDY BEAR")
        common.click_matching("pictures/battle/hug_bear.png")
        while(not common.element_exist("pictures/events/proceed.png")):
            common.sleep(0.5)
        common.click_matching("pictures/events/proceed.png")
        skill_check()
        return 0

    return 1

def skill_check():
    """Handles Skill checks in the game"""
    logger.info(f"Skill Check")
    check_images = [
        "pictures/events/very_high.png",
        "pictures/events/high.png",
        "pictures/events/normal.png",
        "pictures/events/low.png",
        "pictures/events/very_low.png"
        ] #Images for the skill check difficulties
    
    common.wait_skip("pictures/events/skill_check.png")
    common.sleep(1) #for the full list to render
    for i in check_images: #Choose the highest to pass check
        if common.element_exist(i,0.9):
            common.click_matching(i)
            logger.info(f"Selected Sinner for skill check")
            break

    common.click_matching("pictures/events/commence.png")
    common.sleep(3) #Waits for coin tosses
    logger.info(f"Coin tosses finished")
    common.mouse_move_click(common.scale_x(1193),common.scale_y(623))
    while(True):
        common.mouse_click()
        if common.element_exist("pictures/events/proceed.png"):
            common.click_matching("pictures/events/proceed.png")
            break
        if common.element_exist("pictures/events/continue.png"):
            common.click_matching("pictures/events/continue.png")
            break
        if common.element_exist("pictures/events/commence_battle.png"):
            common.click_matching("pictures/events/commence_battle.png")
            logger.info(f"Check Failed, Commencing Battle")
            return
    logger.info(f"Finished Skill check")

    if common.element_exist("pictures/events/skip.png"):
        if common.element_exist("pictures/events/skill_check.png"):#for retry scenarios
            logger.info(f"Failed Skill Check, Retrying")
            skill_check()
        if common.element_exist("pictures/battle/violet_hp.png"):
            logger.info(f"NOON OF VIOLET")
            common.wait_skip("pictures/battle/violet_hp.png")
            common.wait_skip("pictures/events/continue.png")

    else:
        common.sleep(1) #in the event of ego gifts
        if common.element_exist("pictures/mirror/general/ego_gift_get.png"):
            common.click_matching("pictures/general/confirm_b.png")
            logger.info(f"DEBUG: EGO Gift prompt")