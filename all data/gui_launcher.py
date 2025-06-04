import customtkinter as ctk
import subprocess
import signal
import os
import sys
import platform
from tkinter import messagebox
import keyboard
import json
import time
import threading
import logging
import queue
from threading import Thread
import configparser
import re
import webbrowser

DISCORD_INVITE = "https://discord.gg/vccsv4Q4ta"
def join_discord():
    webbrowser.open(DISCORD_INVITE)

# =====================================================================
# PATH HANDLING - IMPROVED DIRECTORY STRUCTURE DETECTION
# =====================================================================

def get_correct_base_path():
    """Get the correct base path for the application with smart directory detection"""
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        base = os.path.dirname(sys.executable)
    else:
        # Running as script
        base = os.path.dirname(os.path.abspath(__file__))
        
    # Smart directory detection
    if os.path.basename(base) == "src":
        # We're in src folder inside all data
        all_data_dir = os.path.dirname(base)  # Go up 1 level to all data
        main_dir = os.path.dirname(all_data_dir)  # Go up 1 more level
    elif os.path.basename(base) == "all data":
        # We're directly in the all data folder
        all_data_dir = base
        main_dir = os.path.dirname(base)
    else:
        # We're in the main directory
        all_data_dir = os.path.join(base, "all data")
        main_dir = base
        
    return main_dir, all_data_dir

# Get correct paths
MAIN_DIR, ALL_DATA_DIR = get_correct_base_path()
BASE_PATH = ALL_DATA_DIR  # Set BASE_PATH to "all data" folder

# Add src to Python path for imports
sys.path.append(os.path.join(BASE_PATH, 'src'))

# Try to import the updater module
try:
    from src.updater import check_for_updates, auto_update
    UPDATER_AVAILABLE = True
except ImportError:
    UPDATER_AVAILABLE = False

# Define python interpreter path based on whether we're frozen or not
def get_python_command():
    if getattr(sys, 'frozen', False):
        # If running as exe, use the executable path to launch Python modules
        if platform.system() == "Windows":
            return os.path.join(MAIN_DIR, "gui_launcher.exe")
        else:
            return os.path.join(MAIN_DIR, "gui_launcher")
    else:
        # If running as script, use system's Python interpreter
        return sys.executable

PYTHON_CMD = get_python_command()

# Script paths
MIRROR_SCRIPT_PATH = os.path.join(BASE_PATH, "src", "compiled_runner.py")
EXP_SCRIPT_PATH = os.path.join(BASE_PATH, "src", "exp_runner.py")
THREADS_SCRIPT_PATH = os.path.join(BASE_PATH, "src", "threads_runner.py")
THEME_RESTART_PATH = os.path.join(BASE_PATH, "src", "theme_restart.py")
FUNCTION_RUNNER_PATH = os.path.join(BASE_PATH, "src", "function_runner.py")
BATTLER_SCRIPT_PATH = os.path.join(BASE_PATH, "src", "battler.py")

# Configuration file paths
CONFIG_DIR = os.path.join(BASE_PATH, "config")
JSON_PATH = os.path.join(CONFIG_DIR, "squad_order.json")
SLOW_JSON_PATH = os.path.join(CONFIG_DIR, "slow_squad_order.json")
STATUS_SELECTION_PATH = os.path.join(CONFIG_DIR, "status_selection.txt")
GUI_CONFIG_PATH = os.path.join(CONFIG_DIR, "gui_config.txt")
HELP_TEXT_PATH = os.path.join(BASE_PATH, "Help.txt")

# Create config directory if it doesn't exist
os.makedirs(CONFIG_DIR, exist_ok=True)

# Setting up basic logging configuration
LOG_FILENAME = os.path.join(BASE_PATH, "Pro_Peepol's.log")
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILENAME)
    ]
)
# Use "GUI" directly instead of __name__
logger = logging.getLogger("GUI")

# =====================================================================
# LOGGING HELPERS
# =====================================================================

# Convenience functions for different log levels
def debug(message):
    logger.debug(message)

def info(message):
    logger.info(message)

def warning(message):
    logger.warning(message)

def error(message):
    logger.error(message)

def critical(message):
    logger.critical(message)

# Module names for log filtering
LOG_MODULES = {
    "GUI": "GUI",  # Changed from __main__ to GUI
    "Mirror Dungeon": "compiled_runner",
    "Exp": "exp_runner",
    "Threads": "threads_runner",
    "Function": "function_runner",
    "Common": "common",
    "Core": "core",
    "Mirror": "mirror",
    "Mirror Utils": "mirror_utils",
    "Theme": "theme_restart",
    "Luxcavation": "luxcavation_functions",
    "Other": "other"
}

# List of log messages to filter out (noise reduction)
FILTERED_MESSAGES = [
    "Loaded existing log file with filters applied",
    "GUI initialized",
    "Created tab layout with all tabs",
    "Mirror Dungeon tab setup complete",
    "Exp tab setup complete",
    "Threads tab setup complete",
    "Others tab setup complete",
    "Settings tab setup complete",
    "Help tab setup complete",
    "Logs tab setup complete",
    "Keyboard shortcuts registered from configuration",
    "Starting Pro Peepol Macro application",
    "Application closing",
    "Application closed",
    "Loaded squad data from file",
    "Saved slow squad data to file",
    "Registered keyboard shortcuts: ctrl+q (Mirror), ctrl+e (Exp), ctrl+r (Threads), ctrl+t (Battle)"
]

# =====================================================================
# GLOBAL CONSTANTS
# =====================================================================

# Available themes for the UI - USING ONLY VALIDATED THEMES THAT EXIST
THEMES = {
    "Dark": {"mode": "dark", "theme": "dark-blue"},
    "Blue Dark": {"mode": "dark", "theme": "blue"},
    "Green Dark": {"mode": "dark", "theme": "green"},
    "Light": {"mode": "light", "theme": "blue"}
}

# Game status columns layout
STATUS_COLUMNS = [
    ["sinking", "burn", "poise"],
    ["charge", "rupture", "slash", "blunt"],
    ["bleed", "tremor", "pierce"]
]

# Character list for the game
SINNER_LIST = [
    "Yi Sang", "Faust", "Don Quixote", "Ryōshū", "Meursault",
    "Hong Lu", "Heathcliff", "Ishmael", "Rodion", "Sinclair", "Gregor", "Outis"
]

# Team layout positioning in the grid
TEAM_ORDER = [
    ("sinking", 0, 0), ("charge", 0, 1), ("slash", 0, 2),
    ("blunt", 1, 0), ("burn", 1, 1), ("rupture", 1, 2),
    ("poise", 2, 0), ("bleed", 2, 1), ("tremor", 2, 2),
    ("pierce", 3, 0), ("None", 3, 1)
]

# =====================================================================
# GLOBAL VARIABLES
# =====================================================================

# Global variables for data storage and state tracking
squad_data = {}
slow_squad_data = {}
checkbox_vars = {}
dropdown_vars = {}
expand_frames = {}
process = None
exp_process = None
threads_process = None
function_process = None
function_process_list = []  # List to track multiple function processes
battle_process = None
filtered_messages_enabled = True
is_update_available = False  # Track if updates are available

# Chain automation variables
chain_running = False
chain_queue = []
current_chain_step = 0

# Lazy loading flags
settings_tab_loaded = False
logs_tab_loaded = False

# =====================================================================
# HELPER FUNCTIONS
# =====================================================================

def load_checkbox_data():
    """Load checkbox variables at startup without creating UI elements"""
    global checkbox_vars
    
    # Only load if not already loaded
    if checkbox_vars:
        return
    
    prechecked = load_initial_selections()
    
    # Create BooleanVar objects for each team status without creating UI
    for name, row, col in TEAM_ORDER:
        var = ctk.BooleanVar(value=name in prechecked)
        checkbox_vars[name] = var
    
    debug(f"Loaded checkbox data at startup. Pre-checked: {list(prechecked)}")

