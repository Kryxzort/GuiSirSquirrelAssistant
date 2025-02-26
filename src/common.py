import numpy as np
import cv2
import time
from mss import mss
import pyautogui
import os
import secrets
from mss.tools import to_png

pyautogui.FAILSAFE = False

# Screen related functions
def capture_screen():
    """Captures the full screen using MSS and converts it to a numpy array for CV2."""
    with mss() as sct:
        # Dynamically get the current screen resolution
        monitor = sct.monitors[1]  # [1] is the primary monitor; adjust if using multiple monitors
        
        # Capture the screen with the current resolution
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        
        # Convert the color from BGRA to BGR for OpenCV compatibility
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
        return img

def non_max_suppression_fast(boxes, overlapThresh=0.5):
    """Some stonks thing to remove multiple detections on the same position"""
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

def match_image(template_path, threshold=0.8):
    """Finds the image specified and returns the center coordinates, regardless of screen resolution"""
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        raise FileNotFoundError(f"Template image '{template_path}' not found.")

    # Capture current screen and get dimensions
    screenshot = capture_screen()
    screenshot_height, screenshot_width = screenshot.shape[:2]
    
    # Scale only if width & height doesnt match
    if screenshot_width != 2560 and screenshot_height != 1440:
        # Calculate scale factor  
        scale_factor_x = screenshot_width / 2560
        scale_factor_y = screenshot_height / 1440
        scale_factor = min(scale_factor_x,scale_factor_y)
        # Load and resize the template image according to the scale factor
        template = cv2.resize(template, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_LINEAR)
        if scale_factor < 0.75:
            threshold = threshold-0.05
    
    template_height, template_width = template.shape[:2]
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)

    locations = np.where(result >= threshold)
    boxes = []

    # Loop through all the matching locations and create bounding boxes
    for pt in zip(*locations[::-1]):  # Switch columns and rows
        top_left = pt
        bottom_right = (top_left[0] + template_width, top_left[1] + template_height)
        boxes.append([top_left[0], top_left[1], bottom_right[0], bottom_right[1]])

    boxes = np.array(boxes)

    # Apply non-maximum suppression to remove overlapping boxes
    filtered_boxes = non_max_suppression_fast(boxes)

    # List to hold the center coordinates of all filtered elements
    found_elements = []
    
    #Get Matches
    for (x1, y1, x2, y2) in filtered_boxes:
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        found_elements.append((center_x, center_y))
    
    return sorted(found_elements) if found_elements else []

def greyscale_match_image(template_path, threshold=0.8):
    """Same as match image but just in greyscale"""
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        raise FileNotFoundError(f"Template image '{template_path}' not found.")

    # Capture current screen and get dimensions
    screenshot = capture_screen()
    screenshot_height, screenshot_width = screenshot.shape[:2]
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

    # Scale only if width & height doesnt match
    if screenshot_width != 2560 and screenshot_height != 1440:
        # Calculate scale factor  
        scale_factor_x = screenshot_width / 2560
        scale_factor_y = screenshot_height / 1440
        scale_factor = min(scale_factor_x,scale_factor_y)
        # Load and resize the template image according to the scale factor
        template = cv2.resize(template, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_LINEAR)
        if scale_factor < 0.75:
            threshold = threshold-0.05
    
    template_height, template_width = template.shape[:2]
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)

    locations = np.where(result >= threshold)
    boxes = []

    # Loop through all the matching locations and create bounding boxes
    for pt in zip(*locations[::-1]):  # Switch columns and rows
        top_left = pt
        bottom_right = (top_left[0] + template_width, top_left[1] + template_height)
        boxes.append([top_left[0], top_left[1], bottom_right[0], bottom_right[1]])

    boxes = np.array(boxes)

    # Apply non-maximum suppression to remove overlapping boxes
    filtered_boxes = non_max_suppression_fast(boxes)

    # List to hold the center coordinates of all filtered elements
    found_elements = []
    
    #Get Matches
    for (x1, y1, x2, y2) in filtered_boxes:
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        found_elements.append((center_x, center_y))
    
    return sorted(found_elements) if found_elements else []

def debug_match_image(template_path, threshold=0.8):
    """Same as match image but draws rectangles around the found image"""
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        raise FileNotFoundError(f"Template image '{template_path}' not found.")

    # Capture current screen and get dimensions
    screenshot = capture_screen()
    screenshot_height, screenshot_width = screenshot.shape[:2]
    
    # Scale only if width & height doesnt match
    if screenshot_width != 2560 and screenshot_height != 1440:
        # Calculate scale factor  
        scale_factor_x = screenshot_width / 2560
        scale_factor_y = screenshot_height / 1440
        scale_factor = min(scale_factor_x,scale_factor_y)
        # Load and resize the template image according to the scale factor
        template = cv2.resize(template, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_LINEAR)
        if scale_factor < 0.75:
            threshold = threshold-0.05
    
    template_height, template_width = template.shape[:2]
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)

    locations = np.where(result >= threshold)
    boxes = []

    # Loop through all the matching locations and create bounding boxes
    for pt in zip(*locations[::-1]):  # Switch columns and rows
        top_left = pt
        bottom_right = (top_left[0] + template_width, top_left[1] + template_height)
        boxes.append([top_left[0], top_left[1], bottom_right[0], bottom_right[1]])

    boxes = np.array(boxes)

    # Apply non-maximum suppression to remove overlapping boxes
    filtered_boxes = non_max_suppression_fast(boxes)

    # List to hold the center coordinates of all filtered elements
    found_elements = []
    
    #Get Matches
    for (x1, y1, x2, y2) in filtered_boxes:
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        found_elements.append((center_x, center_y))
        
        # Draw rectangle around the match
        cv2.rectangle(screenshot, (x1, y1), (x2, y2), color=(0, 255, 0), thickness=2)

    # Show the screenshot with rectangles for immediate feedback
    cv2.imshow("Matches", screenshot)
    cv2.waitKey(0)  # Wait for a key press to close the window
    cv2.destroyAllWindows()

    return found_elements if found_elements else None

