import argparse
import logging
import os
import threading
import requests
import keyboard  # Import the keyboard module
from src import mirror
from src.core import md_setup
from src.common import error_screenshot, match_image

connection_event = threading.Event()
    
def update():
    r = requests.get("https://api.github.com/repos/Samsterr/SirSquirrelAssistant/releases/latest")
    tag = "1.0.5.1.3"
    r_tag = r.json()["tag_name"]
    if r_tag != tag:
        print("A New Version is Available! Downloading it to your current folder")
        r = requests.get("https://github.com/Samsterr/SirSquirrelAssistant/releases/download/" + r_tag + "/sirsquirrel.7z")
        with open("sirsquirrel.7z", "wb") as f:
            f.write(r.content)
        print("Download Completed. Please look for the 7z and update as per usual before continuing")

def exit_program():
    print("\nHotkey pressed. Exiting the program...")
    os._exit(0)

# Start a background thread to listen for 'Ctrl+Q'
def exit_listener():
    keyboard.add_hotkey('ctrl+q', exit_program)  # Register hotkey Ctrl+Q to exit
    # Keep the listener active without blocking the main thread
    while True:
        keyboard.wait('ctrl+q')  # Block until Ctrl+Q is pressed

def connection_listener():
    while True:
        if match_image("pictures/general/connection.png"):
            connection_event.clear()
        connection_event.set()

def mirror_dungeon(run_count, logger):
    with open("config/status_selection.txt", "r") as f:
        status = [i.strip().lower() for i in f.readlines()]
    try:
        num_runs = 0
        status_list = (status * ((run_count // len(status)) + 1))[:run_count]
        logger.info("Starting")
        for i in range(run_count):
            logger.info("Run {}".format(num_runs + 1))
            logger.info("Current Team: "+status_list[i])
            run_complete = False
            md_setup()
            MD = mirror.Mirror(status_list[i])
            MD.setup()
            while(not run_complete):
                if connection_event.is_set():
                    run_complete = MD.mirror_loop()    
            num_runs += 1   
    except Exception as e:
        error_screenshot()
        logger.exception(e)

def main():
    logging.basicConfig(
        level=logging.DEBUG,  # Set the logging level (e.g., DEBUG, INFO, WARNING)
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
        handlers=[
            logging.FileHandler("squirrel.log"),  # Output to a file
        ]
    )
    logger = logging.getLogger(__name__)
    parser = argparse.ArgumentParser()
    parser.add_argument("RunCount", help="How many times you want to run Mirror Dungeons", type=int)
    args = parser.parse_args()
    update()
    connection_event.set()
    exit_listener_thread = threading.Thread(target=exit_listener, daemon=True)
    exit_listener_thread.start()

    connection_thread = threading.Thread(target=connection_listener, daemon=True)
    connection_thread.start()

    mirror_dungeon(args.RunCount, logger)

if __name__ == "__main__":
    main()
