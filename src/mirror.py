from src import common, mirror_utils, core
import logging
import os
    
class Mirror:
    def __init__(self, status):
        self.logger = logging.getLogger(__name__)
        self.status = status
        self.squad_order = self.set_sinner_order(status)
        self.squad_set = False
        self.aspect_ratio = common.get_aspect_ratio()

    @staticmethod
    def set_sinner_order(status):
        """Gets the squad order for the corrosponding status"""
        if mirror_utils.squad_choice(status) is None:
            return core.squad_order("default")
        else:
            return core.squad_order(status)
        
    @staticmethod
    def floor_id():
        """Returns what floor is currently on"""
        floor = ""
        if common.match_image('pictures/mirror/packs/floor1.png',0.9):
            floor = "f1"
        elif common.match_image('pictures/mirror/packs/floor2.png',0.9):
            floor = "f2"
        elif common.match_image('pictures/mirror/packs/floor3.png',0.9):
            floor = "f3"
        elif common.match_image('pictures/mirror/packs/floor4.png',0.9):
            floor = "f4"
        elif common.match_image('pictures/mirror/packs/floor5.png',0.9):
            floor = "f5"
        return floor
    
    #Pre MD Loop Functions
    def initial_squad_selection(self):
        """Searches for the squad name with the status type, if not found then uses the current squad"""
        self.logger.info("Mirror Dungeon Squad Select")
        status = mirror_utils.squad_choice(self.status)
        if status is None:
            self.logger.info("Invalid Status - defaulting to poise")
            common.key_press("enter")
            self.status = "poise"
            while(not common.match_image("pictures/mirror/grace/grace_menu.png")): #added check for default state
                common.sleep(0.5) #Transitional to Grace of Dreams
            return
        common.sleep(1)
        if match := common.match_image(status): #checks if current team is in view and click if so
            common.click_matching_coords(match)
        else:
            #This is to bring us to the first entry of teams
            match = common.match_image("pictures/mirror/general/squad_select.png")
            x,y = common.random_choice(match)
            common.mouse_move(x+common.uniform_scale_single(90),y+common.uniform_scale_single(90))
            for i in range(30):
                common.mouse_scroll(1000)
            common.sleep(1) # Let the scrolling animation finish

            #scrolls through all the squads in steps to look for the name
            for _ in range(4):
                if not common.match_image(status):
                    for i in range(7):
                        common.mouse_scroll(-1000)
                    common.sleep(1)
                    if match := common.match_image(status):
                        common.click_matching_coords(match)
                        break
                    continue
                else:
                    common.click_matching(status)
                    break

        common.key_press("enter")
        while(not common.match_image("pictures/mirror/grace/grace_menu.png")):
            common.sleep(0.5) #Transitioning to Grace of Dreams

    def grace_of_stars(self):
        """Selects grace of stars blessings for the runs"""
        self.logger.info("Grace of Stars")
        graces = [(925,890),(1300,890),(1300,445),(1675,445),(550,445)] #Levels, Stats Up, Theme Packs, Cost+Gift, Generalist Gift
        for x,y in graces:
            common.mouse_move_click(common.scale_x(x),common.scale_y(y))
        common.click_matching("pictures/mirror/general/enter_b.png")
        common.sleep(1)
        common.click_matching("pictures/general/confirm_b.png")
        while(not common.match_image("pictures/mirror/general/gift_select.png")): #Mitigate the weird freeze
            common.sleep(0.5)
    
    def gift_selection(self):
        """selects the ego gift of the same status, fallsback on random if not unlocked"""
        self.logger.info("E.G.O Gift Selection")
        gift = mirror_utils.gift_choice(self.status)
        if not common.match_image(gift,0.9): #Search for gift and if not present scroll to find it
            found = common.match_image("pictures/mirror/general/gift_select.png")
            x,y = common.random_choice(found)
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
        while (not common.match_image("pictures/mirror/general/ego_gift_get.png")): #handles the ego gift get
            common.sleep(0.1)
        common.key_press("enter")
        core.delay_load(1.5)
        
    def setup(self):
        while(not common.match_image("pictures/mirror/general/md_enter.png")):
            common.sleep(0.5)
        common.click_matching("pictures/mirror/general/md_enter.png")

        if match := common.match_image("pictures/general/enter.png"): #Fresh run
            common.click_matching_coords(match)
            self.logger.info("Starting Run")
            while(not common.match_image("pictures/mirror/general/squad_select.png")):
                common.sleep(0.5) 

        elif match := common.match_image("pictures/general/resume.png"): #check if md is in progress
            common.click_matching_coords(match)
            self.logger.info("Resuming Run")
            core.delay_load(2)
            
        elif common.match_image("pictures/mirror/general/explore_reward.png"):
            self.logger.info("Completed Run Detected")
            if common.match_image("pictures/mirror/general/clear.png"): # Checks if Run is Won
                self.logger.info("Run Won")
                common.click_matching("pictures/general/md_claim.png")
                if match := common.match_image("pictures/general/confirm_w.png"):
                    self.logger.info("Rewards Claimed")
                    common.click_matching_coords(match)
                    while(True): #handles the weekly reward / bp pass prompts
                        if common.match_image("pictures/mirror/general/weekly_reward.png"):
                            self.logger.debug("Weekly / Event Reward Prompt")
                            common.key_press("enter")
                        if common.match_image("pictures/mirror/general/pass_level.png"):
                            self.logger.debug("BP PROMPT")
                            common.key_press("enter")
                            break
                    common.click_matching("pictures/general/cancel.png")
            else:
                self.logger.info("Run Lost, Giving Up")
                common.click_matching("pictures/general/give_up.png")
                common.click_matching("pictures/general/cancel.png")

        if common.match_image("pictures/mirror/general/squad_select.png"): #checks if in initial squad select
            self.initial_squad_selection()

        if common.match_image("pictures/mirror/grace/grace_menu.png"): #checks if in grace menu
            self.grace_of_stars()

        if common.match_image("pictures/mirror/general/gift_select.png"): #Checks if in gift select
            self.gift_selection()

    #Pack Related Functions
    def exclusion_detection(self,floor):
        """Detects an excluded pack"""
        detected = False
        if floor == "f1" or floor == "f2" or floor == "f3":
            return detected
        if floor == "f4":
            exclusion = ["pictures/mirror/packs/f4/wrath.png",
                       "pictures/mirror/packs/f4/crawling.png",
                       "pictures/mirror/packs/f4/violet.png",
                       "pictures/mirror/packs/f4/lust.png"]
        if floor == "f5":
            exclusion = ["pictures/mirror/packs/f5/crawling.png",
                         "pictures/mirror/packs/f5/wrath.png",
                         "pictures/mirror/packs/f5/lust.png"]
            
        detected = any(common.match_image(i) for i in exclusion) #use 0.75 if current has issues
        return detected

    def pack_list(self,floor, threshold=0.8):
        with open("config/" + floor + ".txt", "r") as f:
            packs = [i.strip() for i in f.readlines()] #uses the f1,f2,f3,f4 txts for floor order
        for i in packs:
            self.choose_pack(i, threshold)

    def choose_pack(self,pack_image, threshold=0.8):
        if not common.match_image(pack_image):
            return
        else:
            found = common.match_image(pack_image,threshold)
            if "status" in pack_image: #ownership filtering should only be done for statuses
                self.logger.debug(found)
                if pack_image == "pictures/mirror/packs/status/pierce_pack.png":
                    found = [x for x in found if x[1] > common.scale_y(1092)] #Removes pierce misdetection on hard toggle
                if match := common.match_image("pictures/mirror/packs/status/owned.png"):
                    #owned_found = common.match_image("pictures/mirror/packs/status/owned.png")
                    owned_check = common.proximity_check(found,match,50)
                    if owned_check:
                        if len(found) > len(owned_check):
                            self.logger.info("Found Owned Gifts in Pack rewards - filtering")
                            for i in owned_check:
                                found.remove(i)
            x,y = common.random_choice(found)
            common.mouse_move(x,y-common.uniform_scale_single(350))
            common.mouse_drag(x,y)
            core.floor_transition_loading()
            return

    def pack_selection(self):
        """Prioritises the status gifts if not follows a list"""
        self.logger.info("Pack Selection")
        status = mirror_utils.pack_choice(self.status) or "pictures/mirror/packs/status/poise_pack.png"
        floor = self.floor_id()
        self.logger.info("Current Floor "+ floor)

        if floor == "f1": #handles all the reward prompts 
            common.sleep(4)

        if common.match_image("pictures/mirror/packs/floor_hard.png"): #accounts for cost additions or hard mode swap
            common.sleep(4) # the ego gift crediting blocks the refresh button
            if match := common.match_image("pictures/mirror/packs/hard_toggle.png"): #Accounting for previous hard run and toggling back.
                self.logger.info("Hard Mode was previously ran, reverting to Normal")
                common.click_matching_coords(match)
                self.logger.info("Toggled from Hard")
                floor = self.floor_id()
                self.logger.debug("Current Floor "+ floor)

        common.mouse_move(200,200)
        common.sleep(2)
        if found := common.match_image("pictures/mirror/general/refresh.png"):
            x,y = common.random_choice(found)
        
        refresh_flag = common.luminence(x,y) < 70 

        if self.exclusion_detection(floor) and not refresh_flag: #if pack exclusion detected and not refreshed
            self.logger.info("Pack exclusion detected, refreshing")
            common.click_matching("pictures/mirror/general/refresh.png")
            common.mouse_move(200,200)
            return self.pack_selection()

        elif common.match_image(status) and not self.exclusion_detection(floor) and floor != "f5": #if pack exclusion absent and status exists and not Floor 5
            self.logger.info("Pack exclusion not detected, status detected, choosing from status")
            return self.choose_pack(status)
        
        elif self.exclusion_detection(floor) and refresh_flag: #if pack exclusion detected and refreshed
            self.logger.info("Pack exclusion detected and refreshed, choosing from packlist")
            return self.pack_list(floor)

        else:
            self.logger.info("PACKS: using pack list")
            return self.pack_list(floor)
        
    def squad_select(self):
        """Selects sinners in squad order"""
        self.logger.info("Selecting Squad for Battle")
        if not self.squad_set or not common.match_image("pictures/squads/full_squad.png"): #This is so that we dont need to reset every time
            common.click_matching("pictures/battle/clear.png")
            if match := common.match_image("pictures/general/confirm_w.png"):
                common.click_matching_coords(match)
            for x,y in self.squad_order: #click squad members according to the order in the json file
                common.mouse_move_click(x,y)
            self.squad_set = True
        common.click_matching("pictures/squads/squad_select.png")
        while(not common.match_image("pictures/battle/winrate.png")): #because squad select will always transition to battle
            common.sleep(0.5)
        core.battle()

    def reward_select(self):
        """Selecting EGO Gift rewards"""
        self.logger.info("Reward Selection")
        status_effect = mirror_utils.reward_choice(self.status)
        if status_effect is None:
            status_effect = "pictures/mirror/rewards/poise_reward.png"
        if match := common.match_image(status_effect,0.85):
            self.logger.info("Reward Selection: Status found")
            common.click_matching_coords(match)
        else:
            self.logger.info("Reward Selection: Status found")
            common.click_matching("pictures/mirror/general/reward_select.png")

        common.key_press("enter")
        while (not common.match_image("pictures/mirror/general/ego_gift_get.png")): #handles the ego gift get
            common.sleep(0.5)
        common.key_press("enter")

    def encounter_reward_select(self):
        """Select Encounter Rewards prioritising starlight first"""
        self.logger.info("Encounter Reward Selection")
        encounter_reward = ["pictures/mirror/encounter_reward/cost_gift.png",
                            "pictures/mirror/encounter_reward/cost.png",
                            "pictures/mirror/encounter_reward/gift.png",
                            "pictures/mirror/encounter_reward/resource.png"]
        common.sleep(0.5)
        for rewards in encounter_reward:
            if match := common.match_image(rewards):
                common.click_matching_coords(match)
                common.click_matching("pictures/general/confirm_b.png")
                common.sleep(1)
                if common.match_image("pictures/mirror/encounter_reward/prompt.png"):
                    common.key_press("enter")
                    break
                if common.match_image("pictures/mirror/general/ego_gift_get.png"): #handles the ego gift get
                    common.click_matching("pictures/general/confirm_b.png")
                break
        common.sleep(3) #needs to wait for the gain to credits

    def check_nodes(self,nodes):
        non_exist = [1,1,1]
        top = common.greyscale_match_image("pictures/mirror/general/node_1.png")
        middle = common.greyscale_match_image("pictures/mirror/general/node_2.png")
        bottom = common.greyscale_match_image("pictures/mirror/general/node_3.png")
        if not top:
            non_exist[0] = 0
        if not middle:
            non_exist[1] = 0
        if not bottom:
            non_exist[2] = 0
        nodes = [y for y, exists in zip(nodes, non_exist) if exists != 0]
        return nodes

    def navigation(self):
        """Core navigation function to reach the end of floor"""
        self.logger.info("Navigating")
        #Checks incase continuing quitted out MD
        common.click_matching("pictures/mirror/general/danteh.png")
        if match := common.match_image("pictures/mirror/general/nav_enter.png"):
            common.click_matching_coords(match)
            #common.key_press("enter")

        elif match := common.match_image("pictures/mirror/general/boss_node.png"):
            common.click_matching_coords(match)
            while (not common.match_image("pictures/mirror/general/nav_enter.png")):
                common.sleep(0.5)
            #common.click_matching("pictures/mirror/general/nav_enter.png")
            common.key_press("enter")
        else:
            #Find which node is the traversable one
            node_location = []
            if self.aspect_ratio == "16:10":
                node_y = [189,607,1036] #for 16/10
            else:
                node_y = [263,689,1115] #for 4/3 16/9
            
            #Checking for which direction on the nodes and removing those that dont exist
            node_y = self.check_nodes(node_y)
            self.logger.debug("Checking for Node Paths")

            if len(node_y) == 0:
                raise RuntimeError (f"Ran into an error finding paths, Try Rerunning")

            for y in node_y:
                if self.aspect_ratio == "4:3":
                    node_location.append((common.uniform_scale_single(1440),common.uniform_scale_single(y) + common.uniform_scale_single(105)))
                else:
                    node_location.append((common.uniform_scale_single(1440),common.uniform_scale_single(y)))
