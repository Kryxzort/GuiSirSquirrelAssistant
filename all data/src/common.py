import numpy as np
import cv2
import time
from mss import mss
import pyautogui
import json
import os
import secrets
import sys
from mss.tools import to_png
import logging
from PIL import ImageGrab
from functools import partial

pyautogui.FAILSAFE = False

# Template reference resolutions - used only for template matching
REFERENCE_WIDTH_1440P = 2560
REFERENCE_HEIGHT_1440P = 1440
REFERENCE_WIDTH_1080P = 1920
REFERENCE_HEIGHT_1080P = 1080

# Monitor configuration - can be adjusted by user if needed
GAME_MONITOR_INDEX = 1  # Default to primary monitor (index 1 in mss)
X_OFFSET = 0 # For fine-tuning mouse position if needed
Y_OFFSET = 0 # For fine-tuning mouse position if needed

# Actual monitor resolution (will be set during initialization)
MONITOR_WIDTH = None
MONITOR_HEIGHT = None

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

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = BASE_PATH
    return os.path.join(base_path, relative_path)

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

def update_from_shared_vars(shared_vars):
    """AUTOMATIC: Detects and updates ALL variables from SharedVars"""
    
    # Automatically find ALL Value objects in shared_vars
    for attr_name in dir(shared_vars):
        if not attr_name.startswith('_'):
            attr_obj = getattr(shared_vars, attr_name)
            
            if hasattr(attr_obj, 'value'):
                global_var_name = attr_name.upper()
                globals()[global_var_name] = attr_obj.value
                
                logger.info(f"Auto-detected: {global_var_name} = {attr_obj.value}")

def detect_monitor_resolution():
    """Detect the actual resolution of the game monitor"""
    global MONITOR_WIDTH, MONITOR_HEIGHT
    
    with mss() as sct:
        monitor = sct.monitors[GAME_MONITOR_INDEX]
        MONITOR_WIDTH = monitor['width']
        MONITOR_HEIGHT = monitor['height']
        
        # Calculate aspect ratio
        aspect_ratio = MONITOR_WIDTH / MONITOR_HEIGHT
        
        # Log the detected resolution
        logger.info(f"Detected monitor resolution: {MONITOR_WIDTH}x{MONITOR_HEIGHT}, aspect ratio: {aspect_ratio:.2f}")
        
        return MONITOR_WIDTH, MONITOR_HEIGHT

# Initialize monitor resolution at module load time
detect_monitor_resolution()

def random_choice(list):
    return secrets.choice(list)

def sleep(x):
    """Sleep function"""
    time.sleep(x)

def mouse_scroll(amount):
    pyautogui.scroll(amount)

def _validate_monitor_index(monitor_index, fallback=1):
    """Validate and return a safe monitor index"""
    with mss() as sct:
        if monitor_index >= len(sct.monitors):
            logger.warning(f"Monitor index {monitor_index} out of range, falling back to monitor {fallback}")
            return fallback
        return monitor_index

def get_monitor_info(monitor_index=None):
    """Get information about the specified monitor or the game monitor"""
    with mss() as sct:
        mon_idx = monitor_index if monitor_index is not None else GAME_MONITOR_INDEX
        mon_idx = _validate_monitor_index(mon_idx)
        return sct.monitors[mon_idx]

def get_MonCords(x, y):
    """Convert local coordinates to global monitor coordinates"""
    mon = get_monitor_info()
    return mon['left'] + x, mon['top'] + y

def mouse_move(x, y):
    """Moves the mouse to the X,Y coordinate specified on the game monitor"""
    real_x, real_y = get_MonCords(x, y)
    pyautogui.moveTo(real_x, real_y)

def mouse_click():
    """Performs a left click on the current position"""
    pyautogui.click()

def mouse_hold():
    pyautogui.mouseDown()
    sleep(2)
    pyautogui.mouseUp()

def mouse_down():
    pyautogui.mouseDown()

def mouse_up():
    pyautogui.mouseUp()

def mouse_move_click(x, y):
    """Moves the mouse to the X,Y coordinate specified and performs a left click"""
    mouse_move(x, y)
    mouse_click()

