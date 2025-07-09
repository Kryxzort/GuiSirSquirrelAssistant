
import sys
import os
import logging
import json

import common
import shared_vars
import mirror_utils
from core import (skill_check, battle_check, battle, check_loading, 
                  transition_loading, post_run_load)


def get_base_path():
    """Determine if running as executable or script and return base path."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        folder_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        return (os.path.dirname(folder_path) if os.path.basename(folder_path) == 'src' 
                else folder_path)


# Set base path
BASE_PATH = get_base_path()
sys.path.append(os.path.join(BASE_PATH, "src"))
os.chdir(BASE_PATH)

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

PACK_PRIORITY_JSON = os.path.join(BASE_PATH, "config", "pack_priority.json")
PACK_EXCEPTIONS_JSON = os.path.join(BASE_PATH, "config", "pack_exceptions.json")


class Mirror:
    def __init__(self, status):
        self.status = status
        self.logger = logging.getLogger(__name__)
        self.squad_order = self.set_sinner_order(status)
        self.aspect_ratio = common.get_aspect_ratio()
        self.res_x, self.res_y = common.get_resolution()
        self.squad_set = False

    @staticmethod
    def floor_id():
        """Returns what floor is currently on."""
        floor = ""
        if common.element_exist('pictures/mirror/packs/floor1.png', 0.9):
            floor = "floor1"
        elif common.element_exist('pictures/mirror/packs/floor2.png', 0.9):
            floor = "floor2"
        elif common.element_exist('pictures/mirror/packs/floor3.png', 0.9):
            floor = "floor3"
        elif common.element_exist('pictures/mirror/packs/floor4.png', 0.9):
            floor = "floor4"
        elif common.element_exist('pictures/mirror/packs/floor5.png', 0.9):
            floor = "floor5"
        return floor
        
    @staticmethod
    def set_sinner_order(status):
        """Gets the squad order for the team status."""
        if mirror_utils.squad_choice(status) is None:
            return common.squad_order("default")
        else:
            return common.squad_order(status)

    def setup_mirror(self):
        """Setting up the Mirror Dungeon Run."""
        while not common.element_exist("pictures/mirror/general/md_enter.png"):
            common.sleep(0.5)
        common.click_matching("pictures/mirror/general/md_enter.png")

        if common.element_exist("pictures/mirror/general/explore_reward.png"):
            if common.element_exist("pictures/mirror/general/clear.png"):
                common.click_matching("pictures/general/md_claim.png")
                if common.element_exist("pictures/general/confirm_w.png"):
                    common.click_matching("pictures/general/confirm_w.png")
                    while True:  # handles the weekly reward / bp pass prompts
                        if common.element_exist("pictures/mirror/general/weekly_reward.png"):
                            common.key_press("enter")
                        if common.element_exist("pictures/mirror/general/pass_level.png"):
                            common.key_press("enter")
                            #common.click_matching("pictures/general/confirm_b.png")
                            break
                    common.click_matching("pictures/general/cancel.png")
            else:
                common.click_matching("pictures/general/give_up.png")
                common.click_matching("pictures/general/cancel.png")

        if common.element_exist("pictures/general/resume.png"): #check if md is in progress
            common.click_matching("pictures/general/resume.png")
            check_loading()

        if common.element_exist("pictures/general/enter.png"): #Fresh run
            common.click_matching("pictures/general/enter.png")
            while(not common.element_exist("pictures/CustomAdded1080p/general/squads/squad_select.png")):
                common.sleep(0.5) 

        if common.element_exist("pictures/CustomAdded1080p/general/squads/squad_select.png"): #checks if in Squad select
            self.initial_squad_selection()

        if common.element_exist("pictures/CustomAdded1080p/mirror/general/grace_menu.png"): #checks if in grace menu
            self.grace_of_stars()

        if common.element_exist("pictures/mirror/general/gift_select.png"): #Checks if in gift select
            self.gift_selection()
    
    def check_run(self):
        """Checks if the run resulted in a loss or win"""
        run_complete = 0
        win_flag = 0
        if common.element_exist("pictures/general/defeat.png"):
            self.defeat()
            run_complete = 1
            #win_flag = 0

        if common.element_exist("pictures/general/victory.png"):
            self.victory()
            run_complete = 1
            win_flag = 1

        return win_flag,run_complete

    def mirror_loop(self):
        """Handles all the mirror dungeon logic in this"""
        if common.element_exist("pictures/general/maint.png"): #maintainance prompt
            common.click_matching("pictures/general/close.png")
            common.sleep(0.5)
            common.click_matching("pictures/general/no_op.png")
            common.click_matching("pictures/general/close.png")
            self.logger.critical("Server under maintenance")
            os._exit(0)

        if common.element_exist("pictures/events/skip.png"): #if hitting the events click skip to determine which is it
            common.mouse_move(200, 200)
            common.click_skip(4)
            self.event_choice()

        elif common.element_exist("pictures/mirror/general/danteh.png"): #checks if currently navigating
            self.navigation()

        elif common.element_exist("pictures/CustomAdded1080p/general/squads/clear_selection.png"): #checks if in squad select and then proceeds with battle
            self.squad_select()

        elif common.element_exist("pictures/mirror/restshop/shop.png"): #new combined shop and rest stop
            self.rest_shop()

        elif common.element_exist("pictures/mirror/general/ego_gift_get.png"): #handles the ego gift get
            common.click_matching("pictures/general/confirm_b.png") #might replace with enter

        elif common.element_exist("pictures/mirror/general/reward_select.png"): #checks if in reward select
            self.reward_select()

        elif common.element_exist("pictures/mirror/general/encounter_reward.png"): #checks if in encounter rewards
            self.encounter_reward_select()            

        elif common.element_exist("pictures/CustomAdded1080p/mirror/packs/inpack.png"): #checks if in pack select
            self.pack_selection()

        elif common.element_exist("pictures/battle/winrate.png"):
            battle()

        elif common.element_exist("pictures/mirror/general/event_effect.png"):
            found = common.match_image("pictures/mirror/general/event_select.png")
            x,y = common.random_choice(found)
            common.mouse_move_click(x, y)
            common.sleep(1)
            common.click_matching("pictures/general/confirm_b.png")

        return self.check_run()

    def grace_of_stars(self):
        """Selects grace of stars blessings for the runs"""
        graces = [(925, 890), (1300, 445), (1300, 890), (1675, 445), (550, 445)]  # Levels, Stats Up, Theme Packs, Cost+Gift, Generalist Gift
        for x, y in graces:
            common.mouse_move_click(common.scale_x(x), common.scale_y(y))
        common.click_matching("pictures/mirror/general/enter_b.png")
        common.sleep(1)
        common.click_matching("pictures/general/confirm_b.png")
        while(not common.element_exist("pictures/mirror/general/gift_select.png")): #Mitigate the weird freeze
            common.sleep(0.5)
    
    def gift_selection(self):
        """selects the ego gift of the same status, fallsback on random if not unlocked"""
        gift = mirror_utils.gift_choice(self.status)
        if not common.element_exist(gift,0.9): #Search for gift and if not present scroll to find it
            found = common.match_image("pictures/mirror/general/gift_select.png")
            x,y = found[0]
            common.mouse_move(x - common.scale_x(1365),y + common.scale_y(50))
            for i in range(5):
                common.mouse_scroll(-1000)

        found = common.match_image("pictures/mirror/general/gift_select.png")
        x,y = found[0]
        y = y + common.uniform_scale_single(235)
        if self.status == "sinking":
            initial_gift_coords = [y+common.uniform_scale_single(190), y+common.uniform_scale_single(190*2),y]
        else:
            initial_gift_coords = [y,y+common.uniform_scale_single(190), y+common.uniform_scale_single(190*2)]

        common.click_matching(gift,0.9) #click on specified
        for i in initial_gift_coords:
            common.mouse_move_click(common.uniform_scale_single(1640),i)
        common.key_press("enter")
        while not common.element_exist("pictures/mirror/general/ego_gift_get.png"):
            common.sleep(0.5)
        for i in range(3):
            if common.element_exist("pictures/mirror/general/ego_gift_get.png"): #handles the ego gift get
                common.key_press("enter")
                common.sleep(0.5)
        check_loading()

    def initial_squad_selection(self):
        """Searches for the squad name with the status type, if not found then uses the current squad"""
        status = mirror_utils.squad_choice(self.status)
        if status is None:
            common.key_press("enter")
            self.status = "poise"
            while(not common.element_exist("pictures/CustomAdded1080p/mirror/general/grace_menu.png")): #added check for default state
                common.sleep(0.5) #Transitional to Grace of Dreams
            return
        #This is to bring us to the first entry of teams
        found = common.match_image("pictures/CustomAdded1080p/general/squads/squad_select.png")
        x,y = found[0]
        common.mouse_move(x+common.uniform_scale_single(90),y+common.uniform_scale_single(90))
        for i in range(30):
            common.mouse_scroll(1000)
        common.sleep(1)
        #scrolls through all the squads in steps to look for the name
        for _ in range(4):
            if not common.element_exist(status):
                for i in range(7):
                    common.mouse_scroll(-1000)
                common.sleep(1)
                if common.element_exist(status):
                    common.click_matching(status)
                    break
                continue
            else:
                common.click_matching(status)
                break
        common.key_press("enter")
        while(not common.element_exist("pictures/CustomAdded1080p/mirror/general/grace_menu.png")):
            common.sleep(0.5) #Transitional to Grace of Dreams

    def pack_selection(self):
        """Prioritises the status gifts for packs if not follows a list"""
        status = mirror_utils.pack_choice(self.status) or "pictures/mirror/packs/status/poise_pack.png"
        floor = self.floor_id()
        if floor == "floor1":
            common.sleep(4)

        if common.element_exist("pictures/CustomAdded1080p/mirror/packs/floor_normal.png", 0.9):
            if common.element_exist("pictures/CustomAdded1080p/mirror/packs/normal_toggle.png", 0.9) and shared_vars.hard_mode: #Accounting for previous hard run and toggling back.
                common.click_matching("pictures/CustomAdded1080p/mirror/packs/normal_toggle.png", 0.9)
                floor = self.floor_id()

        elif common.element_exist("pictures/mirror/packs/floor_hard.png", 0.9): #accounts for cost additions or hard mode swap
            common.sleep(4) # the ego gift crediting blocks the refresh button
            if common.element_exist("pictures/mirror/packs/hard_toggle.png", 0.9) and not shared_vars.hard_mode: #Accounting for previous hard run and toggling back.
                common.click_matching("pictures/mirror/packs/hard_toggle.png", 0.9)
                floor = self.floor_id()

        common.mouse_move(200,200)
        common.sleep(2)
        if found := common.match_image("pictures/mirror/general/refresh.png", 0.9):
            x,y = found[0]
        refresh_flag = common.luminence(x,y) < 70 

        if self.exclusion_detection(floor) and not refresh_flag: #if pack exclusion detected and not refreshed
            common.click_matching("pictures/mirror/general/refresh.png", 0.9)
            common.mouse_move(200, 200)
            return self.pack_selection()

        elif self.exclusion_detection(floor) and refresh_flag:
            return self.pack_list(floor)
        
        elif shared_vars.prioritize_list_over_status and not self.exclusion_detection(floor) and floor != "floor5":
            if self.pack_list_has_matches(floor):
                return self.pack_list(floor)
            elif common.element_exist(status, 0.9):
                return self.choose_pack(status)
            else:
                return self.pack_list(floor)

        elif common.element_exist(status, 0.9) and not self.exclusion_detection(floor) and floor != "floor5":
            return self.choose_pack(status)

        else:
            return self.pack_list(floor)

    def pack_list_has_matches(self, floor, threshold=0.9):
        """Check if pack list has any matches without selecting them"""
        try:
            if os.path.exists(PACK_PRIORITY_JSON):
                with open(PACK_PRIORITY_JSON, "r") as f:
                    priority_data = json.load(f)
                    
                exceptions = []
                if os.path.exists(PACK_EXCEPTIONS_JSON):
                    with open(PACK_EXCEPTIONS_JSON, "r") as f:
                        exceptions_data = json.load(f)
                        exceptions = exceptions_data.get(floor, [])
                
                floor_priorities = priority_data.get(floor, {})
                sorted_packs = sorted(floor_priorities.items(), key=lambda x: x[1])
                packs = [pack for pack, _ in sorted_packs if pack not in exceptions]
                
                for pack in packs:
                    floor_num = floor[-1]
                    image_floor = f"f{floor_num}"
                    pack_image = f"pictures/mirror/packs/{image_floor}/{pack}.png"
                    if common.element_exist(pack_image, threshold):
                        return True
                        
        except Exception as e:
            self.logger.warning(f"Error checking pack list matches: {e}")
        
        return False

    def pack_list(self, floor, threshold=0.9):
        """Select packs based on priority files"""
        # Load from JSON files
        try:
            # Get priority packs from JSON
            if os.path.exists(PACK_PRIORITY_JSON):
                with open(PACK_PRIORITY_JSON, "r") as f:
                    priority_data = json.load(f)
                    
                # Get exceptions from JSON
                exceptions = []
                if os.path.exists(PACK_EXCEPTIONS_JSON):
                    with open(PACK_EXCEPTIONS_JSON, "r") as f:
                        exceptions_data = json.load(f)
                        exceptions = exceptions_data.get(floor, [])
                
                # Get priority order for this floor
                floor_priorities = priority_data.get(floor, {})
                
                # Sort by priority (ascending)
                sorted_packs = sorted(floor_priorities.items(), key=lambda x: x[1])
                
                # Remove exceptions
                packs = [pack for pack, _ in sorted_packs if pack not in exceptions]
                
                # Try to find each pack in order
                for pack in packs:
                    # Convert floor name format for image path (floor1 -> f1)
                    floor_num = floor[-1]
                    image_floor = f"f{floor_num}"
                    pack_image = f"pictures/mirror/packs/{image_floor}/{pack}.png"
                    if common.element_exist(pack_image, threshold):
                        return self.choose_pack(pack_image, threshold)
            
        except Exception as e:
            self.logger.warning(f"Error using pack priority files: {e}, picking first available")
        
        self.logger.warning(f"No packs found in priority system, picking first available")
        for found_pack in common.match_image("pictures/CustomAdded1080p/mirror/packs/inpack.png"):
            x, y = found_pack
            x + -300
            y2 = y + 500
            common.mouse_move(common.scale_x_1080p(x), common.scale_y_1080p(y))
            common.mouse_drag(common.scale_x_1080p(x), common.scale_y_1080p(y2))
            return

    def choose_pack(self, pack_image, threshold=0.9):
        found = common.match_image(pack_image, threshold)
        if pack_image == "pictures/mirror/packs/status/pierce_pack.png":
            found = [x for x in found if x[1] > common.scale_y(1092)] #Removes poor detections
        owned_found = common.ifexist_match("pictures/mirror/packs/status/owned.png", 0.9)
        if owned_found:
            owned_check = common.proximity_check(found,owned_found,50)
            if owned_check:
                if len(found) > len(owned_check):
                    for i in owned_check:
                        found.remove(i)
        x,y = common.random_choice(found)
        common.mouse_move(x,y-common.uniform_scale_single(350))
        common.mouse_drag(x,y)
        transition_loading()
        return

    def exclusion_detection(self, floor):
        """Detects an excluded pack using exception files"""
        detected = 0
        try:
            # Try to load exceptions from JSON file
            if os.path.exists(PACK_EXCEPTIONS_JSON):
                with open(PACK_EXCEPTIONS_JSON, "r") as f:
                    exceptions_data = json.load(f)
                    exceptions = exceptions_data.get(floor, [])
                
                # Check if any exception packs are present
                if exceptions:
                    # Convert floor name format for image path (floor1 -> f1)
                    floor_num = floor[-1]
                    image_floor = f"f{floor_num}"
                    exclusion = [f"pictures/mirror/packs/{image_floor}/{pack}.png" for pack in exceptions]
                    detected = any(common.element_exist(i, 0.9) for i in exclusion)
                    return int(detected)
        except Exception as e:
            self.logger.warning(f"Error loading pack exceptions: {e}")
        
        # Try the old method as fallback
        try:
            floor_num = floor[-1]
            exception_path = os.path.join(BASE_PATH, "config", f"pack_exceptions_f{floor_num}.txt")
            if os.path.exists(exception_path):
                with open(exception_path, "r") as f:
                    exceptions = [line.strip() for line in f.readlines() if line.strip()]
                
                # Check if any exception packs are present
                if exceptions:
                    exclusion = [f"pictures/mirror/packs/f{floor_num}/{pack}.png" for pack in exceptions]
                    detected = any(common.element_exist(i, 0.9) for i in exclusion)
                    return int(detected)
        except Exception as e:
            self.logger.warning(f"Error loading old pack exceptions: {e}")
        
        # Return 0 if no exceptions file or empty file
        return 0

    def squad_select(self):
        """selects sinners in squad order"""
        if not self.squad_set or not common.element_exist("pictures/CustomAdded1080p/general/squads/full_squad.png"):
            common.click_matching("pictures/CustomAdded1080p/general/squads/clear_selection.png")
            if common.element_exist("pictures/general/confirm_w.png"):
                common.click_matching("pictures/general/confirm_w.png")
            for i in self.squad_order: #click squad members according to the order in the json file
                x,y = i
                common.mouse_move_click(x, y)
            self.squad_set = True
        common.mouse_move_click(common.scale_x_1080p(1722), common.scale_y_1080p(881))
        while(not common.element_exist("pictures/battle/winrate.png")): #because squad select will always transition to battle
            common.sleep(0.5)
        battle()

    def reward_select(self):
        """Selecting EGO Gift rewards"""
        status_effect = mirror_utils.reward_choice(self.status)
        if status_effect is None:
            status_effect = "pictures/mirror/rewards/poise_reward.png"
        if not common.element_exist(status_effect,0.85):
            while not common.element_exist("pictures/mirror/general/reward_select.png"):
                common.mouse_move_click(200, 200)
                common.sleep(0.5)
            found = common.match_image("pictures/mirror/general/reward_select.png")
            x,y = common.random_choice(found)
            common.mouse_move_click(x, y)
            common.mouse_move(200, 200)
        else:
            found = common.match_image(status_effect,0.85)
            x,y = common.random_choice(found)
            common.mouse_move_click(x, y)

        #common.click_matching("pictures/mirror/general/confirm_gift.png")
        common.key_press("enter")
        common.sleep(1)
        #common.click_matching("pictures/general/confirm_b.png")
        
        common.key_press("enter")

    def encounter_reward_select(self):
        """Select Encounter Rewards prioritising starlight first"""
        encounter_reward = ["pictures/mirror/encounter_reward/cost_gift.png",
                            "pictures/mirror/encounter_reward/cost.png",
                            "pictures/mirror/encounter_reward/gift.png",
                            "pictures/mirror/encounter_reward/resource.png"]
        common.sleep(0.5)
        for rewards in encounter_reward:
            if common.element_exist(rewards):
                common.click_matching(rewards)
                common.click_matching("pictures/general/confirm_b.png")
                common.sleep(1)
                if common.element_exist("pictures/mirror/encounter_reward/prompt.png"):
                    common.click_matching("pictures/CustomAdded1080p/mirror/general/BorderedConfirm.png")
                    break
                if common.element_exist("pictures/mirror/general/ego_gift_get.png"): #handles the ego gift get
                    common.click_matching("pictures/general/confirm_b.png")
                break
        common.sleep(3) #needs to wait for the gain to credits

    def check_nodes(self,nodes):
        non_exist = [1,1,1]
        top = common.greyscale_match_image("pictures/mirror/general/node_1.png",0.75)
        top_alt = common.greyscale_match_image("pictures/mirror/general/node_1_o.png",0.75)
        middle = common.greyscale_match_image("pictures/mirror/general/node_2.png",0.75)
        middle_alt = common.greyscale_match_image("pictures/mirror/general/node_2_o.png",0.75)
        bottom = common.greyscale_match_image("pictures/mirror/general/node_3_o.png",0.75)
        bottom_alt = common.greyscale_match_image("pictures/mirror/general/node_3.png",0.75)
        if not top and not top_alt:
            non_exist[0] = 0
        if not middle and not middle_alt:
            non_exist[1] = 0
        if not bottom and not bottom_alt:
            non_exist[2] = 0
        nodes = [y for y, exists in zip(nodes, non_exist) if exists != 0]
        return nodes

    def navigation(self):
        """Core navigation function to reach the end of floor"""
        #Checks incase continuing quitted out MD
        common.click_matching("pictures/mirror/general/danteh.png")
        if common.element_exist("pictures/mirror/general/nav_enter.png"):
            common.click_matching("pictures/mirror/general/nav_enter.png")
        else:
        #Find which node is the traversable one
            node_location = []
            if self.aspect_ratio == "16:10": #Oddly the old coordinates work for 16:10 but 16:9/4:3 need new ones
                node_y = [189,607,1036] #for 16/10
            else:
                node_y = [263,689,1115] #for 4/3 16/9
            
            #Checking for which direction on the nodes and removing those that dont exist
            node_y = self.check_nodes(node_y)

            for y in node_y:
                if self.aspect_ratio == "4:3":
                    node_location.append((common.uniform_scale_single(1440),common.uniform_scale_single(y) + common.uniform_scale_single(105)))
                else:
                    node_location.append((common.uniform_scale_single(1440),common.uniform_scale_single(y)))
#           
            if self.aspect_ratio == "16:9": #Drag because 16:9 blocks the top view of the cost
                common.mouse_move(200, 200)
                if found := common.match_image("pictures/mirror/general/danteh.png"):
                    x,y = found[0]
                    common.mouse_move(x,y)
                    common.mouse_drag(x,y+common.scale_y(100))

            combat_nodes = common.match_image("pictures/mirror/general/cost.png")
 #Combat detected nodes
            combat_nodes = [x for x in combat_nodes if x[0] > common.scale_x(1280) and x[0] < common.scale_x(1601)]
 #filter only for next nodes
            combat_nodes_locs = common.proximity_check_fuse(node_location, combat_nodes,100, common.scale_y(200))
            node_location = [i for i in node_location if i not in list(combat_nodes_locs)]
            node_location = node_location + list(combat_nodes_locs)

            while(not common.element_exist("pictures/mirror/general/nav_enter.png")):
                if common.element_exist("pictures/general/defeat.png") or common.element_exist("pictures/general/victory.png"):
                    return
                for x,y in node_location:
                    common.mouse_move_click(x, y)
                    common.sleep(1)
                    if common.element_exist("pictures/mirror/general/nav_enter.png"):
                        break
                    else: #Added new might break some stuff idk NEW CODE HERE
                        self.navigation()
                        return
            common.click_matching("pictures/mirror/general/nav_enter.png")

    def sell_gifts(self):
        """Handles Selling gifts"""
        for _ in range(3):
            common.sleep(1)
            if common.element_exist("pictures/mirror/restshop/market/vestige_2.png"):
                common.click_matching("pictures/mirror/restshop/market/vestige_2.png")
                common.click_matching("pictures/mirror/restshop/market/sell_b.png")
                common.click_matching("pictures/general/confirm_w.png")

            if common.element_exist("pictures/mirror/restshop/scroll_bar.png"):
                common.click_matching("pictures/mirror/restshop/scroll_bar.png")
                for k in range(5):
                    common.mouse_scroll(-1000)
    
    def fuse(self):
        common.click_matching("pictures/mirror/restshop/fusion/fuse_b.png")
        if common.element_exist("pictures/CustomAdded1080p/mirror/general/cannot_fuse.png"):
            common.mouse_move(50, 50)
            return False
        common.click_matching("pictures/general/confirm_b.png")
        while(not common.element_exist("pictures/mirror/general/ego_gift_get.png")): #in the event of slow connection
            common.sleep(0.5)
        common.key_press("enter")
        return True

    def find_gifts(self, statuses):
        fusion_gifts = []
        
        vestige_coords = common.ifexist_match("pictures/mirror/restshop/market/vestige_2.png")
        if vestige_coords:
            fusion_gifts += vestige_coords
            # Store vestige coords for later identification
            self.vestige_coords = vestige_coords
        else:
            self.vestige_coords = None
            
        for i in statuses:
            status = mirror_utils.get_status_gift_template(i)
            
            # Use higher threshold for pierce since somehow the ++ icons on upgraded gifts were detected as pierce?!?!?
            if i == 'pierce':
                threshold = 0.79
            else:
                threshold = 0.75

            # Similarly, it can mistake circular part of left side fusion UI as slash icon
            if i == 'slash':
                threshold = 0.79
            else:
                threshold = 0.75
            
            status_coords = common.ifexist_match(status, threshold)
            if status_coords:
                fusion_gifts += status_coords
            else:
                pass
        
        # Remove duplicate coordinates
        original_count = len(fusion_gifts)
        fusion_gifts = list(dict.fromkeys(fusion_gifts))
        if original_count != len(fusion_gifts):
            pass
        
        # Filter out status detections that are inside exception gift areas
        fusion_gifts = self.filter_exception_gifts(fusion_gifts)
        
        return [x for x in fusion_gifts if x[0] > common.scale_x(1235) and x[1] < common.scale_y(800)] #this is to remove the left side and bottom area 
    
    def filter_exception_gifts(self, fusion_gifts):
        """Remove status detections that are inside exception gift areas"""
        if not fusion_gifts:
            return fusion_gifts
        
        exception_gifts = self.load_fusion_exceptions()
        if not exception_gifts:
            return fusion_gifts
        
        # Find all exception gift bounding boxes once (optimized approach)
        all_exception_boxes = []
        for gift_img in exception_gifts:
            boxes = common.ifexist_match(gift_img, 0.9, area="all")
            if boxes:
                all_exception_boxes.extend(boxes)
        
        if not all_exception_boxes:
            return fusion_gifts
        
        # Use enhanced_proximity_check with bounding box mode for exception filtering
        inside_exception = common.enhanced_proximity_check(all_exception_boxes, fusion_gifts,
                                                          use_bounding_box=True, return_bool=False)
        
        # Filter out gifts that are inside exception areas
        filtered_gifts = [gift for gift in fusion_gifts if gift not in inside_exception]
        
        return filtered_gifts
    
    def load_fusion_exceptions(self):
        """Load fusion exceptions from JSON config file"""
        fusion_exceptions_path = os.path.join(BASE_PATH, "config", "fusion_exceptions.json")
        exception_gifts = []
        
        try:
            if os.path.exists(fusion_exceptions_path):
                with open(fusion_exceptions_path, 'r') as f:
                    exceptions_data = json.load(f)
                
                # Only support list format: ["gift_name1", "gift_name2"]
                if isinstance(exceptions_data, list):
                    for name in exceptions_data:
                        image_path = f"pictures/CustomFuse/{name}.png"
                        exception_gifts.append(image_path)
                else:
                    self.logger.warning(f"FUSION: Expected list format, got {type(exceptions_data)}. Use format: [\"gift_name1\", \"gift_name2\"]")
                        
        except Exception as e:
            self.logger.warning(f"Error loading fusion exceptions: {e}")
        
        if exception_gifts:
            pass
        else:
            pass
            
        return exception_gifts
    
    def fuse_gifts(self):

        def exit_fusion():
            if common.element_exist("pictures/mirror/restshop/close.png"):
                common.click_matching("pictures/mirror/restshop/fusion/forecasts.png")
                common.click_matching("pictures/mirror/restshop/close.png")
            else:
                common.sleep(5)
                if common.element_exist("pictures/mirror/restshop/close.png"):
                    common.click_matching("pictures/mirror/restshop/close.png")

        # Check if we should fuse EGO gifts
        if shared_vars.skip_ego_fusion:
            return

        statuses = ["burn","bleed","tremor","rupture","sinking","poise","charge","slash","pierce","blunt"] #List of status to use
        statuses.remove(self.status)
        common.click_matching("pictures/mirror/restshop/fusion/fuse.png")
        common.sleep(1.5)
        if not common.element_exist("pictures/mirror/restshop/fusion/fuse_menu.png"):
            return
        common.mouse_move_click(common.scale_x(730), common.scale_y(700))
        status_picture = mirror_utils.get_fusion_target_button(self.status)
        common.click_matching(status_picture)
        common.click_matching("pictures/general/confirm_b.png")
        common.click_matching("pictures/mirror/restshop/fusion/bytier.png")
        common.click_matching("pictures/mirror/restshop/fusion/bykeyword.png")

        if common.element_exist("pictures/mirror/restshop/scroll_bar.png"): #if scroll bar present scrolls to the start
            common.click_matching("pictures/mirror/restshop/scroll_bar.png")
            for i in range(5):
                common.mouse_scroll(1000)
            common.sleep(0.5)

        while(True):
            fusion_gifts = self.find_gifts(statuses)
            
            if len(fusion_gifts) >= 3:
                click_count = 0
                for x,y in fusion_gifts:
                    common.mouse_move_click(x, y)
                    common.click_matching("pictures/mirror/restshop/fusion/forecasts.png")
                    click_count += 1
                    if click_count == 3:
                        if not self.fuse():
                            exit_fusion()
                            return
                        click_count = 0
                        break

            elif len(fusion_gifts) > 0 and common.element_exist("pictures/mirror/restshop/scroll_bar.png"):
                click_count = 0
                for x,y in fusion_gifts:
                    common.mouse_move_click(x, y)
                    common.click_matching("pictures/mirror/restshop/fusion/forecasts.png")
                    click_count += 1
                common.click_matching("pictures/mirror/restshop/scroll_bar.png")
                for i in range(5):
                    common.mouse_scroll(-1000)
                common.sleep(0.5)
                fusion_gifts_scroll = self.find_gifts(statuses)
                duplicates = common.proximity_check_fuse(fusion_gifts_scroll,fusion_gifts,10,common.scale_y(348))
                for i in duplicates:
                    fusion_gifts_scroll.remove(i)
                if (len(fusion_gifts_scroll) + click_count) >= 3:
                    for x,y in fusion_gifts_scroll:
                        common.mouse_move_click(x, y)
                        common.click_matching("pictures/mirror/restshop/fusion/forecasts.png")
                        click_count += 1
                        if click_count == 3:
                            if not self.fuse():
                                exit_fusion()
                                return
                            click_count = 0
                            break
                else:
                    break
            else:
                break
        
        exit_fusion()
                
    def rest_shop(self):
        # Check if we should skip restshop
        if shared_vars.skip_restshop:
                # LEAVING
            common.click_matching("pictures/mirror/restshop/leave.png")
            if not common.element_exist("pictures/general/confirm_w.png"):
                common.mouse_move_click(50,50)
                common.click_matching("pictures/mirror/restshop/leave.png")
            common.click_matching("pictures/general/confirm_w.png")
            if common.element_exist("pictures/general/confirm_b.png"):
                common.click_matching("pictures/general/confirm_b.png")
            return
            
        # Flow should be Fuse > Heal > Enhance > Buy since cost is scarce and stronger gifts is better

        # FUSING
        self.fuse_gifts()
        # Check for insufficient cost to exit
        if common.element_exist("pictures/mirror/restshop/small_not.png"):
            common.click_matching("pictures/mirror/restshop/leave.png")
            if not common.element_exist("pictures/general/confirm_w.png"):
                common.mouse_move_click(50,50)
                common.click_matching("pictures/mirror/restshop/leave.png")
            common.click_matching("pictures/general/confirm_w.png") 
            
        else:
            # HEALING
            if not common.click_matching("pictures/mirror/restshop/heal.png", recursive=False):
                if common.element_exist("pictures/mirror/restshop/small_not.png"):
                    common.click_matching("pictures/mirror/restshop/leave.png")
                    if not common.element_exist("pictures/general/confirm_w.png"):
                        common.mouse_move_click(50,50)
                        common.click_matching("pictures/mirror/restshop/leave.png")
                    common.click_matching("pictures/general/confirm_w.png") 
                    return

            common.click_matching("pictures/mirror/restshop/heal_all.png")
            common.sleep(1)
            common.click_matching("pictures/mirror/restshop/return.png")

            # ENHANCING
            status = mirror_utils.get_status_gift_template(self.status)
            if status is None:
                status = "pictures/mirror/restshop/enhance/poise_enhance.png"
            common.click_matching("pictures/mirror/restshop/enhance/enhance.png")
            if common.element_exist("pictures/mirror/restshop/scroll_bar.png"): # if scroll bar present scrolls to the start
                common.click_matching("pictures/mirror/restshop/scroll_bar.png")
                for i in range(5):
                    common.mouse_scroll(1000)
            self.enhance_gifts(status)
            if common.element_exist("pictures/mirror/restshop/close.png"):
                common.click_matching("pictures/mirror/restshop/close.png")

            # BUYING
            status = mirror_utils.market_choice(self.status)
            if status is None:
                status = "pictures/mirror/restshop/market/poise_market.png"
            for _ in range(3):
                market_gifts = []
                if common.element_exist(status):
                    market_gifts += common.match_image(status)
                # keywordless gifts
                wordless_matches = common.ifexist_match("pictures/mirror/restshop/market/wordless.png")
                if wordless_matches:
                    # Filters in the event of the skill replacement being detected
                    wordless_gifts = [x for x in wordless_matches if not (abs(x[0] - common.scale_x(1300)) <= 10 and abs(x[1] - common.scale_y(541)) <= 10)] 
                    market_gifts += wordless_gifts
                if len(market_gifts):
                    market_gifts = [x for x in market_gifts if (x[0] > common.scale_x(1091) and x[0] < common.scale_x(2322)) and (x[1] > common.scale_y(434) and x[1] < common.scale_y(919))] # filter within purchase area
                    for x,y in market_gifts:
                        # x,y = i
                        if common.luminence(x+common.scale_x(25),y+common.scale_y(1)) < 2: # this area will have a value of less than or equal to 5 if purchased
                            continue
                        if common.element_exist("pictures/mirror/restshop/small_not.png"):
                            break
                        common.mouse_move_click(x, y)
                        if common.element_exist("pictures/mirror/restshop/market/replace.png"): # handle skill replacement opening
                            common.click_matching("pictures/mirror/restshop/enhance/cancel.png")
                        if common.element_exist("pictures/mirror/restshop/market/purchase.png"): # purchase button will appear if purchasable
                            common.click_matching("pictures/mirror/restshop/market/purchase.png")
                            common.click_matching("pictures/general/confirm_b.png")

                if common.element_exist("pictures/mirror/restshop/small_not.png"):
                    break

                if _ != 2:
                    common.mouse_move_click(50, 50)
                    common.sleep(1)
                    common.click_matching("pictures/mirror/restshop/market/refresh.png")

        # LEAVING
        common.click_matching("pictures/mirror/restshop/leave.png")
        if not common.element_exist("pictures/general/confirm_w.png"):
            common.mouse_move_click(50,50)
            common.click_matching("pictures/mirror/restshop/leave.png")
        common.click_matching("pictures/general/confirm_w.png")
        if common.element_exist("pictures/general/confirm_b.png"):
            common.click_matching("pictures/general/confirm_b.png")
        return

    def upgrade(self,gifts,status,shift_x,shift_y):
        for x,y in gifts:
            common.mouse_move_click(x, y)
            for _ in range(2): #upgrading twice
                common.click_matching("pictures/mirror/restshop/enhance/power_up.png")
                if common.element_exist("pictures/mirror/restshop/enhance/more.png"): #If player has no more cost exit
                    common.click_matching("pictures/mirror/restshop/enhance/cancel.png")
                    common.sleep(1)
                    common.mouse_click()
                    return
                elif common.element_exist("pictures/mirror/restshop/enhance/confirm.png"):
                    common.click_matching("pictures/mirror/restshop/enhance/confirm.png")

    def enhance_gifts(self,status):
        """Enhancement gift process"""
        while(True):
            gifts = common.ifexist_match(status)
            if gifts:
                shift_x, shift_y = mirror_utils.enhance_shift(self.status) or (12, -41)
                gifts = [i for i in gifts if i[0] > common.scale_x(1200)] #remove false positives on the left side
                gifts = [i for i in gifts if common.luminence(i[0]+common.uniform_scale_single(shift_x),i[1]+common.uniform_scale_single(shift_y)) > 21]
                # Find all fully_upgraded coordinates once, then filter gifts using those coordinates
                fully_upgraded_coords = common.ifexist_match("pictures/mirror/restshop/enhance/fully_upgraded.png", 0.7)
                if fully_upgraded_coords:
                    # Use enhanced_proximity_check with fixed area mode (115px left and above each gift)
                    gifts = [gift for gift in gifts if not common.enhanced_proximity_check([gift], 
                                                                                         fully_upgraded_coords, 
                                                                                         expand_left=115, expand_above=115,
                                                                                         use_bounding_box=False, return_bool=True)]
                if len(gifts):
                    self.upgrade(gifts,status,shift_x,shift_y)

            wordless_gifts = common.ifexist_match("pictures/mirror/restshop/enhance/wordless_enhance.png")
            if wordless_gifts:
                shift_x, shift_y = mirror_utils.enhance_shift("wordless")
                wordless_gifts = [i for i in wordless_gifts if common.luminence(i[0]+common.uniform_scale_single(shift_x),i[1]+common.uniform_scale_single(shift_y)) > 22]
                if len(wordless_gifts):
                    self.upgrade(wordless_gifts,"pictures/mirror/restshop/enhance/wordless_enhance.png",shift_x,shift_y)

            # TODO
            # original if statement was
            # if common.element_exist("pictures/mirror/restshop/scroll_bar.png") and not common.element_exist("pictures/mirror/restshop/scroll_bar_up.png") and not common.element_exist("pictures/CustomAdded1080p/mirror/general/fully_scrolled.png"):
            # but scroll_bar_up.png was missing and crashing, no idea what it is actually supposed to be, plz add
            if common.element_exist("pictures/mirror/restshop/scroll_bar.png") and not common.element_exist("pictures/CustomAdded1080p/mirror/general/fully_scrolled.png"):
                common.click_matching("pictures/mirror/restshop/scroll_bar.png")
                for k in range(5):
                    common.mouse_scroll(-1000)

            if not gifts:
                break
            

    def event_choice(self):
        common.sleep(1)
        if common.element_exist("pictures/events/level_up.png"):
            common.click_matching("pictures/events/level_up.png")
            common.wait_skip("pictures/events/proceed.png")
            skill_check()

        elif common.element_exist("pictures/events/select_gain.png"): #Select to gain EGO Gift
            common.click_matching("pictures/events/select_gain.png")
            common.mouse_move_click(common.scale_x(1193),common.scale_y(623))
            while(True):
                common.mouse_click()
                if common.element_exist("pictures/events/proceed.png"):
                    common.click_matching("pictures/events/proceed.png")
                    break
                if common.element_exist("pictures/events/continue.png"):
                    common.click_matching("pictures/events/continue.png")
                    break
            common.sleep(1)
            if common.element_exist("pictures/mirror/general/ego_gift_get.png"): #handles the ego gift get
                #common.click_matching("pictures/general/confirm_b.png")
                common.key_press("enter")

        elif common.element_exist("pictures/events/gain_check.png"): #Pass to gain an EGO Gift
            common.click_matching("pictures/events/gain_check.png")
            common.wait_skip("pictures/events/proceed.png")
            skill_check()

        elif common.element_exist("pictures/events/gain_check_o.png"): #Pass to gain an EGO Gift
            common.click_matching("pictures/events/gain_check_o.png")
            common.wait_skip("pictures/events/proceed.png")
            skill_check()

        elif common.element_exist("pictures/events/gain_gift.png"): #Proceed to gain
            common.click_matching("pictures/events/gain_gift.png")
            common.wait_skip("pictures/events/proceed.png")
            if common.element_exist("pictures/events/skip.png"):
                common.click_skip(4)
                self.event_choice()

        elif common.element_exist("pictures/events/select_right.png"): #select the right answer
            if common.element_exist("pictures/events/helterfly.png"):
                common.click_matching("pictures/events/helterfly.png")
            elif common.element_exist("pictures/events/midwinter.png"):
                common.click_matching("pictures/events/midwinter.png")
            common.mouse_move_click(common.scale_x(1193),common.scale_y(623))
            while(True):
                common.mouse_click()
                if common.element_exist("pictures/events/proceed.png"):
                    common.click_matching("pictures/events/proceed.png")
                    break
                if common.element_exist("pictures/events/continue.png"):
                    common.click_matching("pictures/events/continue.png")
                    break
            common.sleep(1)
            if common.element_exist("pictures/mirror/general/ego_gift_get.png"): #handles the ego gift get
                #common.click_matching("pictures/general/confirm_b.png")
                common.key_press("enter")

        elif common.element_exist("pictures/events/win_battle.png"): #Win battle to gain
            common.click_matching("pictures/events/win_battle.png")
            common.wait_skip("pictures/events/commence_battle.png")
        
        elif common.element_exist("pictures/events/skill_check.png"): #Skill Check
            skill_check()

        elif common.element_exist("pictures/mirror/events/kqe.png"): #KQE Event
            common.click_matching("pictures/mirror/events/kqe.png")
            common.wait_skip("pictures/events/continue.png")
            if common.element_exist("pictures/mirror/general/ego_gift_get.png"): #handles the ego gift get
                common.click_matching("pictures/general/confirm_b.png")
        
        elif common.element_exist("pictures/CustomAdded1080p/mirror/events/slot_machine.png"): #Slot machine event
            common.click_matching("pictures/CustomAdded1080p/mirror/events/slot_machine.png")

        elif common.element_exist("pictures/events/proceed.png"):# in the event of it getting stuck
            common.click_matching("pictures/events/proceed.png")

        elif common.element_exist("pictures/events/continue.png"):
            common.click_matching("pictures/events/continue.png")

        elif not battle_check():
            battle()

    def victory(self):
        if common.element_exist("pictures/general/confirm_w.png"):
            common.click_matching("pictures/general/confirm_w.png")
        common.click_matching("pictures/general/beeg_confirm.png")
        common.mouse_move(200,200)
        common.click_matching("pictures/general/claim_rewards.png")
        common.sleep(1)
        common.click_matching("pictures/general/md_claim.png")
        common.sleep(0.5)
        if common.element_exist("pictures/general/confirm_w.png"):
            common.click_matching("pictures/general/confirm_w.png")
            while(True):
                if common.element_exist("pictures/mirror/general/weekly_reward.png"): #Weekly Prompt
                    common.key_press("enter")
                if common.element_exist("pictures/mirror/general/pass_level.png"): #BP Promptw
                    common.key_press("enter")
                    break
            post_run_load()
        else: #incase not enough modules
            common.click_matching("pictures/general/to_window.png")
            common.click_matching("pictures/general/confirm_w.png")
            post_run_load()
            self.logger.error("Insufficient modules")
            os._exit(0)

    def defeat(self):
        if common.element_exist("pictures/general/confirm_w.png"):
            common.click_matching("pictures/general/confirm_w.png")
        common.click_matching("pictures/general/beeg_confirm.png")
        common.mouse_move(200,200)
        common.click_matching("pictures/general/claim_rewards.png")
        common.sleep(1)
        common.click_matching("pictures/general/give_up.png")
        common.click_matching("pictures/general/confirm_w.png")
        post_run_load()