# Shared error handling decorator
def safe_execute(func):
    """Decorator for consistent error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error(f"Error in {func.__name__}: {e}")
            return None
    return wrapper

# Helper function for character name normalization
def sinner_key(name):
    """Convert a sinner name to a standardized key"""
    return name.lower().replace(" ", "").replace("ō", "o").replace("ū", "u")

# Functions for JSON data management
@safe_execute
def load_json():
    """Load squad data from JSON files"""
    global squad_data, slow_squad_data
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r") as f:
            squad_data = json.load(f)
        debug("Loaded squad data from file")
    else:
        squad_data = {}
        warning("Squad data file not found, using empty data")
    # Copy squad to slow
    slow_squad_data = json.loads(json.dumps(squad_data))
    save_slow_json()

@safe_execute
def save_json():
    """Save squad data to JSON file"""
    with open(JSON_PATH, "w") as f:
        json.dump(squad_data, f, indent=4)
    debug("Saved squad data to file")

@safe_execute
def save_slow_json():
    """Save slow squad data to JSON file"""
    with open(SLOW_JSON_PATH, "w") as f:
        json.dump(slow_squad_data, f, indent=4)
    debug("Saved slow squad data to file")

def delayed_slow_sync():
    """Sync squad data to slow squad with delay"""
    try:
        time.sleep(0.5)
        slow_squad_data.update(json.loads(json.dumps(squad_data)))
        save_slow_json()
        debug("Updated slow squad data after delay")
    except Exception as e:
        error(f"Error syncing slow squad data: {e}")

# Functions for status selection management
@safe_execute
def load_initial_selections():
    """Load previously selected checkboxes"""
    try:
        with open(STATUS_SELECTION_PATH, "r") as f:
            return {line.strip() for line in f if line.strip()}
    except FileNotFoundError:
        warning("Status selection file not found")
        return set()

# Process state checking functions
def is_any_process_running():
    """Check if any automation is currently running"""
    return (process is not None or exp_process is not None or 
            threads_process is not None or chain_running)

def get_running_process_name():
    """Get the name of the currently running process"""
    if chain_running:
        return "Chain Automation"
    if process is not None:
        return "Mirror Dungeon"
    if exp_process is not None:
        return "Exp"
    if threads_process is not None:
        return "Threads"
    return None

# Shared process conflict check
def check_process_conflict(process_name):
    """Check if another process is running and show warning"""
    if is_any_process_running():
        running_name = get_running_process_name()
        warning(f"Cannot start {process_name} while {running_name} is running")
        return True
    return False

# =====================================================================
# CONFIGURATION MANAGEMENT
# =====================================================================

# Initialize the main application window
root = ctk.CTk()
root.geometry("433x344")  # Default window size
root.title("Pro Peepol Macro😎")
original_title = root.title()  # Store original title for later restoration

# Configuration management functions
def load_gui_config():
    """Load GUI configuration from file with improved error handling and optimized validation"""
    config = configparser.ConfigParser()
    
    # Default values - only what's actually needed
    defaults = {
        'theme': 'Dark',
        'mirror_runs': '1',
        'exp_runs': '1',
        'exp_stage': '1',
        'threads_runs': '1',
        'threads_difficulty': '20',
        'window_width': '433',
        'window_height': '344',
        'filter_noise': 'True',
        'github_owner': 'Kryxzort',
        'github_repo': 'GuiSirSquirrelAssistant',
        'auto_update': 'False',
        'create_backups': 'True',
        'update_notifications': 'True',
        'kill_processes_on_exit': 'True',
        'chain_threads_runs': '3',  # Default chain values
        'chain_exp_runs': '2',      # Default chain values
        'chain_mirror_runs': '1'    # Default chain values
    }
    
    # Default log filter values
    log_filter_defaults = {
        'debug': 'False',
        'info': 'False',
        'warning': 'True',
        'error': 'True',
        'critical': 'True'
    }
    
    # Default module filter values
    module_filter_defaults = {}
    for module in LOG_MODULES:
        module_filter_defaults[module.lower().replace(' ', '_')] = 'True'
    
    # Default keyboard shortcut values
    shortcut_defaults = {
        'mirror_dungeon': 'ctrl+q',
        'exp': 'ctrl+e',
        'threads': 'ctrl+r',
        'battle': 'ctrl+t',
        'call_function': 'ctrl+g',
        'terminate_functions': 'ctrl+shift+g',
        'chain_automation': 'ctrl+b'
    }
    
    # Load config file if it exists
    config_needs_save = False
    
    if os.path.exists(GUI_CONFIG_PATH):
        try:
            config.read(GUI_CONFIG_PATH)
        except Exception as e:
            error(f"Error loading GUI config: {e}")
            config_needs_save = True
    else:
        config_needs_save = True
    
    # OPTIMIZED: Only add missing sections/keys instead of validating everything
    if 'Settings' not in config:
        config['Settings'] = {}
        config_needs_save = True
    
    # Only add missing defaults
    for key, value in defaults.items():
        if key not in config['Settings']:
            config['Settings'][key] = value
            config_needs_save = True
    
    # Same optimization for other sections
    if 'LogFilters' not in config:
        config['LogFilters'] = log_filter_defaults
        config_needs_save = True
    else:
        for key, value in log_filter_defaults.items():
            if key not in config['LogFilters']:
                config['LogFilters'][key] = value
                config_needs_save = True
    
    if 'ModuleFilters' not in config:
        config['ModuleFilters'] = module_filter_defaults
        config_needs_save = True
    else:
        for key, value in module_filter_defaults.items():
            if key not in config['ModuleFilters']:
                config['ModuleFilters'][key] = value
                config_needs_save = True
    
    if 'Shortcuts' not in config:
        config['Shortcuts'] = shortcut_defaults
        config_needs_save = True
    else:
        for key, value in shortcut_defaults.items():
            if key not in config['Shortcuts']:
                config['Shortcuts'][key] = value
                config_needs_save = True
    
    # Make sure saved theme is valid
    if config['Settings']['theme'] not in THEMES:
        config['Settings']['theme'] = 'Dark'
        config_needs_save = True
    
    # OPTIMIZED: Only save if something actually changed
    if config_needs_save:
        save_gui_config(config)
    
    return config

def save_gui_config(config=None):
    """Save GUI configuration to file with error handling"""
    if config is None:
        # Create config from current state
        config = configparser.ConfigParser()
        
        # Make sure all sections exist
        config['Settings'] = {}
        config['LogFilters'] = {}
        config['ModuleFilters'] = {}
        config['Shortcuts'] = {}
            
        # Add settings safely
        try:
            config['Settings'] = {
                'theme': theme_var.get() if 'theme_var' in globals() else 'Dark',
                'mirror_runs': entry.get() if 'entry' in globals() else '1',
                'exp_runs': exp_entry.get() if 'exp_entry' in globals() else '1',
                'exp_stage': exp_stage_var.get() if 'exp_stage_var' in globals() else '1',
                'threads_runs': threads_entry.get() if 'threads_entry' in globals() else '1',
                'threads_difficulty': threads_difficulty_var.get() if 'threads_difficulty_var' in globals() else '20',
                'window_width': str(root.winfo_width()) if 'root' in globals() else '433',
                'window_height': str(root.winfo_height()) if 'root' in globals() else '344',
                'filter_noise': str(filtered_messages_enabled) if 'filtered_messages_enabled' in globals() else 'True',
                'github_owner': 'Kryxzort',
                'github_repo': 'GuiSirSquirrelAssistant',
                'auto_update': str(auto_update_var.get()) if 'auto_update_var' in globals() else 'False',
                'create_backups': str(create_backups_var.get()) if 'create_backups_var' in globals() else 'True',
                'update_notifications': str(update_notifications_var.get()) if 'update_notifications_var' in globals() else 'True',
                'kill_processes_on_exit': str(kill_processes_var.get()) if 'kill_processes_var' in globals() else 'False',
                'chain_threads_runs': chain_threads_entry.get() if 'chain_threads_entry' in globals() else '3',
                'chain_exp_runs': chain_exp_entry.get() if 'chain_exp_entry' in globals() else '2',
                'chain_mirror_runs': chain_mirror_entry.get() if 'chain_mirror_entry' in globals() else '1'
            }
        except Exception as e:
            error(f"Error setting up Settings section: {e}")
        
        # Save log filter settings if they exist
        try:
            if 'log_filters' in globals():
                config['LogFilters'] = {
                    'debug': str(log_filters['DEBUG'].get()),
                    'info': str(log_filters['INFO'].get()),
                    'warning': str(log_filters['WARNING'].get()),
                    'error': str(log_filters['ERROR'].get()),
                    'critical': str(log_filters['CRITICAL'].get())
                }
        except Exception as e:
            error(f"Error setting up LogFilters section: {e}")
        
        # Save module filter settings if they exist
        try:
            if 'module_filters' in globals() and 'LOG_MODULES' in globals():
                for module in LOG_MODULES:
                    config['ModuleFilters'][module.lower().replace(' ', '_')] = str(module_filters[module].get())
        except Exception as e:
            error(f"Error setting up ModuleFilters section: {e}")
        
        # Save keyboard shortcuts if they exist
        try:
            if 'shortcut_vars' in globals():
                config['Shortcuts'] = {
                    'mirror_dungeon': shortcut_vars['mirror_dungeon'].get(),
                    'exp': shortcut_vars['exp'].get(),
                    'threads': shortcut_vars['threads'].get(),
                    'battle': shortcut_vars['battle'].get(),
                    'call_function': shortcut_vars['call_function'].get(),
                    'terminate_functions': shortcut_vars['terminate_functions'].get(),
                    'chain_automation': shortcut_vars['chain_automation'].get()
                }
        except Exception as e:
            error(f"Error setting up Shortcuts section: {e}")
    
    try:
        # Make sure the config directory exists
        os.makedirs(CONFIG_DIR, exist_ok=True)
        
        with open(GUI_CONFIG_PATH, 'w') as f:
            config.write(f)
    except Exception as e:
        error(f"Error saving GUI config: {e}")

# Load configuration before creating UI elements
config = load_gui_config()
filtered_messages_enabled = config['Settings'].getboolean('filter_noise', True)

# Create log filter UI variables from config
log_filters = {
    "DEBUG": ctk.BooleanVar(value=config['LogFilters'].getboolean('debug', False)),
    "INFO": ctk.BooleanVar(value=config['LogFilters'].getboolean('info', False)),
    "WARNING": ctk.BooleanVar(value=config['LogFilters'].getboolean('warning', True)),
    "ERROR": ctk.BooleanVar(value=config['LogFilters'].getboolean('error', True)),
    "CRITICAL": ctk.BooleanVar(value=config['LogFilters'].getboolean('critical', True))
}

# Create module filter UI variables from config
module_filters = {}
for module in LOG_MODULES:
    key = module.lower().replace(' ', '_')
    module_filters[module] = ctk.BooleanVar(value=config['ModuleFilters'].getboolean(key, True))

# Create keyboard shortcut variables from config
shortcut_vars = {
    'mirror_dungeon': ctk.StringVar(value=config['Shortcuts'].get('mirror_dungeon', 'ctrl+q')),
    'exp': ctk.StringVar(value=config['Shortcuts'].get('exp', 'ctrl+e')),
    'threads': ctk.StringVar(value=config['Shortcuts'].get('threads', 'ctrl+r')),
    'battle': ctk.StringVar(value=config['Shortcuts'].get('battle', 'ctrl+t')),
    'call_function': ctk.StringVar(value=config['Shortcuts'].get('call_function', 'ctrl+g')),
    'terminate_functions': ctk.StringVar(value=config['Shortcuts'].get('terminate_functions', 'ctrl+shift+g')),
    'chain_automation': ctk.StringVar(value=config['Shortcuts'].get('chain_automation', 'ctrl+b'))
}

# MOVED: Update-related variables (MUST be global for auto-update to work without Settings tab)
auto_update_var = ctk.BooleanVar(value=config['Settings'].getboolean('auto_update', False))
create_backups_var = ctk.BooleanVar(value=config['Settings'].getboolean('create_backups', True))
update_notifications_var = ctk.BooleanVar(value=config['Settings'].getboolean('update_notifications', True))
kill_processes_var = ctk.BooleanVar(value=config['Settings'].getboolean('kill_processes_on_exit', False))

# MOVED: Global update callback functions (MUST be global for auto-update to work)
def check_updates_callback(success, message, update_available):
    """Callback for update checks - MUST be global for auto-update"""
    global is_update_available
    is_update_available = update_available
    
    # Update the status label if it exists (Settings tab loaded)
    if 'update_status_label' in globals():
        update_status_label.configure(text=f"Update Status: {message}")
        
        # Show/hide update button based on availability
        if update_available:
            update_now_button.pack(pady=(5, 0))
        else:
            update_now_button.pack_forget()
    
    # Show title notification if both update is available AND notifications are enabled
    if update_available and update_notifications_var.get():
        root.title(f"{original_title} (Outdated Version)")
    else:
        root.title(original_title)

def check_updates_action():
    """Check for updates manually"""
    if 'update_status_label' in globals():
        update_status_label.configure(text="Update Status: Checking for updates...")
    check_for_updates("Kryxzort", "GuiSirSquirrelAssistant", callback=check_updates_callback)

def perform_update():
    """Perform the update process"""
    if 'update_status_label' in globals():
        update_status_label.configure(text="Update Status: Updating...")
    
    def update_finished_callback(success, message):
        if not success and 'update_status_label' in globals():
            update_status_label.configure(text=f"Update Status: {message}")
            messagebox.showerror("Update Failed", message)
    
    auto_update(
        "Kryxzort", 
        "GuiSirSquirrelAssistant", 
        create_backup=create_backups_var.get(),
        callback=update_finished_callback
    )

# =====================================================================
# OPTIMIZED LOGGING DISPLAY HANDLER
# =====================================================================

# Simplified and optimized logging handler
class OptimizedLogHandler(logging.Handler):
    """Optimized log handler that combines file monitoring and text display"""
    
    def __init__(self, text_widget, level_filters, module_filters):
        super().__init__()
        self.text_widget = text_widget
        self.level_filters = level_filters
        self.module_filters = module_filters
        self.queue = queue.Queue()
        self.running = True
        self.update_thread = Thread(target=self._update_widget, daemon=True)
        self.update_thread.start()
        
        # Set formatter for the handler
        self.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        
        # File monitoring
        self.log_file_path = LOG_FILENAME
        self.last_position = 0
        
    def emit(self, record):
        """Put log message in queue for the update thread"""
        if self.running:
            self.queue.put(record)
    
    def _update_widget(self):
        """Thread that updates the text widget with new log messages"""
        while self.running:
            try:
                # Get log message from queue (with timeout to allow thread to exit)
                record = self.queue.get(block=True, timeout=0.2)
                
                # Check if we should display this level and module
                if self._should_show_record(record):
                    # Format the message and schedule GUI update
                    msg = self.format(record)
                    if self.running:  # Check again before scheduling
                        root.after(0, self._append_log, msg)
                
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                # Avoid crashing the thread on any error
                try:
                    print(f"Error in log update thread: {e}")
                except:
                    pass
    
    def _should_show_record(self, record):
        """Check if record should be displayed based on filters"""
        level_name = record.levelname
        module_name = self._get_module_name(record.name)
        
        # Check both level and module filters
        if level_name in self.level_filters and module_name in self.module_filters:
            show_level = self.level_filters[level_name].get()
            show_module = self.module_filters[module_name].get()
            
            return show_level and show_module and self._should_show_message(record.getMessage())
        return False
    
    def _get_module_name(self, logger_name):
        """Map logger name to module name for filtering"""
        # No need to handle __main__ conversion anymore since we use "GUI" directly
        for module, pattern in LOG_MODULES.items():
            if pattern == logger_name:
                return module
        
        return "Other"
    
    def _should_show_message(self, message):
        """Check if the message should be shown or filtered out as noise"""
        if not filtered_messages_enabled:
            return True
            
        # Check if the message contains any filtered message
        for filtered_msg in FILTERED_MESSAGES:
            if filtered_msg in message:
                return False
                
        # Check for loaded pre-checked statuses pattern
        if re.match(r"Loaded pre-checked statuses: .+", message):
            return False
            
        return True
    
    def _append_log(self, msg):
        """Append log message to the text widget"""
        try:
            if self.text_widget and self.running:
                self.text_widget.configure(state="normal")
                self.text_widget.insert("end", msg + "\n")
                self.text_widget.see("end")
                self.text_widget.configure(state="disabled")
        except Exception:
            pass  # Silently ignore errors during shutdown
    
    def close(self):
        """Clean up resources when handler is closed"""
        self.running = False
        if hasattr(self, 'update_thread') and self.update_thread.is_alive():
            self.update_thread.join(timeout=0.1)  # Shorter timeout
        super().close()

    def filter(self, record):
        """Don't use standard filtering"""
        return True

