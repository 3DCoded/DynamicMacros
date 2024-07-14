# Tutorial

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

## Configuration

To configure Dynamic Macros, put in your `printer.cfg` (or a file included in it):

```cfg title="printer.cfg"
[dynamicmacros]
macros: dynamic.cfg
```

Create a new file in the same folder as your `printer.cfg` called `dynamic.cfg`. In it, configure some macros like you normally would. Example:

```cfg title="dynamic.cfg"
[gcode_macro MYTEST]
gcode:
    M117 Test Successful!

[gcode_macro HEAT_HOTEND]
gcode:
    {% set temp = params.TEMP|int %}
    M104 S{temp}
```