def mouse_drag(x, y, seconds=1):
    """Drag from current position to the specified coords on the game monitor"""
    real_x, real_y = get_MonCords(x, y)
    pyautogui.dragTo(real_x, real_y, seconds, button='left')

def key_press(Key, presses=1):
    """Presses the specified key X amount of times"""
    pyautogui.press(Key, presses)

def capture_screen(monitor_index=None):
    """Captures the specified monitor screen using MSS and converts it to a numpy array for CV2."""
    with mss() as sct:
        # Use specified monitor or default game monitor
        mon_idx = monitor_index if monitor_index is not None else GAME_MONITOR_INDEX
        mon_idx = _validate_monitor_index(mon_idx)
            
        monitor = sct.monitors[mon_idx]
        
        # Capture the screen with the current resolution
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        
        # Convert the color from BGRA to BGR for OpenCV compatibility
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
        return img

def save_match_screenshot(screenshot, top_left, bottom_right, template_path, match_index):
    """Saves a screenshot of the matched region, preserving directory structure in 'higher_res'."""
    # Crop the matched region from the full screenshot
    match_region = screenshot[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]
    
    # Create a modified output path in the 'higher_res' folder
    output_path = os.path.join(BASE_PATH, "higher_res", template_path)
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate a unique filename for each match within the higher_res directory
    output_path = os.path.splitext(output_path)[0]  # Remove original extension
    output_path = f"{output_path}.png"  # Append match index
    if os.path.exists(output_path):
        return
    # Save the cropped region
    cv2.imwrite(output_path, match_region)

def is_custom_1080p_image(template_path):
    """Check if the image is from the CustomAdded1080p folder"""
    return "CustomAdded1080p" in template_path

def get_template_reference_resolution(template_path):
    """Determine which reference resolution to use based on the template path"""
    if is_custom_1080p_image(template_path):
        return REFERENCE_WIDTH_1080P, REFERENCE_HEIGHT_1080P
    else:
        # For non-1080p templates, use the 1440p template dimensions
        return REFERENCE_WIDTH_1440P, REFERENCE_HEIGHT_1440P

def _extract_coordinates(filtered_boxes, area="center"):
    """Extract coordinates from filtered boxes based on area preference"""
    found_elements = []
    for (x1, y1, x2, y2) in filtered_boxes:
        if area == "bottom":
            x = (x1 + x2) // 2
            y = y2
        elif area == "top":
            x = (x1 + x2) // 2
            y = y1
        elif area == "left":
            x = x1
            y = (y1 + y2) // 2
        elif area == "right":
            x = x2
            y = (y1 + y2) // 2
        else:  # center
            x = (x1 + x2) // 2
            y = (y1 + y2) // 2
        found_elements.append((x, y))
    
    return sorted(found_elements) if found_elements else []

def _base_match_template(template_path, threshold=0.8, grayscale=False, debug=False, area="center"):
    """Internal function that handles all template matching logic"""
    # Get full path to the template image
    full_template_path = resource_path(template_path)
    
    screenshot = capture_screen()
    screenshot_height, screenshot_width = screenshot.shape[:2]

    # Convert to grayscale if requested
    if grayscale:
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

    # Determine which reference resolution to use based on the template
    base_width, base_height = get_template_reference_resolution(full_template_path)

    scale_factor_x = screenshot_width / base_width
    scale_factor_y = screenshot_height / base_height
    scale_factor = min(scale_factor_x, scale_factor_y)

    # Load template
    color_flag = cv2.IMREAD_GRAYSCALE if grayscale else cv2.IMREAD_COLOR
    template = cv2.imread(full_template_path, color_flag)
    if template is None:
        raise FileNotFoundError(f"Template image '{full_template_path}' not found.")

    template = cv2.resize(template, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_LINEAR)
    template_height, template_width = template.shape[:2]

    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)

    # Adjust threshold for lower scale factors
    if scale_factor < 0.75:
        threshold = threshold - 0.05

    locations = np.where(result >= threshold)
    boxes = []

    for pt in zip(*locations[::-1]):
        top_left = pt
        bottom_right = (top_left[0] + template_width, top_left[1] + template_height)
        boxes.append([top_left[0], top_left[1], bottom_right[0], bottom_right[1]])

    boxes = np.array(boxes)
    filtered_boxes = non_max_suppression_fast(boxes)

    # Debug visualization if requested
    if debug and len(filtered_boxes) > 0:
        debug_screenshot = screenshot.copy()
        if grayscale:
            debug_screenshot = cv2.cvtColor(debug_screenshot, cv2.COLOR_GRAY2BGR)
        
        for (x1, y1, x2, y2) in filtered_boxes:
            cv2.rectangle(debug_screenshot, (x1, y1), (x2, y2), color=(0, 255, 0), thickness=2)

        cv2.imshow("Matches", debug_screenshot)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return _extract_coordinates(filtered_boxes, area)

