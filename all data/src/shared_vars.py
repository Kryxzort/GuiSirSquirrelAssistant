import os
import json
import logging
from threading import Lock

def get_base_path():
    """Get the base directory path"""
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

logger = logging.getLogger(__name__)

# Config cache system
_config_cache = {}
_cache_lock = Lock()
_scaled_coords_cache = {}

class ConfigCache:
    
    @staticmethod
    def get_config(config_name):
        """Get config data from cache, loading if needed"""
        with _cache_lock:
            if config_name not in _config_cache:
                ConfigCache._load_config(config_name)
            return _config_cache.get(config_name, {})
    
    @staticmethod
    def _load_config(config_name):
        """Load config file into cache"""
        try:
            config_path = os.path.join(BASE_PATH, "config", f"{config_name}.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    _config_cache[config_name] = json.load(f)
            else:
                _config_cache[config_name] = {}
        except Exception as e:
            _config_cache[config_name] = {}
    
    @staticmethod
    def reload_config(config_name):
        """Reload specific config from file"""
        with _cache_lock:
            if config_name in _config_cache:
                del _config_cache[config_name]
            ConfigCache._load_config(config_name)
    
    @staticmethod
    def reload_all():
        """Reload all cached configs"""
        with _cache_lock:
            config_names = list(_config_cache.keys())
            _config_cache.clear()
            for config_name in config_names:
                ConfigCache._load_config(config_name)
    
    @staticmethod
    def preload_all_configs():
        """Preload common config files into cache for performance"""
        config_files = [
            "squad_order", "delayed_squad_order", "status_selection", 
            "exp_team_selection", "threads_team_selection",
            "gui_config", "pack_priority", "delayed_pack_priority",
            "pack_exceptions", "delayed_pack_exceptions", "fusion_exceptions",
            "grace_selection"
        ]
        with _cache_lock:
            for config_name in config_files:
                if config_name not in _config_cache:
                    ConfigCache._load_config(config_name)
        
        # Load image threshold configuration
        ConfigCache._load_config("image_thresholds")

class ScaledCoordinates:
    
    @staticmethod
    def get_scaled_coords(coord_set_name):
        """Get scaled coordinate set, calculating if needed"""
        if coord_set_name not in _scaled_coords_cache:
            ScaledCoordinates._calculate_coords(coord_set_name)
        return _scaled_coords_cache.get(coord_set_name, {})
    
    @staticmethod
    def _calculate_coords(coord_set_name):
        """Calculate and cache scaled coordinates for different screen resolutions"""
        import common
        
        if coord_set_name == "grace_of_stars":
            base_coords = {
                "star of the beniggening": (300, 350),
                "cumulating starcloud": (600, 350),
                "interstellar travel": (900, 350),
                "star shower": (1200, 350),
                "binary star shop": (1500, 350),
                "moon star shop": (300, 650),
                "favor of the nebula": (600, 650),
                "starlight guidance": (900, 650),
                "chance comet": (1200, 650),
                "perfected possibility": (1500, 650)
            }
            scaled_coords = {}
            for name, (x, y) in base_coords.items():
                scaled_coords[name] = common.scale_coordinates_1080p(x, y)
            _scaled_coords_cache[coord_set_name] = scaled_coords
        
        elif coord_set_name == "character_positions":
            base_coords = {
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
            scaled_coords = {}
            for name, (x, y) in base_coords.items():
                # Use 1440p scaling for character positions as per original code
                scaled_coords[name] = common._uniform_scale_coordinates(x, y, common.REFERENCE_WIDTH_1440P, common.REFERENCE_HEIGHT_1440P, use_uniform=False)
            _scaled_coords_cache[coord_set_name] = scaled_coords
        
        elif coord_set_name == "battle_buttons":
            base_coords = {
                "to_battle": (1722, 881),  # Squad selection to battle button
            }
            scaled_coords = {}
            for name, (x, y) in base_coords.items():
                scaled_coords[name] = common.scale_coordinates_1080p(x, y)
            _scaled_coords_cache[coord_set_name] = scaled_coords
        
        elif coord_set_name == "luxcavation_coords":
            base_coords = {
                "latest_stage": (1613, 715),  # EXP latest stage click
                "exp_drag_start": (397, 48),  # EXP drag movements
                "exp_drag_end": (1920, 48),
                "exp_drag_middle": (1152, 48),
                "thread_select": (564, 722),  # Thread selection
                "latest_difficulty": (925, 725),  # Latest difficulty
                "squad_scroll_offset": (90, 90),  # Squad scroll offset
            }
            scaled_coords = {}
            for name, (x, y) in base_coords.items():
                if name == "squad_scroll_offset":
                    # Use uniform scaling for squad offset
                    scaled_coords[name] = common.scale_coordinates_1440p(x, y)
                else:
                    # Use 1080p scaling for other coordinates
                    scaled_x = common.scale_x_1080p(x)
                    scaled_y = common.scale_y_1080p(y)
                    scaled_coords[name] = (scaled_x, scaled_y)
            _scaled_coords_cache[coord_set_name] = scaled_coords
    
    @staticmethod
    def preload_all_coordinates():
        """Preload all coordinate sets for performance"""
        coord_sets = ["grace_of_stars", "character_positions", "battle_buttons", "luxcavation_coords"]
        for coord_set in coord_sets:
            ScaledCoordinates.get_scaled_coords(coord_set)

def _get_gui_values():
    """Extract current variable values from GUI module"""
    try:
        # Import the GUI module
        import sys
        gui_path = os.path.join(BASE_PATH, "gui_launcher.py")
        if os.path.exists(gui_path):
            old_path = sys.path[:]
            sys.path.insert(0, os.path.dirname(gui_path))
            
            try:
                import gui_launcher
                
                # Use the actual shared_vars instance from GUI if it exists
                if hasattr(gui_launcher, 'shared_vars') and gui_launcher.shared_vars:
                    shared_vars_instance = gui_launcher.shared_vars
                else:
                    # Create instance to get the variable structure
                    shared_vars_instance = gui_launcher.SharedVars()
                
                current_values = {}
                for attr_name in dir(shared_vars_instance):
                    if not attr_name.startswith('_'):
                        attr_value = getattr(shared_vars_instance, attr_name)
                        if hasattr(attr_value, 'value'):
                            current_values[attr_name] = attr_value.value
                
                return current_values
                
            finally:
                sys.path[:] = old_path
                
    except Exception as e:
        pass
    
    return {}

def _load_shared_vars():
    """Load shared variables from config file and GUI defaults"""
    
    # Get current values from GUI
    gui_values = _get_gui_values()
    
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
                shared_vars_data = {key: settings_data.get(key, gui_values[key]) 
                                  for key in gui_values.keys() if key in settings_data}
            
            # Set module-level variables
            for var_name, gui_value in gui_values.items():
                value = shared_vars_data.get(var_name, gui_value)
                globals()[var_name] = value
            
                
        else:
            # Set GUI values directly
            for var_name, gui_value in gui_values.items():
                globals()[var_name] = gui_value
                
    except Exception as e:
        # Set GUI values on error
        for var_name, gui_value in gui_values.items():
            globals()[var_name] = gui_value

# Dynamically export all loaded variables
def _update_all_exports():
    """Update module exports list"""
    global __all__
    # Get all variables from GUI values, plus utility functions
    config_vars = list(_get_gui_values().keys())
    __all__ = config_vars + ['reload_shared_vars']

def reload_shared_vars():
    """Reload shared variables from config"""
    _load_shared_vars()

# Set default for comprehensive_logging if not loaded from GUI
if 'comprehensive_logging' not in globals():
    comprehensive_logging = False

# Set default for base_match_template_logging if not loaded from GUI
if 'base_match_template_logging' not in globals():
    base_match_template_logging = False

# Initialization guard to prevent double loading
_initialized = False

def _initialize_module():
    """Initialize module only once"""
    global _initialized
    if _initialized:
        return
    
    # Auto-load shared variables when module is imported
    _load_shared_vars()
    _update_all_exports()

    # Preload all configs and coordinates for performance
    ConfigCache.preload_all_configs()
    try:
        ScaledCoordinates.preload_all_coordinates()
    except (ImportError, AttributeError):
        # common module might not be available during early import, will load on first use
        pass

    # Load image threshold configuration
    global image_threshold_config
    image_threshold_config = ConfigCache.get_config("image_thresholds")
    
    _initialized = True

# Initialize the module
_initialize_module()
