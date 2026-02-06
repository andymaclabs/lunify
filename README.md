# Lunify

A script builder for DCS World, or any other Lua project that doesn't handle modules.

## How it works

Lunify takes a modular Lua project that uses 'require' to link modules, and generates a single script file which can be run in Lua environments that do not support the Lua require functionality.

Lunify analyses require statements, develops a module dependency tree, wraps modules in a return function to protect local scope, and builds a single file with modules in the correct call order.

### Example

#### Original code

##### module_a.lua

```
local M = {}

local message = "Hello from A!"

function M.speak(text)
  print(text)
end

return M
```

##### main.lua

```
local module_a = require("module_a")

module_a.speak(module_a.message)
```

#### Lunified code

##### main.lunify.lua

```
local lunify_module
lunify_module = function()
  local M = {}
  local message = "Hello from A!"
  function M.speak(text)
    print(text)
  end
  return M
end
local module_a = lunify_module()

module_a.speak(module_a.message)
```

## Installation

Download lunify.py... Nothing to install, other than Python of course!

## Usage

Usage is simple:

- Create lunify.conf file (optional), and
- Run lunify.py in the same directory as lunify.conf.

A couple of things to note:

- Project should have a single main Lua file in the source directory. All other Lua code should be in a sub-directory (e.g ./src/modules). You can call this file whatever you like, but there must only be one lua file.
- Only files that are linked to the entry point file through require statements will be added to the build file. Lunify builds a dependency tree recursively from the main file.
- This app has not been tested extensively, so please provide constructive feedback.

## Config

Lunify will use config settings in the following order of precedence:

1. Command Line (if provided)
2. Config file (lunify.conf)
3. Default config

### Default config

By defualt lunify will set:

- src_path: ./src
- out_path: ./build
- tab_size: 4

```
my_project/
|-- build/
|   +-- main.lunify.lua
+-- src/
|   |-- modules/
|   |   |-- module_a/
|   |   |   +-- module_a.lua
|   |   +-- module_b/
|   |       +-- module_b.lua
|   +-- main.lua
+-- README.md
```

### Custom config

The src_path and out_path can be specified using command line arguments or through the lunify.conf file.

#### Command line

First arugment is custom source path by defualt:

```
python lunify.py ./custom/source/src_path
```

```
my_project/
|-- build/
|   +-- main.lunify.lua
+-- custom/
|   +-- source/
|       +-- src_path/
|           |-- modules/
|           |   |-- module_a/
|           |   |   +-- module_a.lua
|           |   +-- module_b/
|           |       +-- module_b.lua
|           +-- main.lua
+-- README.md
```

Flags can be used as well (order does not matter):

```
python lunify.py -s ./custom_src_path -o ./custom/out_path
```

```
my_project/
|-- custom/
|   +-- out_path/
|       +-- main.lunify.lua
+-- custom_src_path/
|   |-- modules/
|   |   |-- module_a/
|   |   |   +-- module_a.lua
|   |   +-- module_b/
|   |       +-- module_b.lua
|   +-- main.lua
+-- README.md
```

#### Config file (lunify.conf)

A config file (lunify.conf) can be added to the project directory.

```
{
  "src_path": "./src",
  "out_path": "./build",
  "tab_size": 2
}
```

```
my_project/
|-- build/
|   +-- main.lunify.lua
+-- src/
|   |-- modules/
|   |   |-- module_a/
|   |   |   +-- module_a.lua
|   |   +-- module_b/
|   |       +-- module_b.lua
|   +-- main.lua
|-- lunify.conf
+-- README.md
```

## Contributing

Contributions are welcome!

1. Fork the project
2. Create your Feature Branch (`git checkout -b feature/amazing_feature`)
3. Commit your changes (`git commit -m "Add some amazing feature"`)
4. Push your change (`git push origin feature/amazing_feature`)
5. Open a Pull Request

## Licence

```
Distributed under the MIT License.
```