def match_image(template_path, threshold=0.8, area="center"):
    """Finds the image specified and returns coordinates depending on area: center, bottom, left, right, top."""
    return _base_match_template(template_path, threshold, grayscale=False, debug=False, area=area)

def greyscale_match_image(template_path, threshold=0.75):
    """Finds the image specified and returns the center coordinates, regardless of screen resolution,
    and saves screenshots of each match found."""
    return _base_match_template(template_path, threshold, grayscale=True, debug=False, area="center")

def debug_match_image(template_path, threshold=0.8):
    """Finds the image specified and returns the center coordinates, regardless of screen resolution,
       and draws rectangles on each match found."""
    return _base_match_template(template_path, threshold, grayscale=False, debug=True, area="center")

def proximity_check(list1, list2, threshold):
    close_pairs = set()  # To store pairs of coordinates that are close
    for coord1 in list1:
        for coord2 in list2:
            distance = np.sqrt((coord1[0] - coord2[0]) ** 2 + (coord1[1] - coord2[1]) ** 2)
            if distance < threshold:
                close_pairs.add(coord1)
    return close_pairs

def proximity_check_fuse(list1, list2, x_threshold ,threshold):
    close_pairs = set()  # To store pairs of coordinates meeting the criteria
    for coord1 in list1:
        for coord2 in list2:
            x_difference = abs(coord1[0] - coord2[0])
            if x_difference < x_threshold:  # Check if x values are the same
                y_difference = abs(coord1[1] - coord2[1])
                if y_difference < threshold:  # Check if y difference is within the threshold
                    close_pairs.add(coord1)
    return close_pairs

def get_resolution(monitor_index=None):
    """Gets the resolution of the specified monitor or the game monitor"""
    mon = get_monitor_info(monitor_index)
    return mon['width'], mon['height']

def non_max_suppression_fast(boxes, overlapThresh=0.5):
    """Remove multiple detections on the same position"""
    if len(boxes) == 0:
        return []

    # Convert to float if necessary
    if boxes.dtype.kind == "i":
        boxes = boxes.astype("float")

    # Initialize the list of picked indexes
    pick = []

    # Get coordinates of bounding boxes
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]

    # Compute the area of the bounding boxes and sort by the bottom-right y-coordinate
    area = (x2 - x1 + 1) * (y2 - y1 + 1)
    idxs = np.argsort(y2)

    # Keep looping while some indexes still remain in the indexes list
    while len(idxs) > 0:
        # Grab the last index in the indexes list, add the index value to the list of picked indexes
        last = len(idxs) - 1
        i = idxs[last]
        pick.append(i)

        # Find the largest (x, y) coordinates for the start of the bounding box
        # and the smallest (x, y) coordinates for the end of the bounding box
        xx1 = np.maximum(x1[i], x1[idxs[:last]])
        yy1 = np.maximum(y1[i], y1[idxs[:last]])
        xx2 = np.minimum(x2[i], x2[idxs[:last]])
        yy2 = np.minimum(y2[i], y2[idxs[:last]])

        # Compute the width and height of the bounding box
        w = np.maximum(0, xx2 - xx1 + 1)
        h = np.maximum(0, yy2 - yy1 + 1)

        # Compute the ratio of overlap
        overlap = (w * h) / area[idxs[:last]]

        # Delete all indexes from the index list that have an overlap greater than the threshold
        idxs = np.delete(idxs, np.concatenate(([last], np.where(overlap > overlapThresh)[0])))

    # Return only the bounding boxes that were picked
    return boxes[pick].astype("int")

