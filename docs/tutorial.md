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

Run `MYTEST` again, and the output should be:
```
Test successful!
```