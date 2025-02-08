import os
import json
import shutil
import logging


def init():
    pass


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# load config file
if not os.path.exists("config.json"):
    # copy example config
    shutil.copy("config.example.json", "config.json")
    logging.warning("Config file not found, copied example config")

with open("config.json", "r") as f:
    config = json.load(f)
    logging.info("Config loaded")

with open("implantData.json", "r", encoding="utf8") as f:
    implantData = json.load(f)
    logging.info("Implant Data loaded")