# =====================================================================
# STATUS SELECTION MANAGEMENT
# =====================================================================

# Status selection management functions
@safe_execute
def save_selected_statuses():
    """Save selected checkboxes to file with most recent at the bottom"""
    # Safety check - this shouldn't happen anymore but just in case
    if not checkbox_vars:
        warning("Attempted to save statuses before checkbox data was loaded")
        return
    
    selected = [name for name, var in checkbox_vars.items() if var.get()]
    
    # Try to read existing selections to determine order
    try:
        with open(STATUS_SELECTION_PATH, "r") as f:
            existing_selections = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        existing_selections = []
    
    # Remove any selections that are no longer selected
    existing_selections = [s for s in existing_selections if s in selected]
    
    # Add new selections at the bottom
    for s in selected:
        if s in existing_selections:
            # Move to the end by removing and re-adding
            existing_selections.remove(s)
            existing_selections.append(s)
        else:
            # New selection, add at the end
            existing_selections.append(s)
    
    # Save the updated selections
    with open(STATUS_SELECTION_PATH, "w") as f:
        f.write("\n".join(existing_selections))
    
    info(f"Saved selected statuses: {existing_selections}")

def on_checkbox_toggle(changed_option):
    """Handle checkbox toggle events"""
    save_selected_statuses()
    info(f"Status toggled: {changed_option}")

# =====================================================================
# UI INTERACTION FUNCTIONS
# =====================================================================

# UI interaction functions
def toggle_expand(frame, arrow_var):
    """Toggle expansion of frames"""
    if frame.winfo_ismapped():
        frame.pack_forget()
        arrow_var.set("▶")
    else:
        frame.pack(pady=(2, 8), fill="x")
        arrow_var.set("▼")

# Dropdown management functions
@safe_execute
def update_json_from_dropdown(status):
    """Update JSON data from dropdown selections"""
    entries = dropdown_vars[status]
    updated = {}
    for i, var in enumerate(entries):
        val = var.get()
        if val != "None":
            updated[sinner_key(val)] = i + 1
    squad_data[status] = updated
    save_json()
    threading.Thread(target=delayed_slow_sync, daemon=True).start()
    debug(f"Updated squad data for status: {status}")

def dropdown_callback(status, index, *_):
    """Handle dropdown selection changes"""
    try:
        new_val = dropdown_vars[status][index].get()
        if new_val == "None":
            update_json_from_dropdown(status)
            return

        # Check if duplicate exists
        for i, var in enumerate(dropdown_vars[status]):
            if i != index and var.get() == new_val:
                # Swap with old value from slow_squad
                old_key = next((k for k, v in slow_squad_data.get(status, {}).items() if v == index + 1), None)
                if old_key:
                    old_pretty = next((x for x in SINNER_LIST if sinner_key(x) == old_key), "None")
                    var.set(old_pretty)
                break

        update_json_from_dropdown(status)
    except Exception as e:
        error(f"Error in dropdown callback: {e}")

# =====================================================================
# OPTIMIZED PROCESS MANAGEMENT FUNCTIONS
# =====================================================================

# Unified process termination function
def terminate_process(proc, name):
    """Unified process termination with error handling"""
    if proc:
        try:
            os.kill(proc.pid, signal.SIGTERM)
            info(f"Terminated {name} process (PID: {proc.pid})")
            return True
        except Exception as e:
            error(f"Failed to kill {name} process: {e}")
    return False

# Process management functions with unified error handling
def kill_bot():
    """Kill Mirror Dungeon subprocess"""
    global process
    if terminate_process(process, "Mirror Dungeon"):
        process = None
    if 'start_button' in globals():
        start_button.configure(text="Start")

def kill_exp_bot():
    """Kill Exp subprocess"""
    global exp_process
    if terminate_process(exp_process, "Exp"):
        exp_process = None
    if 'exp_start_button' in globals():
        exp_start_button.configure(text="Start")

def kill_threads_bot():
    """Kill Threads subprocess"""
    global threads_process
    if terminate_process(threads_process, "Threads"):
        threads_process = None
    if 'threads_start_button' in globals():
        threads_start_button.configure(text="Start")

def kill_function_runner():
    """Kill Function Runner subprocess"""
    global function_process, function_process_list
    if terminate_process(function_process, "Function Runner"):
        function_process = None
    
    # Also terminate any processes in the list
    for proc in function_process_list[:]:  # Use a copy of the list for iteration
        if proc and proc.poll() is None:  # Check if process is still running
            if terminate_process(proc, "Function Runner"):
                function_process_list.remove(proc)
    
    # Update UI if buttons exist
    if 'function_terminate_button' in globals():
        function_terminate_button.configure(state="disabled")

# Unified process start function with shared validation
def start_automation_process(process_type, command_args, button_ref, process_ref_name):
    """Unified function to start automation processes"""
    global process, exp_process, threads_process
    
    # Check for process conflicts
    if check_process_conflict(process_type):
        return
    
    # Check if this specific process is already running (toggle stop)
    current_process = globals().get(process_ref_name)
    if current_process and button_ref.cget("text") == "Stop":
        if process_type == "Mirror Dungeon":
            kill_bot()
        elif process_type == "Exp":
            kill_exp_bot()
        elif process_type == "Threads":
            kill_threads_bot()
        return
    
    # Create environment variables with correct paths
    env = os.environ.copy()
    env['PYTHONPATH'] = BASE_PATH + os.pathsep + os.path.join(BASE_PATH, 'src')
    
    # Launch process with appropriate command
    try:
        new_process = subprocess.Popen(command_args, env=env)
        
        # Update global process reference
        globals()[process_ref_name] = new_process
        
        button_ref.configure(text="Stop")
        info(f"Started {process_type} automation (PID: {new_process.pid})")
        
        # Save the configuration
        save_gui_config()
        
    except Exception as e:
        error(f"Failed to start {process_type}: {e}")
        messagebox.showerror("Error", f"Failed to start {process_type}: {e}")

# Process start functions - now much simpler
def start_run():
    """Start Mirror Dungeon automation"""
    try:
        count = int(entry.get())
    except ValueError:
        messagebox.showerror("Invalid Input", "Enter a valid number of runs.")
        warning("Invalid number of runs entered for Mirror Dungeon")
        return
        
    save_selected_statuses()
    
    # Determine command based on execution mode
    if getattr(sys, 'frozen', False):
        command_args = [PYTHON_CMD, "-m", "src.compiled_runner", str(count)]
    else:
        command_args = [sys.executable, MIRROR_SCRIPT_PATH, str(count)]
    
    start_automation_process("Mirror Dungeon", command_args, start_button, "process")

