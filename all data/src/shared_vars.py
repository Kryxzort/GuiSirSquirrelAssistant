import os
import json
import logging

def get_base_path():
    """Get the correct base path for the application"""
    import sys
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

# Get base path for config access
BASE_PATH = get_base_path()

# Set up logging
logger = logging.getLogger(__name__)

def _load_shared_vars():
    """Load shared variables from gui_config.json automatically"""
    global skip_ego_check, skip_restshop, skip_ego_fusion, hard_mode, x_offset, y_offset
    global debug_image_matches, convert_images_to_grayscale, reconnection_delay
    global reconnect_when_internet_reachable, prioritize_list_over_status
    
    # Default values
    default_values = {
        'skip_ego_check': False,
        'skip_restshop': False,
        'skip_ego_fusion': False,
        'hard_mode': False,
        'x_offset': 0,
        'y_offset': 0,
        'debug_image_matches': False,
        'convert_images_to_grayscale': True,
        'reconnection_delay': 6,
        'reconnect_when_internet_reachable': False,
        'prioritize_list_over_status': False
    }
    
    try:
        config_path = os.path.join(BASE_PATH, "config", "gui_config.json")
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Get SharedVars section, fallback to Settings for backward compatibility
            shared_vars_data = config.get('SharedVars', {})
            if not shared_vars_data:
                # Fallback to Settings section for backward compatibility
                settings_data = config.get('Settings', {})
                shared_vars_data = {key: settings_data.get(key, default_values[key]) 
                                  for key in default_values.keys() if key in settings_data}
            
            # Set module-level variables
            for var_name, default_value in default_values.items():
                value = shared_vars_data.get(var_name, default_value)
                globals()[var_name] = value
                logger.debug(f"Loaded shared variable {var_name} = {value}")
                
        else:
            logger.warning(f"GUI config file not found at {config_path}, using default values")
            # Set default values
            for var_name, default_value in default_values.items():
                globals()[var_name] = default_value
                
    except Exception as e:
        logger.error(f"Error loading shared variables from config: {e}")
        # Set default values on error
        for var_name, default_value in default_values.items():
            globals()[var_name] = default_value

def reload_shared_vars():
    """Manually reload shared variables from config file"""
    _load_shared_vars()

# Auto-load shared variables when module is imported
_load_shared_vars()

# Export all shared variables for easy access
__all__ = [
    'skip_ego_check', 'skip_restshop', 'skip_ego_fusion', 'hard_mode', 'x_offset', 'y_offset',
    'debug_image_matches', 'convert_images_to_grayscale', 'reconnection_delay',
    'reconnect_when_internet_reachable', 'prioritize_list_over_status',
    'reload_shared_vars'
]
