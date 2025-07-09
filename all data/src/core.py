import sys
import os
import time
import logging
from sys import exit

import pyautogui

import common
import shared_vars


def get_base_path():
    """Determine if running as executable or script and return base path."""
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

screen_width, screen_height = pyautogui.size()

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
    """Converts to Module (Runs from the main menu)."""
    if common.click_matching("pictures/general/module.png"):
        if not common.click_matching("pictures/general/right_arrow.png", recursive=False):
            while common.element_exist("pictures/CustomAdded1080p/general/goback.png"):
                common.click_matching("pictures/CustomAdded1080p/general/goback.png")
            common.click_matching("pictures/general/right_arrow.png")
        common.click_matching("pictures/general/confirm_w.png")
        common.click_matching("pictures/general/cancel.png")
        return True
    elif common.element_exist("pictures/CustomAdded1080p/mirror/general/InMirrorSelectCheck.png"):
        return False

def navigate_to_md():
    """Navigates to the Mirror Dungeon from the menu."""
    if common.click_matching("pictures/CustomAdded1080p/mirror/general/button_to_md_tab.png", recursive=False):
       common.mouse_move(200, 200)
       if common.element_exist("pictures/mirror/general/md_enter.png"):
            return

    while not common.element_exist("pictures/general/MD.png"):
        while common.element_exist("pictures/CustomAdded1080p/general/goback.png"):
            common.click_matching("pictures/CustomAdded1080p/general/goback.png")
        common.click_matching("pictures/general/window.png")
        common.click_matching("pictures/general/drive.png")
    common.click_matching("pictures/general/MD.png")

def pre_md_setup():
    if refill_enkephalin():
        navigate_to_md()
        return True
    return False

def check_loading():
    """Handles the loading screen transitions"""
    common.sleep(2) #Handles fade to black
    while(common.element_exist("pictures/general/loading.png")): #checks for loading screen bar
        common.sleep(0.5) #handles the remaining loading

def transition_loading():
    """Theres a load that occurs while transitioning to the next floor"""
    common.sleep(5)

def post_run_load():
    """There is some oddity in the loading time for this that makes it annoying to measure so this is a blanket wait for main menu stall"""
    while(not common.element_exist("pictures/general/module.png")):
        common.sleep(1)

def reconnect():
    while(common.element_exist("pictures/general/server_error.png")):
        if shared_vars.reconnect_when_internet_reachable:
            if common.check_internet_connection():
                common.click_matching("pictures/general/retry.png")
                common.mouse_move(200,200)
            else:
                common.sleep(1)
        else:
            common.sleep(shared_vars.reconnection_delay)
            common.click_matching("pictures/general/retry.png")
            common.mouse_move(200,200)
    if common.element_exist("pictures/general/no_op.png"):
        common.click_matching("pictures/general/close.png")
        logger.info(f"COULD NOT RECONNECT TO THE SERVER. SHUTTING DOWN!")
        os._exit(0)

def battle():
    """Handles battles by mashing winrate, also handles skill checks and end of battle loading"""
    battle_finished = 0
    winrate_visible_start = None
    winrate_timeout = 5
    winrate_invisible_start = None
    winrate_invisible_timeout = 10
    
    while(battle_finished != 1):
        if common.element_exist("pictures/general/server_error.png"):
            common.mouse_up()
            reconnect()

        if common.element_exist("pictures/general/loading.png") and not common.element_exist("pictures/CustomAdded1080p/battle/setting_cog.png"): #Checks for loading screen to end the while loop
            common.mouse_up()
            if common.element_exist("pictures/battle/winrate.png"):
                logger.info("false read loading")
                battle()
                return

            battle_finished = 1
            logger.info(f"Battle finished!")
            common.sleep(3)
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
                winrate_visible_start = None
                logger.warning(f"Winrate screen stuck for {winrate_timeout} seconds")
                common.mouse_up()
                common.click_matching("pictures/battle/winrate.png", 0.9)
                ego_check()
                common.key_press("enter")
            else:
                # Normal winrate handling
                common.mouse_up()
                common.key_press("p")
                # on slower machine, it can take a little bit for winrate to go through
                common.sleep(0.5)
                ego_check()
                common.key_press("enter")
                common.mouse_down()
                time.sleep(1)
                if not common.element_exist("pictures/CustomAdded1080p/battle/battle_in_progress.png"):
                    common.mouse_move_click(common.scale_x_1080p(20), common.scale_y_1080p(20))

        else: # Check if winrate hasn't been visible for too long and battle might have ended or winrate might be covered
            if common.element_exist("pictures/mirror/general/encounter_reward.png"): #checks for a special button in the mirror select menu to stop the battle.
                battle_finished = 1
                logger.info(f"battle ended, in mirror")
                return
            
            winrate_visible_start = None
            current_time = time.time()
            if winrate_invisible_start is None:
                winrate_invisible_start = current_time
            
            elif current_time - winrate_invisible_start > winrate_invisible_timeout:
                winrate_invisible_start = None
                logger.warning(f"No winrate for {winrate_invisible_timeout} seconds")
                common.mouse_up()
                common.mouse_move_click(common.scale_x_1080p(20), common.scale_y_1080p(20))