def start_exp_run():
    """Start Exp automation"""
    try:
        runs = int(exp_entry.get())
        stage_value = exp_stage_var.get()
        
        # Handle numeric stages with validation
        if stage_value != "latest":
            stage = int(stage_value)
            if runs < 1 or stage < 1 or stage > 7:
                messagebox.showerror("Invalid Input", "Enter a valid number of runs and stage (1-7 or 'latest').")
                warning(f"Invalid input: runs={runs}, stage={stage_value}")
                return
        
        # Just validate runs for any stage value
        if runs < 1:
            messagebox.showerror("Invalid Input", "Enter a valid number of runs.")
            warning(f"Invalid input: runs={runs}")
            return
            
    except ValueError:
        messagebox.showerror("Invalid Input", "Enter valid numbers.")
        warning("Invalid numeric input for Exp automation")
        return

    # Determine command based on execution mode
    if getattr(sys, 'frozen', False):
        command_args = [PYTHON_CMD, "-m", "src.exp_runner", str(runs), stage_value]  # Pass stage_value directly
    else:
        command_args = [sys.executable, EXP_SCRIPT_PATH, str(runs), stage_value]  # Pass stage_value directly
    
    start_automation_process("Exp", command_args, exp_start_button, "exp_process")

def start_threads_run():
    """Start Threads automation"""
    try:
        runs = int(threads_entry.get())
        difficulty = int(threads_difficulty_var.get())
        if runs < 1 or difficulty not in [20, 30, 40, 50]:
            messagebox.showerror("Invalid Input", "Enter a valid number of runs and difficulty (20, 30, 40, or 50).")
            warning(f"Invalid input: runs={runs}, difficulty={difficulty}")
            return
    except ValueError:
        messagebox.showerror("Invalid Input", "Enter valid numbers.")
        warning("Invalid numeric input for Threads automation")
        return
    
    # Ensure the threads script path is correct
    if not os.path.exists(THREADS_SCRIPT_PATH):
        error(f"Threads runner script not found at: {THREADS_SCRIPT_PATH}")
        messagebox.showerror("Error", f"Could not find threads_runner.py in src directory. Please ensure it exists.")
        return
    
    # Determine command based on execution mode
    if getattr(sys, 'frozen', False):
        command_args = [PYTHON_CMD, "-m", "src.threads_runner", str(runs), str(difficulty)]
    else:
        command_args = [sys.executable, THREADS_SCRIPT_PATH, str(runs), str(difficulty)]
    
    start_automation_process("Threads", command_args, threads_start_button, "threads_process")

# =====================================================================
# CHAIN AUTOMATION FUNCTIONS
# =====================================================================

def start_chain_automation():
    """Start chain automation with Threads -> Exp -> Mirror sequence"""
    global chain_running, chain_queue, current_chain_step
    
    if chain_running:
        # Stop chain if already running
        stop_chain_automation()
        return
    
    # Check for process conflicts
    if check_process_conflict("Chain Automation"):
        return
    
    # Parse chain inputs
    try:
        threads_runs = int(chain_threads_entry.get()) if chain_threads_entry.get().strip() else 0
        exp_runs = int(chain_exp_entry.get()) if chain_exp_entry.get().strip() else 0
        mirror_runs = int(chain_mirror_entry.get()) if chain_mirror_entry.get().strip() else 0
    except ValueError:
        messagebox.showerror("Invalid Input", "Enter valid numbers for chain automation.")
        return
    
    # Build chain queue
    chain_queue = []
    if threads_runs > 0:
        chain_queue.append(("Threads", threads_runs))
    if exp_runs > 0:
        chain_queue.append(("Exp", exp_runs))
    if mirror_runs > 0:
        chain_queue.append(("Mirror", mirror_runs))
    
    if not chain_queue:
        messagebox.showerror("Invalid Input", "At least one automation type must have a number greater than 0.")
        return
    
    # Start chain
    chain_running = True
    current_chain_step = 0
    chain_start_button.configure(text="Stop Chain")
    chain_status_label.configure(text="Chain Status: Starting...")
    
    # Save current UI settings to config (like individual automations do)
    save_gui_config()
    
    info(f"Starting chain automation: {chain_queue}")
    run_next_chain_step()

def stop_chain_automation():
    """Stop chain automation"""
    global chain_running
    
    chain_running = False
    
    # Stop any currently running processes
    kill_bot()
    kill_exp_bot()
    kill_threads_bot()
    
    chain_start_button.configure(text="Start Chain")
    chain_status_label.configure(text="Chain Status: Stopped")
    info("Chain automation stopped")

def run_next_chain_step():
    """Run the next step in the chain automation"""
    global current_chain_step, chain_running
    
    if not chain_running or current_chain_step >= len(chain_queue):
        # Chain completed or stopped
        chain_running = False
        chain_start_button.configure(text="Start Chain")
        chain_status_label.configure(text="Chain Status: Completed")
        info("Chain automation completed")
        return
    
    # Get current step
    automation_type, runs = chain_queue[current_chain_step]
    chain_status_label.configure(text=f"Chain Status: Running {automation_type} ({runs} runs) - Step {current_chain_step + 1}/{len(chain_queue)}")
    
    # Save selected statuses for Mirror automation
    if automation_type == "Mirror":
        save_selected_statuses()
    
    # Start the appropriate automation
    try:
        env = os.environ.copy()
        env['PYTHONPATH'] = BASE_PATH + os.pathsep + os.path.join(BASE_PATH, 'src')
        
        if automation_type == "Threads":
            difficulty = int(threads_difficulty_var.get())
            if getattr(sys, 'frozen', False):
                command_args = [PYTHON_CMD, "-m", "src.threads_runner", str(runs), str(difficulty)]
            else:
                command_args = [sys.executable, THREADS_SCRIPT_PATH, str(runs), str(difficulty)]
            
            global threads_process
            threads_process = subprocess.Popen(command_args, env=env)
            info(f"Chain: Started Threads automation ({runs} runs, difficulty {difficulty})")
            
        elif automation_type == "Exp":
            stage = int(exp_stage_var.get())
            if getattr(sys, 'frozen', False):
                command_args = [PYTHON_CMD, "-m", "src.exp_runner", str(runs), str(stage)]
            else:
                command_args = [sys.executable, EXP_SCRIPT_PATH, str(runs), str(stage)]
            
            global exp_process
            exp_process = subprocess.Popen(command_args, env=env)
            info(f"Chain: Started Exp automation ({runs} runs, stage {stage})")
            
        elif automation_type == "Mirror":
            if getattr(sys, 'frozen', False):
                command_args = [PYTHON_CMD, "-m", "src.compiled_runner", str(runs)]
            else:
                command_args = [sys.executable, MIRROR_SCRIPT_PATH, str(runs)]
            
            global process
            process = subprocess.Popen(command_args, env=env)
            info(f"Chain: Started Mirror automation ({runs} runs)")
        
        # Move to next step
        current_chain_step += 1
        
        # Monitor this step completion
        monitor_chain_step()
        
    except Exception as e:
        error(f"Failed to start {automation_type} in chain: {e}")
        stop_chain_automation()

def monitor_chain_step():
    """Monitor the current chain step and proceed when done"""
    global chain_running, process, exp_process, threads_process
    
    if not chain_running:
        return
    
    # Get current step info
    if current_chain_step == 0 or current_chain_step > len(chain_queue):
        # No step started yet or chain completed
        return
    
    automation_type, runs = chain_queue[current_chain_step - 1]
    
    # Check if current process is done
    current_process = None
    process_finished = False
    
    if automation_type == "Threads":
        current_process = threads_process
        if threads_process is None or threads_process.poll() is not None:
            process_finished = True
            if threads_process and threads_process.poll() is not None:
                threads_process = None  # Clean up
    elif automation_type == "Exp":
        current_process = exp_process
        if exp_process is None or exp_process.poll() is not None:
            process_finished = True
            if exp_process and exp_process.poll() is not None:
                exp_process = None  # Clean up
    elif automation_type == "Mirror":
        current_process = process
        if process is None or process.poll() is not None:
            process_finished = True
            if process and process.poll() is not None:
                process = None  # Clean up
    
    if process_finished:
        info(f"Chain: {automation_type} automation completed, moving to next step")
        
        # Start next step after a small delay
        root.after(2000, run_next_chain_step)  # 2 second delay between steps
    else:
        # Still running, check again in 1 second
        root.after(1000, monitor_chain_step)

# =====================================================================
# FUNCTION RUNNER FUNCTIONS
# =====================================================================

def call_function():
    """Call a function using function_runner.py"""
    global function_process_list
    
    # Get the function to call
    function_name = function_entry.get().strip()
    if not function_name:
        messagebox.showerror("Invalid Input", "Please enter a function to call.")
        warning("Empty function name provided")
        return
    
    try:
        # Create an environment with the correct paths
        env = os.environ.copy()
        env['PYTHONPATH'] = BASE_PATH + os.pathsep + os.path.join(BASE_PATH, 'src')
        
        # Launch with the appropriate command
        if getattr(sys, 'frozen', False):
            command_args = [PYTHON_CMD, "-m", "src.function_runner", function_name, "--listen-stdin"]
        else:
            command_args = [sys.executable, FUNCTION_RUNNER_PATH, function_name, "--listen-stdin"]
        
        new_process = subprocess.Popen(command_args, env=env)
        
        # Add to the list of function processes
        function_process_list.append(new_process)
        function_terminate_button.configure(state="normal")
        info(f"Called function: {function_name} (PID: {new_process.pid})")
        
    except Exception as e:
        error(f"Failed to call function: {e}")
        messagebox.showerror("Error", f"Failed to call function: {e}")

