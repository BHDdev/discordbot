import os
import json
import shutil

# load config file
if not os.path.exists("config.json"):
    # copy example config
    shutil.copy("config.example.json", "config.json")

with open("config.json", "r") as f:
    config = json.load(f)