def get_aspect_ratio(monitor_index=None):
    width, height = get_resolution(monitor_index)
    if (width / 4) * 3 == height:
        return "4:3"
    if (width / 16) * 9 == height:
        return "16:9"
    if (width / 16) * 10 == height:
        return "16:10"
    else:
        return None

# ==================== INTERNAL DRY SCALING FUNCTIONS ====================

def _uniform_scale_coordinates(x, y, reference_width, reference_height, use_uniform=True):
    """Internal function that does all coordinate scaling work"""
    scale_factor_x = MONITOR_WIDTH / reference_width
    scale_factor_y = MONITOR_HEIGHT / reference_height
    
    if use_uniform:
        # Use minimum scale factor to maintain aspect ratio (true uniform scaling)
        scale_factor = min(scale_factor_x, scale_factor_y)
        scaled_x = round(x * scale_factor) + X_OFFSET
        scaled_y = round(y * scale_factor) + Y_OFFSET
    else:
        # Use individual scale factors (stretches to fill screen)
        scaled_x = round(x * scale_factor_x) + X_OFFSET
        scaled_y = round(y * scale_factor_y) + Y_OFFSET
    
    return scaled_x, scaled_y

def _scale_single_coordinate(coord, reference_dimension, actual_dimension, offset=0):
    """Scale a single coordinate dimension"""
    return round(coord * actual_dimension / reference_dimension) + offset

# ==================== PUBLIC SCALING FUNCTIONS (BACKWARD COMPATIBLE) ====================

def scale_x(x):
    """Scale X coordinate based on 1440p reference to the actual monitor width"""
    return _scale_single_coordinate(x, REFERENCE_WIDTH_1440P, MONITOR_WIDTH, X_OFFSET)

def scale_y(y):
    """Scale Y coordinate based on 1440p reference to the actual monitor height"""
    return _scale_single_coordinate(y, REFERENCE_HEIGHT_1440P, MONITOR_HEIGHT, Y_OFFSET)

def scale_x_1080p(x):
    """Scale X coordinate based on 1080p reference to the actual monitor width"""
    return _scale_single_coordinate(x, REFERENCE_WIDTH_1080P, MONITOR_WIDTH, X_OFFSET)

def scale_y_1080p(y):
    """Scale Y coordinate based on 1080p reference to the actual monitor height"""
    return _scale_single_coordinate(y, REFERENCE_HEIGHT_1080P, MONITOR_HEIGHT, Y_OFFSET)

def uniform_scale_single(coord):
    """Scale a single coordinate using the minimum scale factor to maintain aspect ratio"""
    scale_factor_x = MONITOR_WIDTH / REFERENCE_WIDTH_1440P
    scale_factor_y = MONITOR_HEIGHT / REFERENCE_HEIGHT_1440P
    scale_factor = min(scale_factor_x, scale_factor_y)
    return round(scale_factor * coord)

def uniform_scale_coordinates(x, y):
    """Scale (x, y) coordinates from 1440p reference to the current screen resolution."""
    return _uniform_scale_coordinates(x, y, REFERENCE_WIDTH_1440P, REFERENCE_HEIGHT_1440P, use_uniform=False)

def uniform_scale_coordinates_1080p(x, y):
    """Scale (x, y) coordinates from 1080p reference to the current screen resolution."""
    return _uniform_scale_coordinates(x, y, REFERENCE_WIDTH_1080P, REFERENCE_HEIGHT_1080P, use_uniform=False)

# ==================== GAME-SPECIFIC FUNCTIONS ====================

def click_skip(times):
    """Click Skip the amount of time specified"""
    scaled_x, scaled_y = _uniform_scale_coordinates(895, 465, REFERENCE_WIDTH_1080P, REFERENCE_HEIGHT_1080P, use_uniform=False)
    mouse_move_click(scaled_x, scaled_y)
    for i in range(times):
        mouse_click()