def start_battle():
    """Start a battle directly using the dedicated battler.py script"""
    global battle_process
    
    # Check if there's already a battle process running
    if battle_process is not None and battle_process.poll() is None:
        # Process is still running, terminate it
        try:
            os.kill(battle_process.pid, signal.SIGTERM)
            info(f"Terminated battle process (PID: {battle_process.pid}) via battle shortcut")
            battle_process = None
            return
        except Exception as e:
            error(f"Failed to kill battle process: {e}")
    
    # No battle process running or it's already completed, start a new battle
    try:
        # Create environment variables with correct paths
        env = os.environ.copy()
        env['PYTHONPATH'] = os.pathsep.join([BASE_PATH, os.path.join(BASE_PATH, 'src')])
        
        # Launch with the appropriate command
        if getattr(sys, 'frozen', False):
            # If frozen (exe), launch the script using the bundled Python
            new_battle_process = subprocess.Popen(
                [PYTHON_CMD, "-m", "src.battler"],
                env=env
            )
        else:
            # If script, use the regular Python command
            new_battle_process = subprocess.Popen(
                [sys.executable, BATTLER_SCRIPT_PATH],
                env=env
            )
        
        # Only track in battle_process, not in function_process_list
        battle_process = new_battle_process
        info(f"Started battle via dedicated battler.py (PID: {new_battle_process.pid})")
        
    except Exception as e:
        error(f"Failed to start battle: {e}")
        messagebox.showerror("Error", f"Failed to start battle: {e}")

def toggle_chain_automation():
    """Toggle chain automation via keyboard shortcut"""
    if chain_running:
        stop_chain_automation()
    else:
        start_chain_automation()

def call_function_shortcut():
    """Trigger the call function button via keyboard shortcut"""
    call_function()
    
def terminate_functions_shortcut():
    """Terminate all function processes via keyboard shortcut"""
    kill_function_runner()
    info("Terminated all function processes via keyboard shortcut")

# Button toggle functions
def toggle_button():
    """Toggle Mirror Dungeon button state"""
    if start_button.cget("text") == "Start":
        start_run()
    else:
        kill_bot()

def toggle_exp_button():
    """Toggle Exp button state"""
    if exp_start_button.cget("text") == "Start":
        start_exp_run()
    else:
        kill_exp_bot()

def toggle_threads_button():
    """Toggle Threads button state"""
    if threads_start_button.cget("text") == "Start":
        start_threads_run()
    else:
        kill_threads_bot()

# =====================================================================
# THEME APPLICATION AND KEYBOARD SHORTCUTS
# =====================================================================

# Theme application function
def apply_theme():
    """Apply the selected theme by restarting with theme_restart.py"""
    theme_name = theme_var.get()
    if theme_name in THEMES:
        # Show feedback immediately
        theme_label = ctk.CTkLabel(
            master=root, 
            text=f"Applying {theme_name} theme...",
            font=ctk.CTkFont(size=14)
        )
        theme_label.place(relx=0.5, rely=0.5, anchor="center")
        root.update_idletasks()  # Force update to show message
        
        # Save the current configuration before restarting
        save_gui_config()
        
        info(f"Applying theme: {theme_name} - Restarting application...")
        
        try:
            # Start theme_restart.py with the theme name and specify "Settings" tab
            subprocess.Popen([sys.executable, THEME_RESTART_PATH, theme_name, "Settings"])
            
            # Short delay then exit
            root.after(100, lambda: os._exit(0))
        except Exception as e:
            error(f"Error applying theme: {e}")
            messagebox.showerror("Error", f"Failed to apply theme: {e}")

# Keyboard shortcut management
def register_keyboard_shortcuts():
    """Register keyboard shortcuts based on current settings"""
    # Unhook all existing keyboard shortcuts
    keyboard.unhook_all()
    
    try:
        # Register the shortcuts from the configuration
        keyboard.add_hotkey(shortcut_vars['mirror_dungeon'].get(), toggle_button)
        keyboard.add_hotkey(shortcut_vars['exp'].get(), toggle_exp_button)
        keyboard.add_hotkey(shortcut_vars['threads'].get(), toggle_threads_button)
        keyboard.add_hotkey(shortcut_vars['battle'].get(), start_battle)
        keyboard.add_hotkey(shortcut_vars['call_function'].get(), call_function_shortcut)
        keyboard.add_hotkey(shortcut_vars['terminate_functions'].get(), terminate_functions_shortcut)
        keyboard.add_hotkey(shortcut_vars['chain_automation'].get(), toggle_chain_automation)
        
        debug(f"Registered keyboard shortcuts: {shortcut_vars['mirror_dungeon'].get()} (Mirror), "
              f"{shortcut_vars['exp'].get()} (Exp), {shortcut_vars['threads'].get()} (Threads), "
              f"{shortcut_vars['battle'].get()} (Battle), {shortcut_vars['call_function'].get()} (Call Function), "
              f"{shortcut_vars['terminate_functions'].get()} (Terminate Functions), "
              f"{shortcut_vars['chain_automation'].get()} (Chain Automation)")
    except Exception as e:
        error(f"Error registering keyboard shortcuts: {e}")
        messagebox.showerror("Invalid Shortcut", f"Failed to register shortcuts: {e}\nPlease check your shortcut format.")

# Initialize theme settings
theme_var = ctk.StringVar(value=config['Settings'].get('theme', 'Dark'))

# Make sure theme is one of the valid ones
if theme_var.get() not in THEMES:
    theme_var.set("Dark")
    
ctk.set_appearance_mode(THEMES[theme_var.get()]["mode"])
ctk.set_default_color_theme(THEMES[theme_var.get()]["theme"])

# Set window size from config
window_width = config['Settings'].getint('window_width', 433)
window_height = config['Settings'].getint('window_height', 344)
root.geometry(f"{window_width}x{window_height}")

# Performance improvement: Disable complex logging at startup
info("GUI initialized")

# =====================================================================
# TAB LAYOUT AND UI SETUP
# =====================================================================

# Tab layout
tabs = ctk.CTkTabview(master=root, width=window_width-40, height=window_height-60)
tabs.pack(padx=20, pady=20, fill="both", expand=True)

# Create all tabs
tab_md = tabs.add("Mirror Dungeon")
tab_exp = tabs.add("Exp")
tab_threads = tabs.add("Threads")
tab_others = tabs.add("Others")  # The new "Others" tab
tab_settings = tabs.add("Settings")
tab_help = tabs.add("Help")
tab_logs = tabs.add("Logs")

# FIXED: Handle theme restart and Settings tab loading
is_theme_restart = len(sys.argv) > 1 and sys.argv[1] in THEMES.keys()
load_settings_on_startup = is_theme_restart and len(sys.argv) > 2 and sys.argv[2] == "Settings"

# Add tab change event handler for lazy loading
def on_tab_changed():
    """Handle tab changes and lazy load content"""
    current_tab = tabs.get()
    
    if current_tab == "Settings" and not settings_tab_loaded:
        load_settings_tab()
    elif current_tab == "Logs" and not logs_tab_loaded:
        load_logs_tab()

tabs.configure(command=on_tab_changed)
        
# Setting up the Mirror Dungeon tab
scroll = ctk.CTkScrollableFrame(master=tab_md)
scroll.pack(fill="both", expand=True)