def luminence(x,y):
    """Get Luminence of the pixel and return overall coefficient"""
    screenshot = capture_screen()
    pixel_image = screenshot[y, x]
    coeff = (int(pixel_image[0]) + int(pixel_image[1]) + int(pixel_image[2])) / 3
    return coeff

# General Functions

def sleep(seconds):
    """Sleep for X amount of seconds"""
    time.sleep(seconds)

def random_choice(list):
    """Chooses a random option in the list"""
    return secrets.choice(list)

def click_matching(image_path, threshold=0.8):
    """Click on the image as specified if found"""
    if found:= match_image(image_path,threshold):
        click_matching_coords(found)
    else:
        mouse_move(100,100)
        click_matching(image_path,threshold)
    
def click_matching_coords(found):
    """This is used for the := image checks rather than running match_image again like click matching"""
    x,y = random_choice(found)
    mouse_move_click(x,y)
    time.sleep(0.5)

def wait_skip(img_path,threshold=0.8):
    """Clicks on the skip button and waits for specified element to appear"""
    mouse_move_click(scale_x(1193),scale_y(623))
    while(not match_image(img_path,threshold)):
        mouse_click()
    click_matching(img_path,threshold)

def click_skip(times):
    """Click Skip the amount of time specified"""
    mouse_move_click(scale_x(1193),scale_y(623))
    for i in range(times):
        mouse_click()
    
def error_screenshot():
    os.makedirs("error", exist_ok=True)
    with mss() as sct:
        # Dynamically get the current screen resolution
        monitor = sct.monitors[1]  # [1] is the primary monitor; adjust if using multiple monitors
        # Capture the screen with the current resolution
        screenshot = sct.grab(monitor)
        png = to_png(screenshot.rgb, screenshot.size)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        with open("error/" + timestamp + ".png", "wb") as f:
            f.write(png)

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

# Scaling Functions
def get_resolution():
    """Gets the current resolution"""
    return pyautogui.size()

def get_aspect_ratio():
    """Gets Aspect Ratio"""
    width,height = get_resolution()
    if (width / 4) * 3 == height:
        return "4:3"
    if (width / 16) * 9 == height:
        return "16:9"
    if (width / 16) * 10 == height:
        return "16:10"
    else:
        raise RuntimeError ("Not supported resolution")
    
def scale_x(x):
    """Scales the X coordinate to current resolution from 1440p"""
    screen_width = get_resolution()[0] # Width is index 0
    scale_factor_x = screen_width / 2560
    return round(x * (scale_factor_x))

def scale_y(y):
    """Scales the Y coordinate to current resolution from 1440p"""
    screen_height = get_resolution()[1] # Height is index 1
    scale_factor_y =  screen_height / 1440
    return round(y * scale_factor_y)

def uniform_scale_single(coord):
    width,height = get_resolution()
    scale_factor_x = width / 2560
    scale_factor_y = height / 1440
    scale_factor = min(scale_factor_x,scale_factor_y)
    return round(scale_factor * coord)

def uniform_scale_coordinates(x, y):
    """Scale (x, y) coordinates from 1440P to the current screen resolution."""
    width,height = get_resolution()
    scale_factor_x = width / 2560
    scale_factor_y = height / 1440
    scaled_x = round(x * scale_factor_x)
    scaled_y = round(y * scale_factor_y)
    return scaled_x, scaled_y

# Mouse & Keyboard Functions

def mouse_move(x,y):
    """Moves mouse to the specified X/Y coordinate"""
    pyautogui.moveTo(x,y)

def mouse_click():
    """Performs a left mouse click on the current position"""
    pyautogui.click()

def mouse_move_click(x,y):
    """Moves the mouse to the specified x/y coordinate and click"""
    pyautogui.click(x,y)

def mouse_hold():
    """Holding the mouse down for 2 seconds"""
    pyautogui.mouseDown()
    time.sleep(2)
    pyautogui.mouseUp()

def mouse_down():
    """Holding the mouse down"""
    pyautogui.mouseDown()

def mouse_up():
    """Releasing the mouse"""
    pyautogui.mouseUp()

def mouse_scroll(amount):
    pyautogui.scroll(amount)

def mouse_drag(x,y):
    """Drag from current cursor coordinates to the specified coordinate over 1 second"""
    pyautogui.dragTo(x,y,1,button='left')

def key_press(key, presses=1):
    """Presses the specified key X amount of times"""
    pyautogui.press(key,presses)