def wait_skip(img_path, threshold=0.8):
    """Clicks on the skip button and waits for specified element to appear"""
    scaled_x, scaled_y = _uniform_scale_coordinates(895, 465, REFERENCE_WIDTH_1080P, REFERENCE_HEIGHT_1080P, use_uniform=False)
    mouse_move_click(scaled_x, scaled_y)
    while(not element_exist(img_path, threshold)):
        mouse_click()
    click_matching(img_path, threshold)

def click_matching(image_path, threshold=0.8, area="center", mousegoto200="1"):
    if element_exist(image_path, threshold):
        found = match_image(image_path, threshold, area)
        if found:
            x, y = found[0]
            mouse_move_click(x, y)
            time.sleep(0.5)
        elif mousegoto200 == "1":
            mouse_move(200, 200)
            click_matching(image_path, threshold, area)
        else:
            click_matching(image_path, threshold, area, mousegoto200="0")

def element_exist(img_path, threshold=0.8):
    """Checks if the element exists if not returns none"""
    result = match_image(img_path, threshold)
    return result

def squad_order(status):
    """Returns a list of the image locations depending on the sinner order specified in the json file"""
    characters_positions = {
    "yisang": (580, 500),
    "faust": (847, 500),
    "donquixote": (1113, 500),
    "ryoshu": (1380, 500),
    "meursault": (1647, 500),
    "honglu": (1913, 500),
    "heathcliff": (580, 900),
    "ishmael": (847, 900),
    "rodion": (1113, 900),
    "sinclair": (1380, 900),
    "outis": (1647, 900),
    "gregor": (1913, 900)
}

    json_path = os.path.join(BASE_PATH, "config", "squad_order.json")
    with open(json_path, "r") as f:
        squads = json.load(f)
    squad = squads[status]
    
    sinner_order = []
    for i in range(1,13):
      for name, value in squad.items():
        if value == i:
            sinner_name = name
            if sinner_name in characters_positions:
                position = characters_positions[sinner_name]
                x,y = characters_positions[sinner_name]
                sinner_order.append(_uniform_scale_coordinates(x, y, REFERENCE_WIDTH_1440P, REFERENCE_HEIGHT_1440P, use_uniform=False))  
    return sinner_order

def luminence(x,y):
    """Get Luminence of the pixel and return overall coefficient"""
    screenshot = capture_screen()
    pixel_image = screenshot[y, x]
    coeff = (int(pixel_image[0]) + int(pixel_image[1]) + int(pixel_image[2])) / 3
    return coeff

def error_screenshot():
    error_dir = os.path.join(BASE_PATH, "error")
    os.makedirs(error_dir, exist_ok=True)
    with mss() as sct:
        monitor = sct.monitors[GAME_MONITOR_INDEX]  # Use the configured game monitor
        screenshot = sct.grab(monitor)
        png = to_png(screenshot.rgb, screenshot.size)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        with open(os.path.join(error_dir, timestamp + ".png"), "wb") as f:
            f.write(png)

def set_game_monitor(monitor_index):
    """Set which monitor the game is running on"""
    global GAME_MONITOR_INDEX
    with mss() as sct:
        if monitor_index < 1 or monitor_index >= len(sct.monitors):
            logger.warning(f"Invalid monitor index {monitor_index}, using primary monitor")
            GAME_MONITOR_INDEX = 1
        else:
            GAME_MONITOR_INDEX = monitor_index
            logger.info(f"Game monitor set to {monitor_index}")
    
    # Re-detect monitor resolution after changing monitor
    detect_monitor_resolution()
    return GAME_MONITOR_INDEX

def list_available_monitors():
    """List all available monitors and their properties"""
    with mss() as sct:
        monitors = []
        for i, monitor in enumerate(sct.monitors):
            if i == 0:  # Skip the "all monitors" entry
                continue
            monitors.append({
                "index": i,
                "left": monitor["left"],
                "top": monitor["top"],
                "width": monitor["width"],
                "height": monitor["height"]
            })
        return monitors

def get_monitor_resolution():
    """Get the current monitor resolution"""
    return MONITOR_WIDTH, MONITOR_HEIGHT