ctk.CTkLabel(scroll, text="Number of Runs:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 0))
entry = ctk.CTkEntry(scroll)
entry.pack(pady=(0, 5))
entry.insert(0, config['Settings'].get('mirror_runs', '1'))  # Set from config

start_button = ctk.CTkButton(scroll, text="Start", command=toggle_button)
start_button.pack(pady=(0, 15))

# Setting up the Exp tab
exp_scroll = ctk.CTkScrollableFrame(master=tab_exp)
exp_scroll.pack(fill="both", expand=True)

ctk.CTkLabel(exp_scroll, text="Number of Runs:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 0))
exp_entry = ctk.CTkEntry(exp_scroll)
exp_entry.pack(pady=(0, 5))
exp_entry.insert(0, config['Settings'].get('exp_runs', '1'))  # Set from config

ctk.CTkLabel(exp_scroll, text="Choose Stage:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 0))
exp_stage_var = ctk.StringVar(value=config['Settings'].get('exp_stage', '1'))  # Set from config
exp_stage_dropdown = ctk.CTkOptionMenu(
    master=exp_scroll,
    variable=exp_stage_var,
    values=["1", "2", "3", "4", "5", "6", "7", "latest"],
    width=200,
    font=ctk.CTkFont(size=16)
)
exp_stage_dropdown.pack(pady=(0, 15))

exp_start_button = ctk.CTkButton(exp_scroll, text="Start", command=toggle_exp_button)
exp_start_button.pack(pady=(0, 15))

# Setting up the Threads tab
threads_scroll = ctk.CTkScrollableFrame(master=tab_threads)
threads_scroll.pack(fill="both", expand=True)

ctk.CTkLabel(threads_scroll, text="Number of Runs:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 0))
threads_entry = ctk.CTkEntry(threads_scroll)
threads_entry.pack(pady=(0, 5))
threads_entry.insert(0, config['Settings'].get('threads_runs', '1'))  # Set from config

ctk.CTkLabel(threads_scroll, text="Choose Difficulty:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 0))
threads_difficulty_var = ctk.StringVar(value=config['Settings'].get('threads_difficulty', '20'))  # Set from config
threads_difficulty_dropdown = ctk.CTkOptionMenu(
    master=threads_scroll,
    variable=threads_difficulty_var,
    values=["20", "30", "40", "50"],
    width=200,
    font=ctk.CTkFont(size=16)
)
threads_difficulty_dropdown.pack(pady=(0, 15))

threads_start_button = ctk.CTkButton(threads_scroll, text="Start", command=toggle_threads_button)
threads_start_button.pack(pady=(0, 15))

# =====================================================================
# OTHERS TAB - UPDATED WITH CHAIN FUNCTIONS
# =====================================================================

# Setting up the Others tab
others_scroll = ctk.CTkScrollableFrame(master=tab_others)
others_scroll.pack(fill="both", expand=True)

# Chain Functions section
ctk.CTkLabel(others_scroll, text="Chain Functions", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 0))

chain_help = ctk.CTkLabel(
    others_scroll, 
    text="Run automations in sequence: Threads → Exp → Mirror. Enter 0 to skip.", 
    font=ctk.CTkFont(size=12), 
    text_color="gray"
)
chain_help.pack(pady=(0, 10))

# Chain input frame
chain_frame = ctk.CTkFrame(others_scroll)
chain_frame.pack(pady=(0, 10), fill="x", padx=20)

# Threads input
threads_chain_frame = ctk.CTkFrame(chain_frame)
threads_chain_frame.pack(fill="x", pady=5)
ctk.CTkLabel(threads_chain_frame, text="Threads Runs:", width=100).pack(side="left", padx=(10, 5))
chain_threads_entry = ctk.CTkEntry(threads_chain_frame, width=80)
chain_threads_entry.pack(side="left", padx=(0, 10))
chain_threads_entry.insert(0, config['Settings'].get('chain_threads_runs', '3'))

# Exp input
exp_chain_frame = ctk.CTkFrame(chain_frame)
exp_chain_frame.pack(fill="x", pady=5)
ctk.CTkLabel(exp_chain_frame, text="Exp Runs:", width=100).pack(side="left", padx=(10, 5))
chain_exp_entry = ctk.CTkEntry(exp_chain_frame, width=80)
chain_exp_entry.pack(side="left", padx=(0, 10))
chain_exp_entry.insert(0, config['Settings'].get('chain_exp_runs', '2'))

# Mirror input
mirror_chain_frame = ctk.CTkFrame(chain_frame)
mirror_chain_frame.pack(fill="x", pady=5)
ctk.CTkLabel(mirror_chain_frame, text="Mirror Runs:", width=100).pack(side="left", padx=(10, 5))
chain_mirror_entry = ctk.CTkEntry(mirror_chain_frame, width=80)
chain_mirror_entry.pack(side="left", padx=(0, 10))
chain_mirror_entry.insert(0, config['Settings'].get('chain_mirror_runs', '1'))

# Chain control buttons
chain_control_frame = ctk.CTkFrame(others_scroll)
chain_control_frame.pack(pady=(0, 10))

chain_start_button = ctk.CTkButton(chain_control_frame, text="Start Chain", command=start_chain_automation, width=150)
chain_start_button.pack(side="left", padx=5)

# Chain status
chain_status_label = ctk.CTkLabel(
    others_scroll,
    text="Chain Status: Ready",
    font=ctk.CTkFont(size=12)
)
chain_status_label.pack(pady=(0, 15))

# Separator
separator1 = ctk.CTkFrame(others_scroll, height=2, width=300)
separator1.pack(pady=10)

# Function call section
ctk.CTkLabel(others_scroll, text="Call a function:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 0))
function_entry = ctk.CTkEntry(others_scroll, width=300)
function_entry.pack(pady=(0, 5))

# Help text for function call
function_help = ctk.CTkLabel(
    others_scroll, 
    text="Type any function from any module, e.g., core.battle or time.sleep(1)", 
    font=ctk.CTkFont(size=12), 
    text_color="gray"
)
function_help.pack(pady=(0, 10))

# Buttons for function control
function_call_button = ctk.CTkButton(others_scroll, text="Call", command=call_function, width=150)
function_call_button.pack(pady=(0, 5))

function_terminate_button = ctk.CTkButton(
    others_scroll, 
    text="Terminate All", 
    command=kill_function_runner, 
    width=150,
    state="disabled"  # Initially disabled until a function is called
)
function_terminate_button.pack(pady=(0, 15))

# =====================================================================
# LAZY-LOADED SETTINGS TAB - UPDATED WITH UPDATES SECTION
# =====================================================================

def load_settings_tab():
    """Lazy load the Settings tab content"""
    global settings_tab_loaded, update_status_label, update_now_button
    if settings_tab_loaded:
        return
    
    # Setting up the Settings tab
    settings_scroll = ctk.CTkScrollableFrame(master=tab_settings)
    settings_scroll.pack(fill="both", expand=True)

    # Reordered settings sections: 1. Team, 2. Assign Sinners, 3. Keyboard Shortcuts, 4. Updates, 5. Theme, 6. Kill Processes Toggle

    # 1. Team selection section
    ctk.CTkLabel(settings_scroll, text="Your Team", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 0))
    team_frame = ctk.CTkFrame(settings_scroll)
    team_frame.pack(pady=(0, 15))

    # Use existing checkbox_vars if they exist, otherwise create them
    if not checkbox_vars:
        # This shouldn't happen since we load at startup, but just in case
        load_checkbox_data()

    # Create UI elements using existing checkbox variables
    for name, row, col in TEAM_ORDER:
        var = checkbox_vars[name]  # Use existing variable
        chk = ctk.CTkCheckBox(
            master=team_frame,
            text=name.capitalize(),
            variable=var,
            command=lambda opt=name: on_checkbox_toggle(opt),
            font=ctk.CTkFont(size=16)
        )
        chk.grid(row=row, column=col, padx=5, pady=2, sticky="w")
        # Note: checkbox_vars[name] is already set, no need to set it again

    # 2. Sinner assignment section
    ctk.CTkLabel(settings_scroll, text="Assign Sinners to Name", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="center", pady=(0, 10))

    container = ctk.CTkFrame(settings_scroll)
    container.pack()

    load_json()

    for col_idx, group in enumerate(STATUS_COLUMNS):
        col = ctk.CTkFrame(container, fg_color="transparent")
        col.grid(row=0, column=col_idx, padx=15, sticky="n")

        for row_idx, status in enumerate(group):
            wrapper = ctk.CTkFrame(master=col, fg_color="transparent")
            wrapper.grid(row=row_idx, column=0, sticky="nw")

            arrow_var = ctk.StringVar(value="▶")
            full_text = ctk.StringVar(value=f"{arrow_var.get()} {status.capitalize()}")

            def make_toggle(stat=status, arrow=arrow_var):
                return lambda: toggle_expand(expand_frames[stat], arrow)

            btn = ctk.CTkButton(
                master=wrapper,
                textvariable=full_text,
                command=make_toggle(),
                width=200,
                height=38,
                font=ctk.CTkFont(size=18),
                anchor="w"
            )
            btn.pack(anchor="w", pady=(0, 6))

            arrow_var.trace_add("write", lambda *a, var=arrow_var, textvar=full_text, name=status: textvar.set(f"{var.get()} {name.capitalize()}"))

            frame = ctk.CTkFrame(master=wrapper, fg_color="transparent", corner_radius=0)
            expand_frames[status] = frame
            frame.pack_forget()

            dropdown_vars[status] = []
            default_order = squad_data.get(status, {})
            reverse_map = {v: k for k, v in default_order.items()}

            for i in range(12):
                row = ctk.CTkFrame(master=frame, fg_color="transparent")
                row.pack(pady=1, anchor="w")

                label = ctk.CTkLabel(
                    master=row,
                    text=f"{i+1}.",
                    anchor="e",
                    font=ctk.CTkFont(size=18),
                    text_color="#b0b0b0",
                    width=30
                )
                label.pack(side="left", padx=(0, 10))

                var = ctk.StringVar()
                raw_name = reverse_map.get(i + 1)
                pretty = next((x for x in SINNER_LIST if sinner_key(x) == raw_name), "None") if raw_name else "None"
                var.set(pretty)

                def bind_callback(status=status, idx=i, v=var):
                    v.trace_add("write", lambda *a: dropdown_callback(status, idx))

                dropdown = ctk.CTkOptionMenu(
                    master=row,
                    variable=var,
                    values=SINNER_LIST + ["None"],
                    width=160,
                    font=ctk.CTkFont(size=16)
                )
                dropdown.pack(side="left")
                bind_callback()
                dropdown_vars[status].append(var)

    # 3. Keyboard shortcut configuration section
    ctk.CTkLabel(settings_scroll, text="Keyboard Shortcuts", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 0))
    shortcuts_frame = ctk.CTkFrame(settings_scroll)
    shortcuts_frame.pack(pady=(0, 15), fill="x", padx=20)

    def update_shortcut(shortcut_type):
        """Update and apply a keyboard shortcut"""
        try:
            # Try to register the shortcuts to see if they're valid
            test_key = keyboard.add_hotkey(shortcut_vars[shortcut_type].get(), lambda: None)
            keyboard.remove_hotkey(test_key)
            
            # Save configuration
            save_gui_config()
            # Re-register all shortcuts
            register_keyboard_shortcuts()
            info(f"Updated {shortcut_type} shortcut to: {shortcut_vars[shortcut_type].get()}")
            
        except Exception as e:
            error(f"Invalid shortcut format: {e}")
            # Reset to previous value
            shortcut_vars[shortcut_type].set(config['Shortcuts'].get(shortcut_type))
            messagebox.showerror("Invalid Shortcut", f"Invalid shortcut format: {shortcut_vars[shortcut_type].get()}\n\nValid examples: ctrl+q, alt+s, shift+x")

    # Mirror Dungeon shortcut
    shortcut_row = ctk.CTkFrame(shortcuts_frame)
    shortcut_row.pack(fill="x", pady=5)
    ctk.CTkLabel(shortcut_row, text="Mirror Dungeon:", width=120, anchor="e").pack(side="left", padx=(10, 10))
    md_shortcut_entry = ctk.CTkEntry(shortcut_row, textvariable=shortcut_vars['mirror_dungeon'], width=100)
    md_shortcut_entry.pack(side="left", padx=(0, 10))
    ctk.CTkButton(shortcut_row, text="Apply", width=60, 
                  command=lambda: update_shortcut('mirror_dungeon')).pack(side="left")

    # Exp shortcut
    shortcut_row = ctk.CTkFrame(shortcuts_frame)
    shortcut_row.pack(fill="x", pady=5)
    ctk.CTkLabel(shortcut_row, text="Exp:", width=120, anchor="e").pack(side="left", padx=(10, 10))
    exp_shortcut_entry = ctk.CTkEntry(shortcut_row, textvariable=shortcut_vars['exp'], width=100)
    exp_shortcut_entry.pack(side="left", padx=(0, 10))
    ctk.CTkButton(shortcut_row, text="Apply", width=60, 
                  command=lambda: update_shortcut('exp')).pack(side="left")

    # Threads shortcut
    shortcut_row = ctk.CTkFrame(shortcuts_frame)
    shortcut_row.pack(fill="x", pady=5)
    ctk.CTkLabel(shortcut_row, text="Threads:", width=120, anchor="e").pack(side="left", padx=(10, 10))
    threads_shortcut_entry = ctk.CTkEntry(shortcut_row, textvariable=shortcut_vars['threads'], width=100)
    threads_shortcut_entry.pack(side="left", padx=(0, 10))
    ctk.CTkButton(shortcut_row, text="Apply", width=60, 
                  command=lambda: update_shortcut('threads')).pack(side="left")

    # Start Battle shortcut
    shortcut_row = ctk.CTkFrame(shortcuts_frame)
    shortcut_row.pack(fill="x", pady=5)
    ctk.CTkLabel(shortcut_row, text="Start Battle:", width=120, anchor="e").pack(side="left", padx=(10, 10))
    battle_shortcut_entry = ctk.CTkEntry(shortcut_row, textvariable=shortcut_vars['battle'], width=100)
    battle_shortcut_entry.pack(side="left", padx=(0, 10))
    ctk.CTkButton(shortcut_row, text="Apply", width=60, 
                  command=lambda: update_shortcut('battle')).pack(side="left")

    # Chain Automation shortcut
    shortcut_row = ctk.CTkFrame(shortcuts_frame)
    shortcut_row.pack(fill="x", pady=5)
    ctk.CTkLabel(shortcut_row, text="Chain Automation:", width=120, anchor="e").pack(side="left", padx=(10, 10))
    chain_shortcut_entry = ctk.CTkEntry(shortcut_row, textvariable=shortcut_vars['chain_automation'], width=100)
    chain_shortcut_entry.pack(side="left", padx=(0, 10))
    ctk.CTkButton(shortcut_row, text="Apply", width=60, 
                  command=lambda: update_shortcut('chain_automation')).pack(side="left")

    # Call Function shortcut
    shortcut_row = ctk.CTkFrame(shortcuts_frame)
    shortcut_row.pack(fill="x", pady=5)
    ctk.CTkLabel(shortcut_row, text="Call Function:", width=120, anchor="e").pack(side="left", padx=(10, 10))
    call_function_shortcut_entry = ctk.CTkEntry(shortcut_row, textvariable=shortcut_vars['call_function'], width=100)
    call_function_shortcut_entry.pack(side="left", padx=(0, 10))
    ctk.CTkButton(shortcut_row, text="Apply", width=60, 
                  command=lambda: update_shortcut('call_function')).pack(side="left")

    # Terminate Functions shortcut
    shortcut_row = ctk.CTkFrame(shortcuts_frame)
    shortcut_row.pack(fill="x", pady=5)
    ctk.CTkLabel(shortcut_row, text="Terminate Functions:", width=120, anchor="e").pack(side="left", padx=(10, 10))
    terminate_shortcut_entry = ctk.CTkEntry(shortcut_row, textvariable=shortcut_vars['terminate_functions'], width=100)
    terminate_shortcut_entry.pack(side="left", padx=(0, 10))
    ctk.CTkButton(shortcut_row, text="Apply", width=60, 
                  command=lambda: update_shortcut('terminate_functions')).pack(side="left")

    # Help text for keyboard shortcuts
    shortcut_help = ctk.CTkLabel(shortcuts_frame, text="Format examples: ctrl+q, alt+s, shift+x", 
                                font=ctk.CTkFont(size=12), text_color="gray")
    shortcut_help.pack(pady=(5, 10))

    # 4. MOVED: Updates section (from Others tab)
    if UPDATER_AVAILABLE:
        ctk.CTkLabel(settings_scroll, text="Updates", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 0))

        # Update options frame
        update_frame = ctk.CTkFrame(settings_scroll)
        update_frame.pack(pady=(0, 10), fill="x", padx=20)

        # Auto update toggle - consolidated option
        auto_update_checkbox = ctk.CTkCheckBox(
            update_frame,
            text="Auto update (checks and applies updates on startup)",
            variable=auto_update_var,
            command=lambda: save_gui_config()
        )
        auto_update_checkbox.pack(anchor="w", padx=10, pady=5)

        # Create backups toggle
        create_backups_checkbox = ctk.CTkCheckBox(
            update_frame,
            text="Create backups on update",
            variable=create_backups_var,
            command=lambda: save_gui_config()
        )
        create_backups_checkbox.pack(anchor="w", padx=10, pady=5)

        # Update notifications toggle
        update_notifications_checkbox = ctk.CTkCheckBox(
            update_frame,
            text="Show update notifications",
            variable=update_notifications_var,
            command=lambda: save_gui_config()
        )
        update_notifications_checkbox.pack(anchor="w", padx=10, pady=5)

        # Update status
        update_status_label = ctk.CTkLabel(
            settings_scroll,
            text="Update Status: Not checked",
            font=ctk.CTkFont(size=14)
        )
        update_status_label.pack(pady=(10, 5))

        # Update buttons frame to keep them together
        update_buttons_frame = ctk.CTkFrame(settings_scroll)
        update_buttons_frame.pack(pady=(5, 15))

        # Check for updates button
        check_updates_button = ctk.CTkButton(
            update_buttons_frame,
            text="Check for Updates",
            command=check_updates_action,
            width=150
        )
        check_updates_button.pack(pady=5)

        # Update now button (initially hidden)
        update_now_button = ctk.CTkButton(
            update_buttons_frame,
            text="Update Now",
            command=perform_update,
            width=150
        )
        # Initially hidden - will be shown when updates are available
        update_now_button.pack_forget()

    # 5. Theme selection section
    ctk.CTkLabel(settings_scroll, text="Theme", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 0))
    theme_dropdown = ctk.CTkOptionMenu(
        master=settings_scroll,
        variable=theme_var,
        values=list(THEMES.keys()),
        width=200,
        font=ctk.CTkFont(size=16),
        command=lambda _: apply_theme()
    )
    theme_dropdown.pack(pady=(0, 15))

    # 6. Kill processes on exit toggle
    ctk.CTkLabel(settings_scroll, text="Application Behavior", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 0))
    behavior_frame = ctk.CTkFrame(settings_scroll)
    behavior_frame.pack(pady=(0, 15), fill="x", padx=20)

    kill_processes_checkbox = ctk.CTkCheckBox(
        behavior_frame,
        text="Kill processes on exit (disable for faster closing)",
        variable=kill_processes_var,
        command=lambda: save_gui_config()
    )
    kill_processes_checkbox.pack(anchor="w", padx=10, pady=10)

    settings_tab_loaded = True