def ego_check():
    """Checks for hopeless/struggling clashes and uses E.G.O if possible"""
    # Check if we should skip ego selection
    if shared_vars.skip_ego_check:
        return
        
    bad_clashes = []
    hopeless_matches = common.ifexist_match("pictures/battle/ego/hopeless.png",0.79, no_grayscale=True)
    if hopeless_matches:
        bad_clashes += hopeless_matches
        
    struggling_matches = common.ifexist_match("pictures/battle/ego/struggling.png",0.79, no_grayscale=True)
    if struggling_matches:
        bad_clashes += struggling_matches
    
    bad_clashes = [i for i in bad_clashes if i]
    if len(bad_clashes):
        bad_clashes = [x for x in bad_clashes if x[1] > common.scale_y(1023)] # this is to remove any false positives
        for x,y in bad_clashes:
            usable_ego = []
            common.mouse_move(x-common.scale_x(55),y+common.scale_y(100))
            common.mouse_hold()
            egos = common.match_image("pictures/battle/ego/sanity.png")
            for i in egos:
                x,y = i
                if common.luminence(x,y) > 100:#Sanity icon
                    usable_ego.append(i)
            if len(usable_ego):
                ego = common.random_choice(usable_ego)
                x,y = ego
                if common.element_exist("pictures/battle/ego/sanity.png"):
                    common.mouse_move_click(x + common.scale_x(30), y+common.scale_y(30))
                    common.sleep(0.3)
                    common.mouse_click()
                    common.sleep(1)
            else:
                if common.element_exist("pictures/battle/ego/sanity.png"):
                    common.mouse_move_click(200,200)
                    common.sleep(1)
        common.key_press("p") #Change to Damage
        common.sleep(0.5)
        common.key_press("p") #Deselects
        common.sleep(0.5)
        common.key_press("p") #Back to winrate
        common.sleep(0.5)
    return
    
def battle_check(): #pink shoes, woppily, doomsday clock
    common.sleep(1)
    if common.element_exist("pictures/battle/investigate.png"): #Woppily
        common.click_matching("pictures/battle/investigate.png")
        common.wait_skip("pictures/events/continue.png")
        return 0
        
    elif common.element_exist("pictures/battle/NO.png"): #Woppily
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
        common.click_matching("pictures/battle/refuse.png")
        common.wait_skip("pictures/events/proceed.png")
        skill_check()
        return 0
    
    elif common.element_exist("pictures/battle/shield_passive.png"): #Hohenheim
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
        found = common.match_image("pictures/battle/offer_clay.png")
        if found:
            x,y = found[0]
            if common.luminence(x,y-common.uniform_scale_single(72)) < 195:
                common.click_matching("pictures/battle/offer_clay.png")
                common.wait_skip("pictures/events/continue.png")
                return 0

        common.click_matching("pictures/battle/offer_sinner.png")
        common.wait_skip("pictures/events/proceed.png")
        skill_check()
        return 0

    elif common.element_exist("pictures/battle/hug_bear.png"):
        common.click_matching("pictures/battle/hug_bear.png")
        while(not common.element_exist("pictures/events/proceed.png")):
            common.sleep(0.5)
        common.click_matching("pictures/events/proceed.png")
        skill_check()
        return 0

    return 1

def skill_check():
    """Handles Skill checks in the game"""
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
            break

    common.click_matching("pictures/events/commence.png")
    common.sleep(3) #Waits for coin tosses
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
            return

    if common.element_exist("pictures/events/skip.png"):
        if common.element_exist("pictures/events/skill_check.png"):#for retry scenarios
            skill_check()
        if common.element_exist("pictures/battle/violet_hp.png"):
            common.wait_skip("pictures/battle/violet_hp.png")
            common.wait_skip("pictures/events/continue.png")

    else:
        common.sleep(1) #in the event of ego gifts
        if common.element_exist("pictures/mirror/general/ego_gift_get.png"):
            common.click_matching("pictures/general/confirm_b.png")
