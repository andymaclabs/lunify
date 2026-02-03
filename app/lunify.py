#-------------------------------------------------------------------------------
# File:        lunify.py
# Author:      Andrew "Shabadoo" Abbey
# Description: Merges lua project into single file.
# Date:        03 Feb 2026
#-------------------------------------------------------------------------------

import os
import re
import shutil

#-------------------------------------------------------------------------------
# Function:    get_file_paths
# Description: Walks the src directory and finds paths for all lua files.
# Params:      entry_path - Path to the src directory
# Return:      file_paths - Dictionary of lua files and paths
#-------------------------------------------------------------------------------
def get_file_paths(entry_path):
  file_paths = {}
  for root, dirs, files in os.walk(entry_path):
    for file in files:
      if file[-4:] == ".lua":
        file_paths[file[:-4]] = os.path.join(root, file)
  return file_paths

#-------------------------------------------------------------------------------
# Function:    get_module_tree
# Description: Recursively builds a dependency tree for the project.
# Params:      mod_name - Module name (excluding extension .lua)
#              file_paths - Dictionary of file paths
# Return:      mod_tree - Dependency tree for the project
#-------------------------------------------------------------------------------
def get_module_tree(mod_name, file_paths):
  mod_tree = {mod_name: []}

  file_path = file_paths[mod_name]

  try:
    with open(file_path, "r") as f:
      for line in f:
        match = re.search(r'require\(\"(.*?)\"\)', line)
        if match:
          dep_name = match.group(1)
          mod_tree[mod_name].append(get_module_tree(dep_name, file_paths))
  except:
    print(f"Error: The file '{file_path}' was not found!")

  return mod_tree
#-------------------------------------------------------------------------------
# Function:    copy_to_tmp
# Description: Copies a module to tmp directory.
# Params:      file_path
#              tmp_file_path
#-------------------------------------------------------------------------------
def copy_to_tmp(file_path, tmp_file_path):
  if not os.path.isfile(tmp_file_path):

    print(f"  - Copying: {file_path} -> {tmp_file_path}")

    # Read src file into memory
    with open(file_path, "r") as f:
      print(f"    - Reading: {file_path}...", end="")
      lines = list(f)
    print("Done.")

    # Write modified file to tmp directory
    with open(tmp_file_path, "w") as f:
      print(f"    - Writing: {tmp_file_path}...", end="")
      f.write("-- lunify.end\n")
      f.writelines(lines)
    print("Done.")

  else:
    print(f"File exists: '{tmp_file_path}'")

#-------------------------------------------------------------------------------
# Function:    wrap_module_lines
# Description: Wraps a module in a function
# Params:      lines - Array of lines read from module
#-------------------------------------------------------------------------------
def get_module_as_function(mod_name):
  tmp = "./test/build/tmp"
  tmp_mod_file_path = f"{tmp}\\{mod_name}.lua"

  print(f"      - Wrapping: {tmp_mod_file_path}")

  with open(tmp_mod_file_path, "r") as f:
    mod_lines = list(f)

  new_lines = []

  wrap = True

  for line in mod_lines:
    if "lunify.start" in line:
      wrap = False
      continue

    if "lunify.end" in line:
      new_lines.append("local module = function()\n")
      wrap = True
      continue

    if wrap:
      new_lines.append("\t" + line)
    else:
      new_lines.append(line)

  new_lines.append(f"end\nlocal {mod_name} = module()\n-- lunify.end\n")

  return new_lines

#-------------------------------------------------------------------------------
# Function:    merge_module
# Description: 
# Params:      file_name
#              file_path
# Return:      module_tree
#-------------------------------------------------------------------------------
def merge_modules(mod_name, dep_tree, file_paths):
  src_mod_file_path = file_paths[mod_name]
  dest = "./test/build/tmp"
  tmp_mod_file_path = f"{dest}/{mod_name}.lua"

  # Create tmp directory
  if not os.path.isdir(dest):
    try:
      os.mkdir(dest)
    except:
      print(f"Error: The directory '{dest}' already exists!")

  print(f"Merging: {mod_name} dependent modules...")

  # Iterate over module dependencies
  for dep_name in dep_tree:
    print(f"  - Merging: {dep_name} -> {mod_name}")
    # Check if module dependency is already in tmp directory
    tmp_dep_file_path = f"{dest}\\{dep_name}.lua"
    if not os.path.isfile(tmp_dep_file_path):
      # Copy to tmp directory
      copy_to_tmp(file_paths[dep_name], tmp_dep_file_path)
    else:
      print(f"  - File exists: '{tmp_dep_file_path}'")

  # Read through module file
  # Write each line of module file to tmp/module
  # On find require statement -> swap require for fucntion returning dependent module
  # Write rest of module file.

    if os.path.isfile(tmp_mod_file_path):
      src_mod_file_path = tmp_mod_file_path

    # Read mod_file into list
    with open(src_mod_file_path, "r") as f:
      print(f"  - Reading: {src_mod_file_path}")
      src_mod_lines = list(f)
    
    # Iterate through list and write into mod file.
    with open(tmp_mod_file_path, "w") as f:
      print(f"  - Writing: {tmp_mod_file_path}")
      for line in src_mod_lines:
        
        if "lunify.end" in line:
          continue

        # Check if line is a require statement for the dependency
        if f"require(\"{dep_name}\")" in line:
          
          print(f"    - Call wrapping: {tmp_dep_file_path}")
          
          dep_mod_lines = get_module_as_function(dep_name)

          print(f"    - Wrapped: {tmp_dep_file_path}")

          print(f"    - Writing wrapped: {tmp_dep_file_path}")
          f.writelines(dep_mod_lines)
        else:
          f.write(line)
    print(f"  - Writing Complete: {tmp_dep_file_path}")

  # try:
  #   with open(file_path, "r") as f:
  #     for line in f:
  #       if line.strip() == "-- lunify_start":
  #         print("Place holder")
  # except:
  #   print(f"Error: The file '{file_path}' was not found!")

#-------------------------------------------------------------------------------
# Function:    merge_project
# Description: 
# Params:      mod_tree - Dependency tree for the project
# Return:      None
#-------------------------------------------------------------------------------
def merge_project(mod_tree, file_paths):
  for mod_name, dep_array in mod_tree.items():
    
    # If no dependencies
    if len(dep_array) == 0:
      return
    
    # If dependencies, merge dependencies
    for dep_tree in dep_array:
      merge_project(dep_tree, file_paths)
      # merge modules
      merge_modules(mod_name, dep_tree, file_paths)

  return


#-------------------------------------------------------------------------------
# Function:    app
# Description: The entry point of the applicaiton.
# Params:      path - The path to the src directory
# Return:      None
#-------------------------------------------------------------------------------
def app(path):
  file_paths = get_file_paths(path)
  print(file_paths)

  mod_tree = get_module_tree("main", file_paths)
  print(mod_tree)

  merge_project(mod_tree, file_paths)

#-------------------------------------------------------------------------------
if __name__ == "__main__":
 
 build_dir = "./test/build"

 if os.path.isdir(build_dir + "/tmp"):
   try:
     shutil.rmtree(build_dir + "/tmp")
   except OSError as e:
     print(e)

 app('./test')
