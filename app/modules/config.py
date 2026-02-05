#-------------------------------------------------------------------------------
# File:         modules.config.py
# Author:       Andrew "Shabadoo" Abbey
# Description:  Merges lua project into single file.
# Date:         05 Feb 2026
# Updated:      N/A
#-------------------------------------------------------------------------------

import json
import os

#-------------------------------------------------------------------------------
# Description:  Validates command line arguments.
# Params:       argv - The sys.argv object (command line arguments).
# Return:       config.
#-------------------------------------------------------------------------------
def parse_and_validate_args(argv):
  argv_len = len(argv)
  config = {}
  flags = {
    "-s": "src_path",
    "-o": "out_path"
  }

  if argv_len < 2:
    print("Info: No arguments found.")
    return
  
  if os.path.isdir(argv[1]):
    config["src_path"] = argv[1]
  
  for i in range(argv_len):

    arg = argv[i]
    
    if arg in flags and i < argv_len - 1:
      
      next_arg = argv[i + 1]
      
      if not os.path.isdir(next_arg):
        print(f"Error: Expected path after '{arg}'.")
        continue
      
      config[flags[arg]] = next_arg

  return config

#-------------------------------------------------------------------------------
# Description:  Validates config file data.
# Return:       config
#-------------------------------------------------------------------------------
def parse_and_validate_config_file():
  file_path = "./lunify.conf"

  # Check config file exists
  if not os.path.isfile(file_path):
    print(f"Config file '{file_path}' not found.")
    return {}
  
  # Read config file into dictionary
  try:
    with open(file_path, "r") as f:
      config = json.load(f)
  except Exception as e:
    print(f"Config Error: {e}")

  return config

#-------------------------------------------------------------------------------
# Description:  Sets config for project.
# Return:       config
#-------------------------------------------------------------------------------
def config(argv):
  default_config = {
    "src_path": "./src",
    "out_path": "./build",
    "tab_size": 4,
    "ignore": []
  }

  configs = [
    parse_and_validate_config_file(),
    parse_and_validate_args(argv)
  ]

  for config in configs:
    for key, value in config.items():
      default_config[key] = value

  return default_config