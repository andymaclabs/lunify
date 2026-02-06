#-------------------------------------------------------------------------------
# File:         lunify.py
# Author:       Andrew "Shabadoo" Abbey
# Description:  Merges lua project into single file.
# Date:         03 Feb 2026
# Updated:      06 Feb 2026
#-------------------------------------------------------------------------------

import json
import os
import re
import shutil
import sys

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
    return config
  
  if os.path.isdir(argv[1]):
    config["src_path"] = argv[1]
  
  for i in range(argv_len):

    arg = argv[i]
    
    if arg in flags and i < argv_len - 1:
      
      next_arg = argv[i + 1]
      
      if not os.path.isdir(next_arg):
        print(f"Error: Valid path expected after '{arg}'.")
        continue
      
      config[flags[arg]] = next_arg

  return config

#-------------------------------------------------------------------------------
# Description:  Validates config file data.
# Return:       config
#-------------------------------------------------------------------------------
def parse_and_validate_config_file():

  pwd = os.getcwd()
  file_path = f"{pwd}\\lunify.conf"

  # Check config file exists
  if not os.path.isfile(file_path):
    print(f"Info: Config file '{file_path}' not found.")
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
    "src_path": ".\\src",
    "out_path": ".\\build",
    "tab_size": 4
  }

  configs = [
    parse_and_validate_config_file(),
    parse_and_validate_args(argv)
  ]

  for config in configs:
    for key, value in config.items():
      default_config[key] = value

  return default_config

#-------------------------------------------------------------------------------
# Description:  Walks the src directory and finds paths for all lua files.
# Params:       src_dir - Path to the src directory.
# Return:       paths - Dictionary of lua files and paths.
#-------------------------------------------------------------------------------
def get_file_paths(src_path):
  paths = {}

  if not os.path.isdir(src_path):
    raise Exception(f"Directory '{src_path}' not found.")

  # Walk directory structure
  for root, _, files in os.walk(src_path):
  # Iterate files
    for file in files:
      # Get file extension
      file_ext = file[-4:]
      # Add to path dictionary if lua file
      if file_ext == ".lua":
        module_name = file[:-4]
        paths[module_name] = os.path.join(root, file)

  if not paths:
      raise Exception(f"Directory '{src_path}' does not contain entry file.")

  return paths

#-------------------------------------------------------------------------------
# Description:  Recursively builds a dependency list (in call order) for
#               the project.
# Params:       module_name - Module name (excluding extension .lua).
#               file_paths - Dictionary of file paths.
# Return:       list - Dependency list for the project.
#-------------------------------------------------------------------------------
def get_dependency_list(module_name, file_paths, list = []):

  file_path = file_paths[module_name]

  try:
    # Read src file
    with open(file_path, "r") as f:
      for line in f:
        # Search for dependency statements
        match = re.search(r'require\(\"(.*?)\"\)', line)
        if match:
          dependency = match.group(1)
          # Recursively search for dependencies
          get_dependency_list(dependency, file_paths)
          # Add to dependency list if not already added
          if not dependency in list:
            list.append(dependency)
  except:
    raise Exception("Read file operation could not be completed.")

  return list

#-------------------------------------------------------------------------------
# Description:  Deletes a directory.
# Params:       dir_path - The path to the directory.
# Return:       None.
#-------------------------------------------------------------------------------
def delete_directory(dir_path):
  
  # Check if directory exists
  if not os.path.isdir(dir_path):
    raise Exception(f"Directory '{dir_path}' does not exist.")
      
    # Delete directory
  try:
    shutil.rmtree(dir_path)
  except Exception:
    raise Exception(f"Directory '{dir_path}' could not be deleted.")

#-------------------------------------------------------------------------------
# Description:  Creates a directory.
# Params:       dir_path - The path to the directory to be created.
# Return:       None.
#-------------------------------------------------------------------------------
def create_directory(dir_path):

  # Check if directory exists
  if os.path.isdir(dir_path):
    print(f"Directory '{dir_path}' already exists.")
    return

  try:
    # Create directory
    os.mkdir(dir_path)
  except:
    raise Exception(f"Director '{dir_path}' could not be created.")

#-------------------------------------------------------------------------------
# Description:  Cleans (delete and recreate) a directory
# Params:       dir_path - The path to the directory.
# Return:       None.
#-------------------------------------------------------------------------------
def clean_directory(dir_path):
  delete_directory(dir_path)
  create_directory(dir_path)

#-------------------------------------------------------------------------------
# Description:  Builds the ouput file and writes to build directory.
# Params:       dependency_list - List of project dependencies (in call order).
#               file_paths - Dictionarey of project file paths.
#               build_dir_path - Path to the build directory.
# Return:       None.
#-------------------------------------------------------------------------------
def build(dependency_list, file_paths, app_config):
  w_lines = ["local lunify_module\n"]

  # Get root file and add to module list
  root = list(file_paths)[0]
  dependency_list.append(root)
  module_list = dependency_list

  for module_name in module_list:

    # Read module src file
    try:
      file_path = file_paths[module_name]

      with open(file_path, "r") as f:
        r_lines = list(f)
    except:
      raise Exception(f"Could not read from '{file_path}'.")

    # Start function wrap

    w_lines.append(f"-- lunify -- {module_name} {"-" * 100}"[:80] + "\n")

    if not module_name == root:
      w_lines.append("lunify_module = function()\n")

    # Write src module
    for line in r_lines:

      # Skip blank lines
      if line.strip() == "":
        continue
      
      # Skip require statements
      if re.search(r'require\(\"(.*?)\"\)', line):
        continue
      
      # Write line (indented)
      indent = " " * app_config["tab_size"]
      w_lines.append(("" if module_name == root else indent) + line)

    # End function wrap
    if not module_name == root:
      w_lines.append(f"end\nlocal {module_name} = lunify_module()\n")
  
  # Write file
  try:
    file_path = f"./{app_config["out_path"]}/{root}.lunify.lua"
    with open(file_path, "w") as f:
      f.writelines(w_lines)
  except:
    raise Exception(f"Could not write to '{file_path}'.")

#-------------------------------------------------------------------------------
# Description:  The entry point of the applicaiton.
# Params:       src_dir - The path to the src directory.
#               build_dir_path - The path to the build directory.
# Return:       None.
#-------------------------------------------------------------------------------
def app(app_config):

  src_path = app_config["src_path"]
  out_path = app_config["out_path"]
  
  try:
    # Get file paths for project files
    file_paths = get_file_paths(src_path)
    
    root = list(file_paths)[0]

    # Create ordered and flattened dependency list
    dependency_list = get_dependency_list(root, file_paths)

    # Clean build directory
    clean_directory(out_path)
    
    # Build project
    build(dependency_list, file_paths, app_config)

  except Exception as e:
    print(f"Error: {e}")

#-------------------------------------------------------------------------------
if __name__ == "__main__":
  app_config = config(sys.argv)
  app(app_config)