#           
            if self.aspect_ratio == "16:9": #Drag because 16:9 blocks the top view of the cost
                common.mouse_move(200,200)
                if found := common.match_image("pictures/mirror/general/danteh.png"):
                    x,y = common.random_choice(found)
                    common.mouse_move(x,y)
                    common.mouse_drag(x,y+common.scale_y(100))

            #Prioritising Non Combat Nodes and moving combat nodes to lower indexs - [NON,COMBAT,COMBAT]
            combat_nodes = common.match_image("pictures/mirror/general/cost.png")
            combat_nodes = [x for x in combat_nodes if x[0] > common.scale_x(1280) and x[0] < common.scale_x(1601)]
            combat_nodes_locs = common.proximity_check_fuse(node_location, combat_nodes,100, common.scale_y(200))
            node_location = [i for i in node_location if i not in list(combat_nodes_locs)]
            node_location = node_location + list(combat_nodes_locs)

            #Mitigation for softlock on final battle
            while(not common.match_image("pictures/mirror/general/nav_enter.png")):
                if common.match_image("pictures/general/defeat.png") or common.match_image("pictures/general/victory.png"):
                    self.logger.debug("Detected Victory screen")
                    return
                for x,y in node_location:
                    common.mouse_move_click(x,y)
                    common.sleep(1)
                    if match := common.match_image("pictures/mirror/general/nav_enter.png"):
                        common.click_matching_coords(match)
                        return
    
    def fuse(self):
        common.click_matching("pictures/mirror/restshop/fusion/fuse_b.png")
        common.click_matching("pictures/general/confirm_b.png")
        while(not common.match_image("pictures/mirror/general/ego_gift_get.png")): #in the event of slow connection
            common.sleep(0.5)
        common.key_press("enter")
        self.logger.info("FUSED GIFT")

    def find_gifts(self, statuses):
        self.logger.info("FUSION: Finding Gifts")
        fusion_gifts = []
        if match := common.match_image("pictures/mirror/restshop/market/vestige_2.png"):
            self.logger.info("FUSION: Found Vestige(s)")
            fusion_gifts += match
        for i in statuses:
            status = mirror_utils.enhance_gift_choice(i)
            if match := common.match_image(status):
                self.logger.info("FUSION: Found Status Gift(s)")
                fusion_gifts += match
        
        return [x for x in fusion_gifts if x[0] > common.scale_x(1235)] #this is to remove the left side 
    
    def fuse_gifts(self):
        statuses = ["burn","bleed","tremor","rupture","sinking","poise","charge","slash","pierce","blunt"] #List of status to use
        statuses.remove(self.status)
        self.logger.info("Starting Fusion")
        common.click_matching("pictures/mirror/restshop/fusion/fuse.png")
        common.sleep(2)
        if not common.match_image("pictures/mirror/restshop/fusion/fuse_menu.png"):
            self.logger.info("FUSION: Not Enough Gifts for Fusion")
            return
        common.mouse_move_click(common.scale_x(730),common.scale_y(700))
        status_picture = mirror_utils.fusion_choice(self.status)
        while not common.match_image("pictures/mirror/restshop/fusion/keyword_menu.png"):
            common.sleep(0.5)
        common.click_matching(status_picture)
        common.click_matching("pictures/general/confirm_b.png")
        self.logger.info("FUSION: Sorting Gifts")
        common.click_matching("pictures/mirror/restshop/fusion/bytier.png")
        common.click_matching("pictures/mirror/restshop/fusion/bykeyword.png")

        if match := common.match_image("pictures/mirror/restshop/scroll_bar.png"): #if scroll bar present scrolls to the start
            common.click_matching_coords(match)
            for i in range(5):
                common.mouse_scroll(1000)
            common.sleep(0.5)

        while(True):
            fusion_gifts = self.find_gifts(statuses)
            if len(fusion_gifts) >= 3:
                self.logger.info("FUSION: Found 3 Gifts to fuse")
                click_count = 0
                for x,y in fusion_gifts:
                    common.mouse_move_click(x,y)
                    common.click_matching("pictures/mirror/restshop/fusion/forecasts.png")
                    click_count += 1
                    if click_count == 3:
                        self.fuse()
                        click_count = 0
                        break

            elif len(fusion_gifts) > 0 and common.match_image("pictures/mirror/restshop/scroll_bar.png"):
                self.logger.info("FUSION: Found 1-2 Gifts to fuse, checking for more")
                click_count = 0
                for x,y in fusion_gifts:
                    common.mouse_move_click(x,y)
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
                        common.mouse_move_click(x,y)
                        common.click_matching("pictures/mirror/restshop/fusion/forecasts.png")
                        click_count += 1
                        if click_count == 3:
                            self.fuse()
                            click_count = 0
                            break
                else:
                    self.logger.info("FUSION: Did not find 3 Gifts to fuse after scrolling")
                    break
            else:
                self.logger.info("FUSION: Did not find 3 Gifts to fuse")
                break

        common.click_matching("pictures/mirror/restshop/close.png")
        self.logger.info("Exiting Fusion")

    def rest_shop(self):
        #Flow should be Fuse > Heal > Enhance > Buy since cost is scarce and stronger gifts is better
        self.logger.info("Restshop")

        #FUSING
        self.fuse_gifts()
        #Check for insufficient cost to exit
        if common.match_image("pictures/mirror/restshop/small_not.png"):
            self.logger.info("Restshop: Not enough Cost, Exiting")
            common.click_matching("pictures/mirror/restshop/leave.png")
            if not common.match_image("pictures/general/confirm_w.png"):
                common.mouse_move_click(50,50)
                common.click_matching("pictures/mirror/restshop/leave.png")
            common.click_matching("pictures/general/confirm_w.png") 
            
        else:
            #HEALING
            self.logger.info("Restshop: Check if healing is needed")
            common.click_matching("pictures/mirror/restshop/heal.png")
            common.click_matching("pictures/mirror/restshop/heal_all.png")
            self.logger.info("Restshop: Healed all sinners")
            while(common.match_image("pictures/mirror/restshop/return.png")): #This is apparently an issue with the return button in MD being not responsive
                common.click_matching("pictures/mirror/restshop/return.png")
                common.mouse_move(200,200)
                common.sleep(0.5)

            #ENHANCING
            status = mirror_utils.enhance_gift_choice(self.status)
            if status is None:
                status = "pictures/mirror/restshop/enhance/poise_enhance.png"
            common.click_matching("pictures/mirror/restshop/enhance/enhance.png")
            self.logger.info("Restshop: Enhancing E.G.O Gifts")
            if match := common.match_image("pictures/mirror/restshop/scroll_bar.png"): #if scroll bar present scrolls to the start
                common.click_matching_coords(match)
                for i in range(5):
                    common.mouse_scroll(1000)
            self.enhance_gifts(status)

            #BUYING
            self.logger.info("Restshop: Purchasing Gifts")
            status = mirror_utils.market_choice(self.status)
            if status is None:
                status = "pictures/mirror/restshop/market/poise_market.png"
            for _ in range(3):
                market_gifts = []
                if match := common.match_image(status):
                    self.logger.info("Restshop: Found Status Gift")
                    market_gifts += match
                #keywordless gifts
                if match := common.match_image("pictures/mirror/restshop/market/wordless.png"):
                    self.logger.debug("Restshop: Found Keywordless Gifts")
                    #Filters in the event of the skill replacement being detected
                    wordless_gifts = [x for x in match if not (abs(x[0] - common.scale_x(1300)) <= 10 and abs(x[1] - common.scale_y(541)) <= 10)] 
                    market_gifts += wordless_gifts

                if len(market_gifts):
                    market_gifts = [x for x in market_gifts if (x[0] > common.scale_x(1091) and x[0] < common.scale_x(2322)) and (x[1] > common.scale_y(434) and x[1] < common.scale_y(919))] #filter within purchase area
                    for x,y in market_gifts:
                        self.logger.debug(common.luminence(x+common.scale_x(25),y+common.scale_y(1)))
                        if common.luminence(x+common.scale_x(25),y+common.scale_y(1)) < 2: #this area will have a value of less than or equal to 5 if purchased
                            continue
                        if common.match_image("pictures/mirror/restshop/small_not.png"):
                            self.logger.info("Restshop: Not enough cost, exiting restshop")
                            break
                        common.mouse_move_click(x,y)
                        if common.match_image("pictures/mirror/restshop/market/replace.png"): #handle skill replacement opening
                            self.logger.debug("Restshop: Skill Replacement Page Reached")
                            common.click_matching("pictures/mirror/restshop/enhance/cancel.png")
                        if match := common.match_image("pictures/mirror/restshop/market/purchase.png"): #purchase button will appear if purchasable
                            self.logger.info("Restshop: Purchased E.G.O Gift")
                            common.click_matching_coords(match)
                            common.click_matching("pictures/general/confirm_b.png")

                if common.match_image("pictures/mirror/restshop/small_not.png"):
                    break

                if _ != 2:
                    common.click_matching("pictures/mirror/restshop/market/refresh.png")
                    self.logger.debug("Restshop: Refreshing Shop")

        #LEAVING
        common.click_matching("pictures/mirror/restshop/leave.png")
        if not common.match_image("pictures/general/confirm_w.png"):
            common.mouse_move_click(50,50)
            common.click_matching("pictures/mirror/restshop/leave.png")
        common.click_matching("pictures/general/confirm_w.png")
        return

    def upgrade(self,gifts):
        for x,y in gifts:
            common.mouse_move_click(x,y)
            for _ in range(2): #upgrading twice
                if common.match_image("pictures/mirror/restshop/enhance/fully_upgraded.png"): #if fully upgraded skip this item
                    break
                common.click_matching("pictures/mirror/restshop/enhance/power_up.png")
                if common.match_image("pictures/mirror/restshop/enhance/more.png"): #If player has no more cost exit
                    self.logger.info("Restshop: Not enough cost, exiting enhancement")
                    common.click_matching("pictures/mirror/restshop/enhance/cancel.png")
                    common.sleep(1)
                    common.mouse_click()
                    return
                elif match := common.match_image("pictures/mirror/restshop/enhance/confirm.png"):
                    self.logger.debug("Restshop: E.G.O status gift upgraded")
                    common.click_matching_coords(match)
                    common.sleep(1)

    def enhance_gifts(self,status):
        """Enhancement gift process"""
        while(True):
            gifts = []
            if common.match_image(status):
                shift_x, shift_y = mirror_utils.enhance_shift(self.status) or (12, -41)
                gifts = common.match_image(status)
                gifts = [i for i in gifts if i[0] > common.scale_x(1200)] #remove false positives on the left side
                gifts = [i for i in gifts if common.luminence(i[0]+common.uniform_scale_single(shift_x),i[1]+common.uniform_scale_single(shift_y)) > 21]
                if len(gifts):
                    self.upgrade(gifts)
                self.logger.debug(gifts)

            if match := common.match_image("pictures/mirror/restshop/enhance/wordless_enhance.png"):
                shift_x, shift_y = mirror_utils.enhance_shift("wordless")
                gifts = [i for i in match if common.luminence(i[0]+common.uniform_scale_single(shift_x),i[1]+common.uniform_scale_single(shift_y)) > 21]
                if len(gifts):
                    self.upgrade(gifts)
                self.logger.debug(gifts)

            if match := common.match_image("pictures/mirror/restshop/scroll_bar.png"):
                common.click_matching_coords(match)
                for k in range(5):
                    common.mouse_scroll(-1000)
                common.sleep(1)

            if not gifts:
                break
        
        if match:= common.match_image("pictures/mirror/restshop/close.png"):
            self.logger.info("Restshop: Finished Enhancing Gifts")
            common.click_matching_coords(match)
        

    def event_choice(self):
        self.logger.info("Event")
        common.sleep(1)
        if match:= common.match_image("pictures/events/level_up.png"):
            self.logger.info("Pass to Level Up")
            common.click_matching_coords(match)
            common.wait_skip("pictures/events/proceed.png")
            core.skill_check()

        elif match := common.match_image("pictures/events/select_gain.png"): #Select to gain EGO Gift
            self.logger.info("Select to gain EGO Gift")
            common.click_matching_coords(match)
            common.mouse_move_click(common.scale_x(1193),common.scale_y(623))
            while(True):
                common.mouse_click()
                if match := common.match_image("pictures/events/proceed.png"):
                    common.click_matching_coords(match)
                    break
                if match := common.match_image("pictures/events/continue.png"):
                    common.click_matching_coords(match)
                    break
            common.sleep(1)
            if common.match_image("pictures/mirror/general/ego_gift_get.png"): #handles the ego gift get
                #common.click_matching("pictures/general/confirm_b.png")
                common.key_press("enter")

        elif match:= common.match_image("pictures/events/gain_check.png"): #Pass to gain an EGO Gift
            self.logger.info("Pass to gain EGO Gift")
            common.click_matching_coords(match)
            common.wait_skip("pictures/events/proceed.png")
            core.skill_check()

        elif match := common.match_image("pictures/events/gain_check_o.png"): #Pass to gain an EGO Gift
            self.logger.info("Pass to gain EGO Gift")
            common.click_matching_coords(match)
            common.wait_skip("pictures/events/proceed.png")
            core.skill_check()

        elif match := common.match_image("pictures/events/gain_gift.png"): #Proceed to gain
            self.logger.info("Proceed to gain EGO Gift")
            common.click_matching_coords(match)
            common.wait_skip("pictures/events/proceed.png")
            if common.match_image("pictures/events/skip.png"):
                common.click_skip(4)
                self.event_choice()

        elif common.match_image("pictures/events/select_right.png"): #select the right answer
            self.logger.info("Select the right answer")
            if match := common.match_image("pictures/events/helterfly.png"):
                common.click_matching_coords(match)
            elif match := common.match_image("pictures/events/midwinter.png"):
                common.click_matching_coords(match)
            common.mouse_move_click(common.scale_x(1193),common.scale_y(623))
            while(True):
                common.mouse_click()
                if match := common.match_image("pictures/events/proceed.png"):
                    common.click_matching_coords(match)
                    break
                if match := common.match_image("pictures/events/continue.png"):
                    common.click_matching_coords(match)
                    break
            common.sleep(1)
            if common.match_image("pictures/mirror/general/ego_gift_get.png"): #handles the ego gift get
                #common.click_matching("pictures/general/confirm_b.png")
                common.key_press("enter")

        elif match := common.match_image("pictures/events/win_battle.png"): #Win battle to gain
            self.logger.info("Win battle to gain EGO Gift")
            common.click_matching_coords(match)
            common.wait_skip("pictures/events/commence_battle.png")
        
        elif common.match_image("pictures/events/skill_check.png"): #Skill Check
            core.skill_check()

        elif match := common.match_image("pictures/mirror/events/kqe.png"): #KQE Event
            self.logger.info("KQE")
            common.click_matching_coords(match)
            common.wait_skip("pictures/events/continue.png")
            if common.match_image("pictures/mirror/general/ego_gift_get.png"): #handles the ego gift get
                common.click_matching("pictures/general/confirm_b.png")

        elif match := common.match_image("pictures/events/proceed.png"):# in the event of it getting stuck
            common.click_matching_coords(match)

        elif match := common.match_image("pictures/events/continue.png"):
            common.click_matching_coords(match)

    def victory(self):
        self.logger.info("Run Won")
        if match := common.match_image("pictures/general/confirm_w.png"):
            self.logger.info("Manager Level Up")
            common.click_matching_coords(match)
        common.click_matching("pictures/general/beeg_confirm.png")
        common.mouse_move(200,200)
        common.click_matching("pictures/general/claim_rewards.png")
        common.click_matching("pictures/general/md_claim.png")
        common.sleep(0.5)
        if match := common.match_image("pictures/general/confirm_w.png"):
            self.logger.info("Rewards Claimed")
            common.click_matching_coords(match)
            while(True):
                if common.match_image("pictures/mirror/general/weekly_reward.png"): #Weekly Prompt
                    self.logger.info("Weekly / Event Reward Prompt")
                    common.key_press("enter")
                if common.match_image("pictures/mirror/general/pass_level.png"): #BP Promptw
                    self.logger.info("BP PROMPT")
                    common.key_press("enter")
                    #common.click_matching("pictures/general/confirm_b.png")
                    break
            core.post_run_load()
        else: #incase not enough modules
            common.click_matching("pictures/general/to_window.png")
            common.click_matching("pictures/general/confirm_w.png")
            core.post_run_load()
            self.logger.info("You dont have enough modules to continue")
            os._exit(0)

    def defeat(self):
        self.logger.info("Run Lost")
        if match := common.match_image("pictures/general/confirm_w.png"):
            self.logger.info("Manager Level Up")
            common.click_matching_coords(match)
        common.click_matching("pictures/general/beeg_confirm.png")
        common.mouse_move(200,200)
        common.click_matching("pictures/general/claim_rewards.png")
        common.click_matching("pictures/general/give_up.png")
        common.click_matching("pictures/general/confirm_w.png")
        core.post_run_load()

    def check_run(self):
        """Checks if the run resulted in a loss or win"""
        run_complete = False
        if common.match_image("pictures/general/defeat.png"):
            self.defeat()
            run_complete = True

        if common.match_image("pictures/general/victory.png"):
            self.victory()
            run_complete = True

        return run_complete

    def mirror_loop(self):
        """Handles all the mirror dungeon logic in this"""
        if common.match_image("pictures/general/maint.png"): #maintainance prompt
            common.click_matching("pictures/general/close.png")
            common.sleep(0.5)
            common.click_matching("pictures/general/no_op.png")
            common.click_matching("pictures/general/close.png")
            self.logger.info("SERVER UNDERGOING MAINTAINANCE, BOT WILL STOP NOW!")
            os._exit(0)

        if common.match_image("pictures/events/skip.png"): #if hitting the events click skip to determine which is it
            self.logger.info("Entered ? node")
            common.mouse_move(200,200)
            common.click_skip(4)
            self.event_choice()

        elif common.match_image("pictures/mirror/general/danteh.png"): #checks if currently navigating
            self.navigation()

        elif common.match_image("pictures/battle/clear.png"): #checks if in squad select and then proceeds with battle
            self.squad_select()

        elif common.match_image("pictures/mirror/restshop/shop.png"): #new combined shop and rest stop
            self.rest_shop()

        elif common.match_image("pictures/mirror/general/ego_gift_get.png"): #handles the ego gift get
            self.logger.info("EGO GIFT Prompt")
            common.click_matching("pictures/general/confirm_b.png") #might replace with enter

        elif common.match_image("pictures/mirror/general/reward_select.png"): #checks if in reward select
            self.reward_select()

        elif common.match_image("pictures/mirror/general/encounter_reward.png"): #checks if in encounter rewards
            self.encounter_reward_select()            

        elif common.match_image("pictures/mirror/general/inpack.png"): #checks if in pack select
            self.pack_selection()

        elif common.match_image("pictures/battle/winrate.png"):
            core.battle()

        elif common.match_image("pictures/mirror/general/event_effect.png"):
            found = common.match_image("pictures/mirror/general/event_select.png")
            common.click_matching_coords(found)
            common.click_matching("pictures/general/confirm_b.png")
        
        elif common.match_image("pictures/general/server_error.png"):
            core.reconnect()

        return self.check_run()