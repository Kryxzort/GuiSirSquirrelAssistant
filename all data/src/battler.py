import sys
import logging
import os

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        folder_path = os.path.dirname(os.path.abspath(__file__))
        if os.path.basename(folder_path) == 'src':
            return os.path.dirname(folder_path)
        return folder_path
BASE_PATH = get_base_path()

# Add src to path for imports
sys.path.append(os.path.join(BASE_PATH, 'src'))

# Import common to set up DirtyLogger
import common

# Logging configuration is handled by common.py
logger = logging.getLogger("battler")

def main():
    """Run the battle function and exit immediately"""
    try:
        try:
            # Import core - shared_vars will be automatically loaded
            import core
            
            
            # Call the battle function
            core.battle()
            
        except AttributeError:
            logger.exception("Function 'battle' not found in module 'core'")
        except Exception as e:
            logger.exception(f"Error running battle function: {e}")
            
    except Exception as e:
        logger.exception(f"Unexpected error in battler.py: {e}")
    finally:
        sys.exit(0)

if __name__ == "__main__":
    main()
