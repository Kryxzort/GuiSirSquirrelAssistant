import os
import sys
import json
import time
import urllib.request
import urllib.error
import zipfile
import shutil
import logging
import subprocess
import platform
import threading
import fnmatch
import configparser  # Add this import for config modification
from datetime import datetime

# Configure logging
logger = logging.getLogger("updater")

# Define exclusions - files/directories that should never be updated
EXCLUDED_PATHS = [
    "backups/",    # Backup directory
    "temp/",      # Temporary files
    "*.log"        # Any log files (including Pro_Peepol's.log)
]

# Config files that need smart merging (user settings preserved + new defaults added)
CONFIG_MERGE_FILES = [
    "config/gui_config.json",
    "config/pack_priority.json",
    "config/delayed_pack_priority.json", 
    "config/pack_exceptions.json",
    "config/delayed_pack_exceptions.json",
    "config/squad_order.json",
    "config/delayed_squad_order.json",
    "config/status_selection.json",
    "config/fusion_exceptions.json",
    "config/grace_selection.json"
]

class Updater:
    
    def __init__(self, repo_owner, repo_name, current_version_file="version.json", 
                 backup_folder="backups", temp_folder="temp", api_url=None):
        """Initialize updater with repository info and file paths"""
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.current_version_file = current_version_file
        self.backup_folder = backup_folder
        self.temp_folder = temp_folder
        self.exclusions = EXCLUDED_PATHS
        
        # Default GitHub API URL if none provided
        if api_url is None:
            self.api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        else:
            self.api_url = api_url
            
        # Determine base path and set up correct directory structure
        if getattr(sys, 'frozen', False):
            # Running as compiled exe
            self.base_path = os.path.dirname(sys.executable)
        else:
            # Running as script
            script_path = os.path.abspath(__file__)
            self.base_path = os.path.dirname(script_path)
        
        # Determine parent directories structure
        if os.path.basename(self.base_path) == "src":
            # We're in src folder inside all data
            # src > all data > parent_dir
            self.all_data_dir = os.path.dirname(self.base_path)
            self.parent_dir = os.path.dirname(self.all_data_dir)
        elif os.path.basename(self.base_path) == "all data":
            # We're directly in all_data
            self.all_data_dir = self.base_path
            self.parent_dir = os.path.dirname(self.all_data_dir)
        else:
            # We're in some other location, assume it's the parent directory
            self.parent_dir = self.base_path
            self.all_data_dir = os.path.join(self.parent_dir, "all data")
        
        # Create full paths
        self.version_file_path = os.path.join(self.parent_dir, current_version_file)
        
        # Put backup folder in parent directory (same level as 'all data')
        self.backup_path = os.path.join(self.parent_dir, backup_folder)
        
        # Temp directory in parent directory (same level as 'all data')
        self.temp_path = os.path.join(self.parent_dir, temp_folder)
        
        # Ensure directories exist
        os.makedirs(self.backup_path, exist_ok=True)
        os.makedirs(self.temp_path, exist_ok=True)
    
    def _retry_file_operation(self, operation, operation_desc, max_retries=5, delay=0.5):
        """
        Retry a file operation with exponential backoff to handle file locks and permission issues
        """
        for attempt in range(max_retries):
            try:
                operation()
                if attempt > 0:
                    logger.info(f"Successfully {operation_desc} on attempt {attempt + 1}")
                return True
            except (OSError, IOError, PermissionError) as e:
                error_type = type(e).__name__
                if attempt == max_retries - 1:
                    logger.exception(f"RETRY FAILED: Unable to {operation_desc} after {max_retries} attempts. Final error: {error_type}: {e}")
                    raise
                else:
                    wait_time = delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"RETRY {attempt + 1}/{max_retries}: {error_type} while trying to {operation_desc}: {e}")
                    logger.info(f"Waiting {wait_time:.1f}s before retry...")
                    time.sleep(wait_time)
        return False
        
    def get_current_version(self):
        try:
            if os.path.exists(self.version_file_path):
                with open(self.version_file_path, 'r') as f:
                    version = f.read().strip()
                    return version if version else 'v0'
            return 'v0'  # Default version if file doesn't exist
        except Exception as e:
            logger.exception(f"Error reading version file: {e}")
            return 'v0'
            
    def get_latest_version(self):
        try:
            # First try to get the latest release
            release_url = f"{self.api_url}/releases/latest"
            
            try:
                with urllib.request.urlopen(release_url) as response:
                    if response.getcode() == 200:
                        release_data = json.loads(response.read().decode())
                        return release_data['tag_name'], release_data['zipball_url']
            except urllib.error.HTTPError as e:
                # If no releases found (404), check the version.json file directly
                if e.code != 404:
                    raise
                    
            # Fall back to checking version.json file in the repository
            version_file_url = f"https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/main/version.json"
            
            try:
                with urllib.request.urlopen(version_file_url) as response:
                    if response.getcode() == 200:
                        repo_version = response.read().decode().strip()
                        if repo_version:
                            # Use the zipball URL for the main branch
                            download_url = f"{self.api_url}/zipball/main"
                            return repo_version, download_url
            except Exception as e:
                logger.warning(f"Could not read version.json from repository: {e}")
                    
            # Final fallback to latest commit on main branch
            commits_url = f"{self.api_url}/commits/main"
            with urllib.request.urlopen(commits_url) as response:
                commit_data = json.loads(response.read().decode())
                commit_hash = commit_data['sha']
                # Generate a version number based on the commit date
                commit_date = commit_data['commit']['committer']['date'].split('T')[0].replace('-', '.')
                download_url = f"{self.api_url}/zipball/{commit_hash}"
                return f"commit-{commit_date}", download_url
                
        except Exception as e:
            logger.exception(f"Error checking for updates: {e}")
            return None, None
    
    def check_for_updates(self):
        current_version = self.get_current_version()
        latest_version, download_url = self.get_latest_version()
        
        if latest_version is None:
            logger.warning("Failed to retrieve latest version information")
            return False, None, None
        
        # Clean up versions for comparison (remove any whitespace)
        current_clean = current_version.strip() if current_version else ""
        latest_clean = latest_version.strip() if latest_version else ""
        
        # Debug logging
            
        # Check if we need to update (simple string comparison)
        if current_clean != latest_clean:
            logger.info(f"Update available: {current_clean} -> {latest_clean}")
            return True, latest_clean, download_url
        else:
            return False, latest_clean, None

    def should_exclude(self, file_path, dest_file_path=None):
        # Convert to Unix-style path for consistent matching
        normalized_path = file_path.replace("\\", "/")
        
        # Config files are now handled by config merging system, no special exclusion needed
            
        # Explicitly exclude backup and temp folders
        if normalized_path.startswith(f"{self.backup_folder}/") or normalized_path == self.backup_folder:
            return True
            
        if normalized_path.startswith(f"{self.temp_folder}/") or normalized_path == self.temp_folder:
            return True
        
        for pattern in self.exclusions:
            # Exact match
            if normalized_path == pattern:
                return True
                
            # Directory match (ends with /)
            if pattern.endswith("/") and normalized_path.startswith(pattern):
                return True
                
            # Wildcard match (using glob patterns)
            if "*" in pattern and fnmatch.fnmatch(normalized_path, pattern):
                return True
        
        return False
    
    def download_update(self, download_url):
        # Clear temp directory if it exists (but don't recreate it)
        try:
            # Just clear contents of temp directory without removing it
            for item in os.listdir(self.temp_path):
                item_path = os.path.join(self.temp_path, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            logger.info(f"Cleared temp directory {self.temp_path}")
        except Exception as e:
            logger.warning(f"Error clearing temp directory: {e}")
        
        try:
            # Ensure temp directory exists
            os.makedirs(self.temp_path, exist_ok=True)
            
            # Download the zip file
            zip_path = os.path.join(self.temp_path, 'update.zip')
            logger.info(f"Downloading update from {download_url}")
            
            with urllib.request.urlopen(download_url) as response, open(zip_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
                
            logger.info(f"Download completed: {zip_path}")
            return zip_path
        except Exception as e:
            logger.exception(f"Error downloading update: {e}")
            return None
    
    def modify_backup_config(self, backup_dir):
        # Possible locations for gui_config.json in the backup
        possible_config_paths = [
            os.path.join(backup_dir, "all data", "config", "gui_config.json"),
            os.path.join(backup_dir, "config", "gui_config.json"),
        ]
        
        # Search for gui_config.json in the backup directory if not found in expected locations
        config_path = None
        for path in possible_config_paths:
            if os.path.exists(path):
                config_path = path
                break
        
        # If not found in expected locations, search the entire backup directory
        if not config_path:
            for root, dirs, files in os.walk(backup_dir):
                if "gui_config.json" in files:
                    config_path = os.path.join(root, "gui_config.json")
                    break
        
        if not config_path or not os.path.exists(config_path):
            logger.warning(f"Could not find gui_config.json in backup directory {backup_dir}")
            return False
        
        try:
            logger.info(f"Modifying backup config at: {config_path}")
            
            # Load the backup's config file (NOT the current one!)
            config_data = {}
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            # Ensure Settings section exists
            if 'Settings' not in config_data:
                config_data['Settings'] = {}
            
            # Get current values for logging
            old_auto_update = config_data['Settings'].get('auto_update', 'Unknown')
            old_notifications = config_data['Settings'].get('update_notifications', 'Unknown')
            
            # Disable auto-update and notifications in the BACKUP ONLY
            config_data['Settings']['auto_update'] = False
            config_data['Settings']['update_notifications'] = False
            
            # Add a note to indicate this is a backup (optional)
            config_data['Settings']['_backup_version'] = True
            
            # Write the modified config back to the BACKUP location only
            with open(config_path, 'w') as configfile:
                json.dump(config_data, configfile, indent=2)
            
            logger.info(f"   - auto_update: {old_auto_update} -> False")
            logger.info(f"   - update_notifications: {old_notifications} -> False")
            logger.info(f"   - Location: {config_path}")
            logger.info("   - Original config remains unchanged!")
            
            return True
            
        except Exception as e:
            logger.exception(f"[ERROR] Error modifying backup config: {e}")
            logger.info("Backup creation will continue, but update loop prevention failed")
            return False
    
    def backup_current_version(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        backup_dir = os.path.join(self.backup_path, backup_name)
        
        logger.info(f"Creating backup at {backup_dir}")
        
        try:
            # Make sure backup directory exists
            try:
                # Create parent directory first, then the specific backup directory
                os.makedirs(self.backup_path, exist_ok=True)
                os.makedirs(backup_dir, exist_ok=True)
            except Exception as e:
                logger.exception(f"Failed to create backup directory at {backup_dir}: {e}")
                return None
            
            # We want to back up the parent directory that contains 'all data'
            source_dir = self.parent_dir
            logger.info(f"Backing up contents from {source_dir}")
            
            # Count files for logging
            file_count = 0
            dir_count = 0
            
            # Copy all files and directories from parent_dir to backup_dir
            # excluding the backup, _temp, and extracted folders
            for item in os.listdir(source_dir):
                item_path = os.path.join(source_dir, item)
                backup_item_path = os.path.join(backup_dir, item)
                
                # Skip backup, _temp, and extracted folders
                if item == self.backup_folder or item == self.temp_folder or item == "extracted":
                    logger.info(f"Skipping {item} folder from backup")
                    continue
                
                try:
                    if os.path.isdir(item_path):
                        # For directories, use copytree with ignore function
                        def ignore_func(src, names):
                            return [n for n in names if 
                                    n == self.backup_folder or 
                                    n == self.temp_folder or 
                                    n == "extracted" or
                                    n.endswith('.log')]
                                
                        shutil.copytree(item_path, backup_item_path, 
                                      ignore=ignore_func)
                        dir_count += 1
                        logger.info(f"Backed up directory: {item}")
                    else:
                        # Skip log files
                        if item.endswith('.log'):
                            logger.info(f"Skipping log file: {item}")
                            continue
                            
                        shutil.copy2(item_path, backup_item_path)
                        file_count += 1
                        logger.info(f"Backed up file: {item}")
                except Exception as e:
                    logger.exception(f"Failed to backup {item}: {e}")
                    # Continue with other files instead of failing completely
            
            logger.info(f"Backup completed successfully: {file_count} files and {dir_count} directories")
            
            # IMPORTANT: Now modify the backup's config to prevent update loops
            # This ONLY affects the backup, NOT the current config!
            logger.info("Modifying backup config to prevent update loops...")
            self.modify_backup_config(backup_dir)
            
            return backup_dir
        except Exception as e:
            logger.exception(f"Error creating backup: {e}")
            return None
    
    def apply_update(self, zip_path):
        # Check if this is a staged self-update
        if self._is_staged_update():
            return self._perform_staged_update()
            
        if not zip_path or not os.path.exists(zip_path):
            logger.error("Invalid zip file path")
            return False
            
        try:
            # Extract the zip file directly to _temp directory
            # We'll use the _temp directory directly instead of creating a new "extracted" folder
            logger.info(f"Extracting update to {self.temp_path}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.temp_path)
                
            # GitHub zip files contain a top-level folder with the repo name and commit hash
            # We need to get the name of this folder
            subdirs = [d for d in os.listdir(self.temp_path) if os.path.isdir(os.path.join(self.temp_path, d)) and d != "extracted"]
            if not subdirs:
                logger.error("No repository directories found in extracted zip")
                return False
                
            repo_dir = os.path.join(self.temp_path, subdirs[0])
            logger.info(f"Found repository directory: {repo_dir}")
            
            # Special case: if we're updating the updater itself, stage the update
            updater_path = os.path.join(repo_dir, "all data", "src", "updater.py")
            if os.path.exists(updater_path):
                logger.info("Updater.py update detected - staging self-update")
                return self._stage_self_update(repo_dir)
            
            # Handle config merging BEFORE copying files
            temp_config_backup = self.handle_config_merging(repo_dir)
            
            # Now copy files to the PARENT directory, NOT just all_data
            # This is the key change - we're updating the parent directory structure
            self._copy_directory_with_exclusions(repo_dir, self.parent_dir)
            
            # Handle deleted files in the parent directory
            self._handle_deleted_files(repo_dir)
            
            # Merge user settings back into newly installed configs
            if temp_config_backup:
                self.merge_configs_from_temp(temp_config_backup)
            
            logger.info("Update applied successfully")
            return True
        except Exception as e:
            logger.exception(f"Error applying update: {e}")
            return False
    
    def _copy_directory_with_exclusions(self, src_dir, dest_dir):
        # Create the destination directory if it doesn't exist
        os.makedirs(dest_dir, exist_ok=True)
        
        file_count = 0
        dir_count = 0
        
        # Walk through the source directory
        for root, dirs, files in os.walk(src_dir):
            # Calculate the relative path from the source directory
            rel_path = os.path.relpath(root, src_dir)
            
            # Skip excluded directories
            if rel_path != "." and self.should_exclude(rel_path.replace("\\", "/")):
                logger.info(f"Skipping excluded directory: {rel_path}")
                
                # Remove from dirs to prevent descending into it
                for excluded_dir in list(dirs):
                    if self.should_exclude(os.path.join(rel_path, excluded_dir).replace("\\", "/")):
                        dirs.remove(excluded_dir)
                continue
                
            # Process files
            for file in files:
                # Get the path relative to the repository root
                if rel_path == ".":
                    file_rel_path = file
                else:
                    file_rel_path = os.path.join(rel_path, file).replace("\\", "/")
                
                # Copy the file
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_dir, rel_path, file)
                
                # Skip if this file should be excluded
                if self.should_exclude(file_rel_path, dest_file):
                    logger.info(f"Skipping excluded file: {file_rel_path}")
                    continue
                
                # Create parent directories if needed
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                
                try:
                    # Skip self - don't update our own script if running from the directory being updated
                    if os.path.samefile(src_file, __file__) if os.path.exists(dest_file) else False:
                        logger.info(f"Skipping update to self: {file_rel_path}")
                        continue
                        
                    # Remove existing file if any with retry logic
                    if os.path.exists(dest_file):
                        self._retry_file_operation(lambda: os.remove(dest_file), f"remove {dest_file}")
                    
                    # Copy the file with retry logic
                    self._retry_file_operation(lambda: shutil.copy2(src_file, dest_file), f"copy {src_file} to {dest_file}")
                    file_count += 1
                    logger.debug(f"Updated file: {file_rel_path}")
                except Exception as e:
                    logger.exception(f"Failed to update file {file_rel_path}: {e}")
        
        logger.info(f"Update copied {file_count} files")
    
    def _handle_deleted_files(self, extracted_repo_dir):
        # Get list of all files in the extracted repository (excluding excluded paths)
        repo_files = set()
        for root, dirs, files in os.walk(extracted_repo_dir):
            # Skip excluded directories to prevent descending into them
            dirs_to_remove = []
            for d in dirs:
                rel_path = os.path.relpath(os.path.join(root, d), extracted_repo_dir).replace("\\", "/")
                if self.should_exclude(rel_path):
                    dirs_to_remove.append(d)
            
            # Remove excluded directories from the dirs list
            for d in dirs_to_remove:
                dirs.remove(d)
                
            for file in files:
                # Get path relative to repo root
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, extracted_repo_dir)
                
                # Normalize path
                normalized_path = rel_path.replace("\\", "/")
                
                # Skip excluded paths
                if not self.should_exclude(normalized_path):
                    repo_files.add(normalized_path)
        
        # Get list of all files in the parent directory
        app_files = set()
        for root, dirs, files in os.walk(self.parent_dir):
            # Skip excluded directories
            rel_root = os.path.relpath(root, self.parent_dir).replace("\\", "/")
            if self.should_exclude(rel_root):
                # Skip this directory
                dirs[:] = []  # Clear dirs list to prevent descending
                continue
                
            for file in files:
                # Get path relative to app root
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.parent_dir)
                
                # Normalize path
                normalized_path = rel_path.replace("\\", "/")
                
                # Skip excluded paths
                if not self.should_exclude(normalized_path):
                    app_files.add(normalized_path)
        
        # Find files that exist in app but not in repo
        deleted_files = app_files - repo_files
        
        # Remove these files (but never touch excluded paths)
        deleted_count = 0
        for file_path in deleted_files:
            # Check exclusions one more time for safety
            if self.should_exclude(file_path):
                logger.info(f"Protected excluded file from deletion: {file_path}")
                continue
                
            full_path = os.path.join(self.parent_dir, file_path)
            try:
                # Skip self - don't delete our own script
                if os.path.samefile(full_path, __file__) if os.path.exists(full_path) else False:
                    logger.info(f"Skipping deletion of self: {file_path}")
                    continue
                    
                os.remove(full_path)
                deleted_count += 1
                logger.info(f"Removed deleted file: {file_path}")
            except Exception as e:
                logger.exception(f"Failed to remove deleted file {file_path}: {e}")
        
        logger.info(f"Removed {deleted_count} deleted files")
        
        # Also remove empty directories (but never excluded ones)
        for root, dirs, files in os.walk(self.parent_dir, topdown=False):
            # Skip excluded directories completely
            rel_path = os.path.relpath(root, self.parent_dir).replace("\\", "/")
            if self.should_exclude(rel_path):
                continue
                
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                rel_dir_path = os.path.relpath(dir_path, self.parent_dir).replace("\\", "/")
                
                # Skip excluded directories
                if self.should_exclude(rel_dir_path):
                    continue
                    
                # Try to remove if empty
                try:
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)  # This only removes if directory is empty
                        logger.info(f"Removed empty directory: {rel_dir_path}")
                except OSError as e:
                    # Directory not empty or other error
                    logger.debug(f"Could not remove directory {rel_dir_path}: {e}")
    
    def handle_config_merging(self, repo_dir):
        """
        Handle smart config merging:
        1. Backup user configs to temp
        2. Allow new configs to be installed 
        3. Merge user settings back into new configs
        4. Auto-cleanup temp configs
        """
        logger.info("Starting config merging process")
        
        # Create temp config backup directory
        temp_config_backup = os.path.join(self.temp_path, "config_backup")
        os.makedirs(temp_config_backup, exist_ok=True)
        
        try:
            # Step 1: Backup existing user configs to temp
            config_dir = os.path.join(self.all_data_dir, "config")
            if os.path.exists(config_dir):
                for config_file in CONFIG_MERGE_FILES:
                    config_filename = os.path.basename(config_file)
                    user_config_path = os.path.join(config_dir, config_filename)
                    backup_config_path = os.path.join(temp_config_backup, config_filename)
                    
                    if os.path.exists(user_config_path):
                        shutil.copy2(user_config_path, backup_config_path)
                        logger.info(f"Backed up user config: {config_filename}")
            
            # Step 2: Allow new configs to be installed (handled by normal copy process)
            logger.info("User configs backed up to temp, allowing new configs to install")
            
            # Return temp backup path for later merging
            return temp_config_backup
            
        except Exception as e:
            logger.exception(f"Error during config backup: {e}")
            return None
    
    def merge_configs_from_temp(self, temp_config_backup):
        """
        Merge user settings from temp backup into newly installed configs
        """
        logger.info("Merging user settings into new configs")
        
        try:
            config_dir = os.path.join(self.all_data_dir, "config")
            
            for config_file in CONFIG_MERGE_FILES:
                config_filename = os.path.basename(config_file)
                user_backup_path = os.path.join(temp_config_backup, config_filename)
                current_config_path = os.path.join(config_dir, config_filename)
                
                if os.path.exists(user_backup_path) and os.path.exists(current_config_path):
                    self._merge_single_config(user_backup_path, current_config_path)
                    logger.info(f"Merged config: {config_filename}")
                elif os.path.exists(user_backup_path):
                    # New config doesn't exist, keep user config
                    shutil.copy2(user_backup_path, current_config_path)
                    logger.info(f"Restored user config (no new version): {config_filename}")
            
            # Step 3: Auto-cleanup temp configs
            shutil.rmtree(temp_config_backup, ignore_errors=True)
            logger.info("Config merging completed, temp files cleaned up")
            
        except Exception as e:
            logger.exception(f"Error during config merging: {e}")
    
    def _merge_single_config(self, user_config_path, new_config_path):
        """
        Merge a single config file: user values take priority, new keys get added
        """
        try:
            # Load user config (backup)
            with open(user_config_path, 'r') as f:
                user_config = json.load(f)
        except:
            logger.warning(f"Failed to load user config: {user_config_path}")
            return
        
        try:
            # Load new default config
            with open(new_config_path, 'r') as f:
                new_config = json.load(f)
        except:
            logger.warning(f"Failed to load new config: {new_config_path}")
            # Keep user config if new config is invalid
            shutil.copy2(user_config_path, new_config_path)
            return
        
        # Deep merge: user values override defaults, new keys from defaults are added
        merged_config = self._deep_merge_configs(new_config, user_config)
        
        # Save merged config
        with open(new_config_path, 'w') as f:
            json.dump(merged_config, f, indent=2)
        
        logger.debug(f"Successfully merged: {os.path.basename(new_config_path)}")
    
    def _deep_merge_configs(self, default_config, user_config):
        """
        Deep merge configs - user values override defaults, new keys from default are added
        """
        if isinstance(default_config, dict) and isinstance(user_config, dict):
            result = default_config.copy()
            for key, value in user_config.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    # Recursively merge nested dictionaries
                    result[key] = self._deep_merge_configs(result[key], value)
                else:
                    # User value takes precedence
                    result[key] = value
            return result
        else:
            # Non-dict values: user takes precedence
            return user_config if user_config is not None else default_config

    def update_version_file(self, version):
        try:
            with open(self.version_file_path, 'w') as f:
                f.write(version)
                
            logger.info(f"Version file updated to {version}")
            return True
        except Exception as e:
            logger.exception(f"Error updating version file: {e}")
            return False
    
    def clean_temp_files(self):
        if os.path.exists(self.temp_path):
            try:
                # Instead of removing the directory, just clean its contents
                for item in os.listdir(self.temp_path):
                    item_path = os.path.join(self.temp_path, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                logger.info("Temporary files cleaned up")
            except Exception as e:
                logger.exception(f"Error cleaning up temporary files: {e}")
    
    def restart_application(self):
        try:
            logger.info("Restarting application")
            
            # Create temp directory if it doesn't exist
            os.makedirs(self.temp_path, exist_ok=True)
            
            # Get the command to restart
            if getattr(sys, 'frozen', False):
                # If running as exe, use the executable path
                if platform.system() == "Windows":
                    cmd = [os.path.join(self.all_data_dir, "gui_launcher.exe")]
                else:
                    cmd = [os.path.join(self.all_data_dir, "gui_launcher")]
            else:
                # If running as script, use the Python interpreter
                gui_launcher_path = os.path.join(self.all_data_dir, "gui_launcher.py")
                cmd = [sys.executable, gui_launcher_path]
            
            # Create a restart helper script
            restart_script_path = os.path.join(self.temp_path, "restart.py")
            
            with open(restart_script_path, "w") as f:
                f.write(f"""
import os
import sys
import time
import subprocess

# Wait a moment to ensure files are fully written
time.sleep(1)

# Launch the application
cmd = {repr(cmd)}
print(f"Launching application with command: {{cmd}}")

try:
    subprocess.Popen(cmd)
    print("Application launched successfully")
except Exception as e:
    print(f"Error launching application: {{e}}")
""")
            
            # Launch the restart script
            if platform.system() == "Windows":
                # Use CREATE_NEW_PROCESS_GROUP to detach on Windows
                subprocess.Popen([sys.executable, restart_script_path], 
                              creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                # Use subprocess.DEVNULL to detach on Unix
                subprocess.Popen([sys.executable, restart_script_path], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL, 
                             stdin=subprocess.DEVNULL,
                             start_new_session=True)
            
            # Exit the current process
            logger.info("New process started, exiting current process")
            sys.exit(0)
            
        except Exception as e:
            logger.exception(f"Error restarting application: {e}")
            return False
    
    def cleanup_old_backups(self, keep_count=3):
        """Remove old backup folders, keeping only the most recent ones"""
        try:
            if not os.path.exists(self.backup_path):
                return
            
            # Get all backup directories
            backup_dirs = []
            for item in os.listdir(self.backup_path):
                item_path = os.path.join(self.backup_path, item)
                if os.path.isdir(item_path) and item.startswith("backup_"):
                    backup_dirs.append(item_path)
            
            # Sort by modification time (newest first)
            backup_dirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            # Remove old backups beyond keep_count
            for old_backup in backup_dirs[keep_count:]:
                try:
                    shutil.rmtree(old_backup)
                    logger.info(f"Removed old backup: {os.path.basename(old_backup)}")
                except Exception as e:
                    logger.exception(f"Failed to remove old backup {old_backup}: {e}")
            
            if len(backup_dirs) > keep_count:
                logger.info(f"Cleaned up {len(backup_dirs) - keep_count} old backups, kept {keep_count} most recent")
                
        except Exception as e:
            logger.exception(f"Error cleaning up old backups: {e}")
    
    def perform_update(self, create_backup=True, auto_restart=True, preserve_only_last_3=True):
        # SAFETY: Always create backup regardless of parameter (for safety)
        # If create_backup is True, we'll keep the backup
        # If create_backup is False, we'll delete it after successful update
        backup_path = self.backup_current_version()
        if not backup_path:
            return False, "Failed to create safety backup"
            
        # Check for updates
        update_available, latest_version, download_url = self.check_for_updates()
        
        if not update_available or download_url is None:
            logger.info("No updates available or failed to get update information")
            # Clean up backup if not requested
            if not create_backup and backup_path and os.path.exists(backup_path):
                try:
                    shutil.rmtree(backup_path)
                    logger.info("Cleaned up unnecessary backup")
                except:
                    pass
            return False, "No updates available"
        
        # Download the update
        zip_path = self.download_update(download_url)
        if not zip_path:
            return False, "Failed to download update"
        
        # Apply the update
        if not self.apply_update(zip_path):
            return False, "Failed to apply update"
        
        # Update the version file
        self.update_version_file(latest_version)
        
        # Clean up backup if not requested (but we made one for safety)
        if not create_backup and backup_path and os.path.exists(backup_path):
            try:
                shutil.rmtree(backup_path)
                logger.info("Cleaned up unwanted backup after successful update")
            except:
                pass
        
        # Preserve only last 3 backups if requested
        if create_backup and preserve_only_last_3:
            self.cleanup_old_backups(keep_count=3)
                
        # Clean up
        self.clean_temp_files()
        
        # Restart if requested
        if auto_restart:
            self.restart_application()
        
        return True, f"Successfully updated to {latest_version}"
    
    def check_and_update_async(self, callback=None, create_backup=True, auto_restart=True, preserve_only_last_3=True):
        def update_thread():
            result, message = self.perform_update(create_backup, auto_restart, preserve_only_last_3)
            if callback:
                callback(result, message)
        
        thread = threading.Thread(target=update_thread)
        thread.daemon = True
        thread.start()
        return thread

    def _is_staged_update(self):
        """Check if this updater instance is running as a staged self-update"""
        return len(sys.argv) > 1 and sys.argv[1] == "--staged-update"

    def _stage_self_update(self, repo_dir):
        """Stage a self-update by extracting new updater to temp and calling it"""
        try:
            # Create temp directory for staged updater
            temp_updater_dir = os.path.join(self.temp_path, "staged_updater")
            os.makedirs(temp_updater_dir, exist_ok=True)
            
            # Copy new updater to temp
            new_updater_path = os.path.join(repo_dir, "all data", "src", "updater.py")
            staged_updater_path = os.path.join(temp_updater_dir, "updater.py")
            shutil.copy2(new_updater_path, staged_updater_path)
            
            # Copy other necessary files (like logger if needed)
            logger_src = os.path.join(repo_dir, "all data", "src", "logger.py")
            if os.path.exists(logger_src):
                shutil.copy2(logger_src, os.path.join(temp_updater_dir, "logger.py"))
            
            logger.info(f"Staged updater prepared at {staged_updater_path}")
            
            # Call staged updater with special flag and paths
            cmd = [
                sys.executable, staged_updater_path,
                "--staged-update",
                repo_dir,  # Source path with new files
                self.parent_dir,  # Target installation directory
                self.temp_path  # Temp directory for cleanup
            ]
            
            logger.info("Launching staged self-update...")
            logger.info(f"Command: {' '.join(cmd)}")
            
            # Launch staged updater and exit current process
            subprocess.Popen(cmd, cwd=temp_updater_dir)
            logger.info("Staged updater launched. Current process will exit.")
            
            # Exit current process to allow staged updater to update us
            sys.exit(0)
            
        except Exception as e:
            logger.exception(f"Error staging self-update: {e}")
            return False

    def _perform_staged_update(self):
        """Perform the actual staged update when running as staged updater"""
        try:
            if len(sys.argv) < 4:
                logger.error("Staged update missing required arguments")
                return False
                
            repo_dir = sys.argv[2]
            target_dir = sys.argv[3]
            temp_cleanup_dir = sys.argv[4] if len(sys.argv) > 4 else None
            
            logger.info("=== PERFORMING STAGED SELF-UPDATE ===")
            logger.info(f"Source: {repo_dir}")
            logger.info(f"Target: {target_dir}")
            
            # Brief delay to ensure original process has fully exited
            time.sleep(0.5)
            
            # Initialize updater with target directory as parent
            self.parent_dir = target_dir
            self.all_data_dir = os.path.join(target_dir, "all data")
            
            # Handle config merging BEFORE copying files
            temp_config_backup = self.handle_config_merging(repo_dir)
            
            # Copy all files from repo to target
            self._copy_directory_with_exclusions(repo_dir, target_dir)
            
            # Handle deleted files
            self._handle_deleted_files(repo_dir)
            
            # Merge user settings back into newly installed configs
            if temp_config_backup:
                self.merge_configs_from_temp(temp_config_backup)
            
            # Clean up temp directories with retry logic
            if temp_cleanup_dir and os.path.exists(temp_cleanup_dir):
                try:
                    self._retry_file_operation(lambda: shutil.rmtree(temp_cleanup_dir), f"remove temp directory {temp_cleanup_dir}")
                    logger.info(f"Cleaned up temp directory: {temp_cleanup_dir}")
                except Exception as e:
                    logger.exception(f"Could not clean up temp directory: {e}")
            
            logger.info("Staged self-update completed successfully!")
            return True
            
        except Exception as e:
            logger.exception(f"Error performing staged update: {e}")
            return False

# Helper function to run the updater
def check_for_updates(repo_owner, repo_name, callback=None):
    try:
        updater = Updater(repo_owner, repo_name)
        update_available, version, download_url = updater.check_for_updates()
        
        if update_available:
            message = f"Update available: {version}"
            logger.info(message)
            
            if callback:
                callback(True, message, True)
            return True
        else:
            message = "You have the latest version"
            if callback:
                callback(True, message, False)
            return False
    except Exception as e:
        logger.exception(f"Error checking for updates: {e}")
        if callback:
            callback(False, f"Error: {e}", False)
        return False

def auto_update(repo_owner, repo_name, create_backup=True, preserve_only_last_3=True, callback=None):
    try:
        updater = Updater(repo_owner, repo_name)
        return updater.check_and_update_async(callback, create_backup, preserve_only_last_3=preserve_only_last_3)
    except Exception as e:
        logger.exception(f"Error starting auto-update: {e}")
        if callback:
            callback(False, f"Error: {e}")
        return None

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%d/%m/%Y %H:%M:%S'
    )
    
    # Example usage
    check_for_updates("Kryxzort", "GuiSirSquirrelAssistant")