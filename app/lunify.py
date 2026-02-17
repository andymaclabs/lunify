#-------------------------------------------------------------------------------
# File:         lunify.py
# Author:       Andrew "Shabadoo" Abbey
# Description:  Merges lua project into single file.
# Date:         03 Feb 26
# Edit:         17 Feb 26
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
    "-o": "out_path",
    "-e": "entry_point"
  }

  if argv_len < 2:
    return config
  
  if os.path.isdir(argv[1]):
    config["src_path"] = argv[1]
  
  for i in range(argv_len):

    arg = argv[i]
    
    if arg in flags and i < argv_len - 1:
      
      next_arg = argv[i + 1]
      
      if flags[arg] != "entry_point" and not os.path.isdir(next_arg):
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
  file_path = os.path.join(pwd, "lunify.conf")

  # Check config file exists
  if not os.path.isfile(file_path):
    print(f"Info: Config file '{file_path}' not found. Using defaults")
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
    "src_path": os.path.join(".", "src"),
    "out_path": os.path.join(".", "build"),
    "entry_point": "Main",
    "tab_size": 4,
    "strip_blank_lines": 0,
    "strip_comments": 0
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

  print('Gathering files...')

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

        # Regex to check for valid Lua identifiers
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', module_name):
          raise Exception(f"Invalid Filename: '{file}'. Name must be a valid Lua variable (no hyphens/spaces).")

        file_path = os.path.join(root, file)
        paths[module_name] = file_path

        print(f"\t- Adding '{module_name}' at '{file_path}'.")

  if not paths:
    raise Exception(f"Directory '{src_path}' does not contain entry file.")

  return paths

#-------------------------------------------------------------------------------
# Description:  Recursively builds a dependency list (in call order) for
#               the project.
# Params:       module_name - Module name (excluding extension .lua).
#               file_paths - Dictionary of file paths.
#               resolved - List of already processed modules.
#               seen - Set modules in the current recursion stack.
# Return:       list - Dependency list for the project.
#-------------------------------------------------------------------------------
def get_dependency_list(module_name, file_paths, resolved=None, seen=None):
  if resolved is None: resolved = []
  if seen is None: seen = set()

  # Circular dependency check
  if module_name in seen:
    raise Exception(f"Circular dependency detected! Cycle: {' -> '.join(seen)} -> {module_name}")

  # If already built this module, skip it
  if module_name in resolved:
    return resolved
  
  # Track current path
  seen.add(module_name)

  file_path = file_paths.get(module_name)
  if not file_path:
    raise Exception(f"Module '{module_name}' required but not found.")

  try:
    # Read src file
    with open(file_path, "r") as f:
      
      active_lines = [line for line in f if not line.strip().startswith("--")]
      content = "".join(active_lines)
      
      deps = re.findall(r'require\(\"(.*?)\"\)', content)

      for dep in deps:
        get_dependency_list(dep, file_paths, resolved, seen)

  except Exception as e:
        if "Circular dependency" in str(e): raise e
        raise Exception(f"Error processing '{module_name}': {e}")

  # Backtracking: Remove from current stack
  seen.remove(module_name)

  # Add to final list
  resolved.append(module_name)

  print(f"\t- Resolved '{module_name}' (Dependencies: {len(deps)})")

  return resolved

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
  
  banner_lines = get_banner()
  
  w_lines = [
    f"-- {'=' * 97}\n",
    "-- BUILT WITH LUNIFY - BY SHABADOO\n"
    f"-- {'=' * 97}\n",
  ]

  if banner_lines:
    w_lines.extend(banner_lines)
    w_lines.extend([f"-- {'=' * 97}\n"])

  w_lines.extend(["local lunify_module\n"])

  # Get root file and add to module list
  root = app_config["entry_point"]

  if root not in dependency_list:
    dependency_list.append(root)

  module_list = dependency_list

  print("Building...")

  for module_name in module_list:

    # Read module src file
    try:
      file_path = file_paths[module_name]

      print(f"\t- Reading '{module_name}' at '{file_path}'.")

      with open(file_path, "r") as f:
        r_lines = list(f)
    except:
      raise Exception(f"Could not read from '{file_path}'.")

    # Start function wrap

    w_lines.append(f"-- lunify -- {module_name} {'-' * 100}"[:100] + "\n")

    if not module_name == root:
      w_lines.append("lunify_module = function()\n")

    # Write src module
    for line in r_lines:

      # Skip blank lines
      if app_config["strip_blank_lines"] and line.strip() == "":
        continue

      # Skip comment lines
      if app_config["strip_comments"] and line.strip()[:2] == "--":
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
    out_filename = f"{root}.lunify.lua"
    file_path = os.path.join(app_config["out_path"], out_filename)

    print(f"\t- Writing '{file_path}'.")

    with open(file_path, "w") as f:
      f.writelines(w_lines)
  except Exception as e:
    raise Exception(f"Could not write to '{file_path}'. Reason: {e}")
  
  print(f"Lunify complete.")

#-------------------------------------------------------------------------------
# Description:  The entry point of the applicaiton.
# Params:       src_dir - The path to the src directory.
#               build_dir_path - The path to the build directory.
# Return:       None.
#-------------------------------------------------------------------------------
def app(app_config):

  src_path = app_config["src_path"]
  out_path = app_config["out_path"]
  entry_point = app_config["entry_point"]

  print(f"Lunifying '{src_path}' --> '{out_path}'")
  
  try:
    # Get file paths for project files
    file_paths = get_file_paths(src_path)
    
    if entry_point not in file_paths:
      raise Exception(f"Entry point '{entry_point}'.lua not found.")

    root = entry_point

    # Create ordered and flattened dependency list
    print("Determining module import order...")
    dependency_list = get_dependency_list(root, file_paths)

    # Clean build directory
    clean_directory(out_path)
    
    # Build project
    build(dependency_list, file_paths, app_config)

  except Exception as e:
    print(f"Error: {e}")

#-------------------------------------------------------------------------------
# Description:  Gets a custom ascii banner for Lunify output.
# Return:       An ascii banner from banner.txt
#-------------------------------------------------------------------------------
def get_banner():
  banner_path = os.path.join(os.getcwd(), "banner.txt")
  if not os.path.isfile(banner_path):
    return []
  
  try:
    with open(banner_path, "r", encoding="utf-8") as f:
      return [f"-- {line}" for line in f]
  except:
    return []

#-------------------------------------------------------------------------------
if __name__ == "__main__":
  app_config = config(sys.argv)
  app(app_config)
