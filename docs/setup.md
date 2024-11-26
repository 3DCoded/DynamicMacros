---
comments: true
---

# Setup

Follow this guide to setup and confiure Dynamic Macros.

## Install

Run in your terminal:

```sh
cd ~
git clone https://github.com/3DCoded/DynamicMacros
cd DynamicMacros
sh install.sh
sudo service klipper restart
```

Add to your `moonraker.conf`:

```cfg title="moonraker.conf"
# DynamicMacros Update Manager
[update_manager DynamicMacros]
type: git_repo
path: ~/DynamicMacros
origin: https://github.com/3DCoded/DynamicMacros.git
primary_branch: main
is_system_service: False
install_script: install.sh
```

## Updating

First, update via Moonraker's update manager. Then run in your terminal:

```sh
cd ~/DynamicMacros
sh install.sh
sudo service klipper restart
```

## Configuration

To configure Dynamic Macros, put in your `printer.cfg` (or a file included in it):

```cfg title="printer.cfg"
[dynamicmacros]
configs: dynamic.cfg
```

Create a new file in the same folder as your `printer.cfg` called `dynamic.cfg`. In it, configure some macros like you normally would. Example:

```cfg title="dynamic.cfg"
[gcode_macro MYTEST]
gcode:
    M117 Hello world!

[gcode_macro HEAT_HOTEND]
gcode:
    {% set temp = params.TEMP|int %}
    M104 S{temp}
```

Restart Klipper.

!!! info
    Updating the `[dynamicmacros]` config section requires a Klipper restart. The files listed in the `macros:` parameter must be present when Klipper restarts.

## Testing

If you run the command `MYTEST`, the output should be:
```
Hello world!
```

If you runthe command `HEAT_HOTEND TEMP=200`, the hotend should start heating up. 

Next, edit the `MYTEST` macro to output something else, like `Test successful!`

```cfg title="dynamic.cfg"
[gcode_macro MYTEST]
gcode:
    M117 Test successful!
```

Save the file, but **do not** restart Klipper.

Run the `DYNAMIC_MACRO` command to reload the macros.

Run `MYTEST` again, and the output should be:
```
Test successful!
```

## Features

- [Recursion](recursion.md)
- [Receiving Variable Updates](receivingvariables.md)
- [Utility Functions](utilities.md)
- [Variables](variables.md)

## Tutorial

Follow the [Tutorial](tutorial/index.md).

## When to Restart Klipper or Reload Dynamic Macros

Dynamic Macros provides a utility `DYNAMIC_MACRO` command to run macros manually, and to refresh the macros. Usage examples (assuming M900 is defined as a Dynamic Macro):

```gcode
DYNAMIC_MACRO MACRO=M900 K=0.035
```

is the same as:

```
M900 K0.035
```

To refresh Dynamic Macros, just run `DYNAMIC_MACRO` with no parameters.

A Klipper restart is required if:

- You changed the `description`
- You changed the `initial_duration`
- You changed the `repeat`

A `DYNAMIC_MACRO` refresh is required if:

- You created a new macro
- You renamed an existing macro
- You changed the contents of a macro
- You deleted an existing macro