# =====================================================================
# RESPONSIVE LOGS TAB - FIXED FOR SCALING
# =====================================================================

def load_logs_tab():
    """Lazy load the Logs tab content with responsive design"""
    global logs_tab_loaded, log_handler
    if logs_tab_loaded:
        return

    # Main logs container
    logs_main_frame = ctk.CTkFrame(tab_logs)
    logs_main_frame.pack(fill="both", expand=True, padx=5, pady=5)

    # FIXED: Create responsive filter controls that scale with window size
    filter_container = ctk.CTkScrollableFrame(logs_main_frame, height=120)
    filter_container.pack(fill="x", padx=5, pady=(0, 5))

    # Filter header
    filter_header = ctk.CTkFrame(filter_container)
    filter_header.pack(fill="x", pady=(0, 5))
    
    ctk.CTkLabel(filter_header, text="Log Filters", 
                font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10)

    # Clean logs toggle
    filter_toggle = ctk.CTkSwitch(
        master=filter_header,
        text="Clean Logs",
        variable=ctk.BooleanVar(value=filtered_messages_enabled),
        command=lambda: toggle_filtered_messages(),
        onvalue=True,
        offvalue=False
    )
    filter_toggle.pack(side="right", padx=10)

    def toggle_filtered_messages():
        """Toggle filtering of noisy messages"""
        global filtered_messages_enabled
        filtered_messages_enabled = filter_toggle.get()
        save_gui_config()
        load_log_file(reload_all=True)  # Reload logs with new filter setting

    # FIXED: Responsive filter grid that wraps properly
    filters_main_frame = ctk.CTkFrame(filter_container)
    filters_main_frame.pack(fill="x", expand=True, padx=5, pady=5)

    # Level filters section
    levels_frame = ctk.CTkFrame(filters_main_frame)
    levels_frame.pack(side="left", fill="y", padx=(5, 2))
    
    ctk.CTkLabel(levels_frame, text="Log Levels:", 
                font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(5, 0))

    def apply_filter():
        """Re-load log file with current filters and save filter settings"""
        load_log_file(reload_all=True)
        save_gui_config()

    # Create level checkboxes in a compact layout
    level_grid_frame = ctk.CTkFrame(levels_frame)
    level_grid_frame.pack(fill="x", padx=5, pady=5)

    for i, level in enumerate(log_filters):
        chk = ctk.CTkCheckBox(
            master=level_grid_frame,
            text=level,
            variable=log_filters[level],
            command=apply_filter,
            font=ctk.CTkFont(size=10)
        )
        # Arrange in 2 columns for compactness
        row = i % 3
        col = i // 3
        chk.grid(row=row, column=col, sticky="w", padx=2, pady=1)

    # Module filters section - FIXED: More responsive layout
    modules_frame = ctk.CTkFrame(filters_main_frame)
    modules_frame.pack(side="left", fill="both", expand=True, padx=(2, 5))
    
    ctk.CTkLabel(modules_frame, text="Modules:", 
                font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(5, 0))

    # FIXED: Scrollable frame for modules that adapts to window size
    module_scroll_frame = ctk.CTkScrollableFrame(modules_frame, height=60)
    module_scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

    # Calculate optimal columns based on number of modules
    modules_per_column = max(3, len(LOG_MODULES) // 4)  # At least 3, but try to fit in 4 columns

    for i, module in enumerate(LOG_MODULES):
        col = i // modules_per_column
        row = i % modules_per_column
        
        chk = ctk.CTkCheckBox(
            master=module_scroll_frame,
            text=module,
            variable=module_filters[module],
            command=apply_filter,
            font=ctk.CTkFont(size=10)
        )
        chk.grid(row=row, column=col, sticky="w", padx=2, pady=1)

    # Configure grid weights for responsiveness
    for i in range((len(LOG_MODULES) // modules_per_column) + 1):
        module_scroll_frame.grid_columnconfigure(i, weight=1)

    # Log display area
    log_text = ctk.CTkTextbox(logs_main_frame, font=ctk.CTkFont(size=11))
    log_text.pack(fill="both", expand=True, padx=5, pady=5)
    log_text.configure(state="disabled")  # Make it read-only

    # For tracking file position between reloads
    last_file_position = 0
    
    def should_display_line(line):
        """Check if the line should be displayed based on filters"""
        # Check log level filters
        if " - DEBUG - " in line and not log_filters["DEBUG"].get():
            return False
        elif " - INFO - " in line and not log_filters["INFO"].get():
            return False
        elif " - WARNING - " in line and not log_filters["WARNING"].get():
            return False
        elif " - ERROR - " in line and not log_filters["ERROR"].get():
            return False
        elif " - CRITICAL - " in line and not log_filters["CRITICAL"].get():
            return False
        
        # Check module filters
        module_found = False
        for module, pattern in LOG_MODULES.items():
            if f" - {pattern} - " in line:
                module_found = True
                if not module_filters[module].get():
                    return False
                break
        else:
            # If no specific module was found, check the "Other" filter
            if not module_filters["Other"].get():
                return False
        
        # Filter out noisy messages
        if filtered_messages_enabled:
            # Skip if message contains any filtered text
            for filtered_msg in FILTERED_MESSAGES:
                if filtered_msg in line:
                    return False
                
            # Skip pre-checked statuses logs
            if re.search(r"Loaded pre-checked statuses: .+", line):
                return False
        
        return True
    
    def load_log_file(reload_all=False):
        """Load log file into display, optionally only loading new content"""
        nonlocal last_file_position
        
        try:
            if not os.path.exists(LOG_FILENAME):
                return
                
            current_size = os.path.getsize(LOG_FILENAME)
            
            # If file was truncated or reload_all requested, start from beginning
            if reload_all or current_size < last_file_position:
                log_text.configure(state="normal")
                log_text.delete("1.0", "end")
                last_file_position = 0
            
            # If there's new content
            if current_size > last_file_position:
                with open(LOG_FILENAME, 'r', encoding='utf-8', errors='replace') as f:
                    # Seek to where we left off
                    f.seek(last_file_position)
                    # Only read new lines
                    new_lines = f.readlines()
                
                # Update tracking position
                last_file_position = current_size
                
                # Process and add only the new lines
                if new_lines:
                    log_text.configure(state="normal")
                    for line in new_lines:
                        # Apply filters to the line
                        if should_display_line(line):
                            log_text.insert("end", line)
                    
                    # Scroll to end to show new content
                    log_text.see("end")
                    log_text.configure(state="disabled")
        except Exception as e:
            error(f"Error loading log file: {e}")

    # Control buttons - FIXED: Responsive button layout
    button_frame = ctk.CTkFrame(logs_main_frame)
    button_frame.pack(fill="x", padx=5, pady=(0, 5))

    def clear_gui_logs():
        """Clear only the log display in the GUI"""
        log_text.configure(state="normal")
        log_text.delete("1.0", "end")
        log_text.configure(state="disabled")
        info("GUI log display cleared")

    def clear_log_file():
        """Clear the content of the log file on disk"""
        try:
            # Close and reopen the log file in write mode to truncate it
            for handler in logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    
            # Truncate the file
            with open(LOG_FILENAME, 'w') as f:
                f.write("")
                
            # Reinitialize the file handler
            for handler in logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    handler.stream = open(handler.baseFilename, handler.mode)
            
            # Refresh the display
            load_log_file(reload_all=True)
        except Exception as e:
            error(f"Error clearing log file: {e}")
            messagebox.showerror("Error", f"Failed to clear log file: {e}")

    # Buttons with responsive layout
    clear_gui_logs_btn = ctk.CTkButton(button_frame, text="Clear GUI", command=clear_gui_logs, width=100)
    clear_gui_logs_btn.pack(side="left", padx=5, pady=5)

    clear_log_file_btn = ctk.CTkButton(button_frame, text="Clear File", command=clear_log_file, width=100)
    clear_log_file_btn.pack(side="left", padx=5, pady=5)

    reload_btn = ctk.CTkButton(button_frame, text="Reload", command=lambda: load_log_file(reload_all=True), width=100)
    reload_btn.pack(side="left", padx=5, pady=5)

    # Auto-reload toggle
    auto_reload_var = ctk.BooleanVar(value=True)  # Default to on
    auto_reload_switch = ctk.CTkSwitch(
        master=button_frame,
        text="Auto-reload",
        variable=auto_reload_var,
        onvalue=True,
        offvalue=False
    )
    auto_reload_switch.pack(side="right", padx=5, pady=5)

    # Create and add the optimized handler with filters
    log_handler = OptimizedLogHandler(log_text, log_filters, module_filters)

    # Add the handler to the ROOT logger to capture logs from all scripts
    root_logger = logging.getLogger()
    root_logger.addHandler(log_handler)

    # Auto-reload function that just clicks the reload button
    def auto_reload_logs():
        """Automatically reload logs when the logs tab is active"""
        if logs_tab_loaded and tabs.get() == "Logs" and auto_reload_var.get():
            load_log_file(reload_all=False)  # Only load new content
        
        # Schedule next reload
        root.after(500, auto_reload_logs)
    
    # Load initial content and start auto-reload
    load_log_file(reload_all=True)
    auto_reload_logs()

    logs_tab_loaded = True

# Setting up the Help tab (lightweight, no lazy loading needed)
help_scroll = ctk.CTkScrollableFrame(master=tab_help)
help_scroll.pack(fill="both", expand=True)

# Add a text widget for help
help_text = ctk.CTkTextbox(help_scroll, height=700, width=920, font=ctk.CTkFont(size=12))
help_text.pack(fill="both", expand=True)

# Load help text
try:
    if os.path.exists(HELP_TEXT_PATH):
        with open(HELP_TEXT_PATH, 'r') as f:
            help_content = f.read()
        help_text.insert("1.0", help_content)
    else:
        help_text.insert("1.0", "Help.txt file not found. Please create this file with usage instructions.")
    
    help_text.configure(state="disabled")  # Make it read-only

except Exception as e:
    error(f"Error loading help text: {e}")
    help_text.insert("1.0", f"Error loading Help.txt: {e}")
    help_text.configure(state="disabled")  # Make it read-only

# Add Discord invite button at bottom of Help tab
discord_button = ctk.CTkButton(help_scroll, text="Join my Discord", command=join_discord)
discord_button.pack(pady=10)

# FIXED: Handle theme restart - load Settings tab if needed
if load_settings_on_startup:
    tabs.set("Settings")
    # Manually trigger the Settings tab loading since set() doesn't trigger the callback
    root.after(10, load_settings_tab)

# Register keyboard shortcuts based on config values
register_keyboard_shortcuts()

# =====================================================================
# OPTIMIZED PROCESS MONITORING AND APPLICATION MANAGEMENT
# =====================================================================

# Optimized process monitoring function
def check_processes():
    """Check if processes are still running and update UI accordingly"""
    global process, exp_process, threads_process, function_process_list, battle_process
    
    # Check Mirror Dungeon process
    if process is not None:
        if process.poll() is not None:
            # Process has ended
            info(f"Mirror Dungeon process ended with code: {process.returncode}")
            process = None
            start_button.configure(text="Start")
    
    # Check Exp process
    if exp_process is not None:
        if exp_process.poll() is not None:
            # Process has ended
            info(f"Exp process ended with code: {exp_process.returncode}")
            exp_process = None
            exp_start_button.configure(text="Start")
    
    # Check Threads process
    if threads_process is not None:
        if threads_process.poll() is not None:
            # Process has ended
            info(f"Threads process ended with code: {threads_process.returncode}")
            threads_process = None
            threads_start_button.configure(text="Start")
    
    # Check Battle process specifically
    if battle_process is not None:
        if battle_process.poll() is not None:
            # Battle process has ended
            info(f"Battle process ended with code: {battle_process.returncode}")
            # Clear the battle process variable
            battle_process = None
    
    # Check all Function Runner processes
    for proc in function_process_list[:]:  # Use a copy of the list for iteration
        if proc.poll() is not None:
            # Process has ended
            info(f"Function Runner process ended with code: {proc.returncode}")
            # Remove from list
            function_process_list.remove(proc)
    
    # Update terminate button state based on whether any function processes are running
    if function_process_list:
        function_terminate_button.configure(state="normal")
    else:
        function_terminate_button.configure(state="disabled")
    
    # Schedule next check
    root.after(1000, check_processes)

# OPTIMIZED: Much faster application exit handling
def on_closing():
    """Handle application exit cleanup - OPTIMIZED VERSION"""
    try:
        info("Application closing")
        
        # OPTIMIZATION: Only kill processes if user wants us to
        if kill_processes_var.get():
            try:
                # Kill processes quickly and don't wait for confirmation
                if process:
                    os.kill(process.pid, signal.SIGTERM)
                if exp_process:
                    os.kill(exp_process.pid, signal.SIGTERM)
                if threads_process:
                    os.kill(threads_process.pid, signal.SIGTERM)
                for proc in function_process_list:
                    if proc and proc.poll() is None:
                        os.kill(proc.pid, signal.SIGTERM)
                info("Killed all processes")
            except Exception as e:
                error(f"Error killing processes: {e}")
        
        # OPTIMIZATION: Clean up threads quickly
        try:
            if 'log_handler' in globals() and log_handler:
                log_handler.close()
        except Exception:
            pass  # Ignore cleanup errors
        
        # OPTIMIZATION: No config saving - settings are saved in real-time
        
    except Exception as e:
        print(f"Error during application close: {e}")
    finally:
        # OPTIMIZATION: Fast exit
        os._exit(0)

# Set the callback for window close
root.protocol("WM_DELETE_WINDOW", on_closing)

# =====================================================================
# OPTIMIZED APPLICATION STARTUP
# =====================================================================

# OPTIMIZED: Minimal startup - most content is lazy-loaded
if __name__ == "__main__":
    def start_application():
        """Initialize the application after GUI is loaded - OPTIMIZED VERSION"""
        try:
            # Load checkbox data at startup (before any automation can run)
            load_checkbox_data()
            
            # OPTIMIZATION: Only start process monitoring, don't load logs yet
            check_processes()
            
            # MOVED: Check for updates if enabled (MUST work without Settings tab loaded)
            if UPDATER_AVAILABLE:
                # Delay the check slightly to ensure UI is fully loaded
                if auto_update_var.get():
                    root.after(1000, lambda: auto_update(
                        "Kryxzort", 
                        "GuiSirSquirrelAssistant", 
                        create_backup=create_backups_var.get(),
                        callback=lambda success, message: (
                            update_status_label.configure(text=f"Update Status: {message}")
                            if 'update_status_label' in globals() else None
                        )
                    ))
                elif update_notifications_var.get():
                    # Only check for updates but don't apply them
                    root.after(1000, lambda: check_for_updates(
                        "Kryxzort", 
                        "GuiSirSquirrelAssistant", 
                        callback=check_updates_callback
                    ))
        except Exception as e:
            error(f"Error in start_application: {e}")
    
    # Make sure "all data" folder exists in the correct location
    os.makedirs(BASE_PATH, exist_ok=True)
    
    # OPTIMIZATION: Shorter delay for faster startup
    root.after(5, start_application)
    
    root.mainloop()