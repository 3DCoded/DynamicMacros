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

## Recursion

Unlike normal `gcode_macro`s, Dynamic Macros supports recursion (allowing a macro to call itself). For more examples, see [Examples](examples.md#recursion)

## Receiving Variable Updates

Unlike normal `gcode_macro`s, Dynamic Macros supports receiving variable updates within the same macro. For example, the following macro will show the same output in both `M117`s:

```cfg
[gcode_macro STATIC_MOVE]
gcode:
  G28
  M117 Before: {printer.toolhead.position.z}
  # Above displays position before macro run
  G90
  G1 Z20
  M117 After: {printer.toolhead.position.z}
  # Above displays same position
```

However, this macro will show different outputs based on the current Z position of the toolhead:

```cfg
[gcode_macro DYNAMIC_MOVE]
gcode:
  G28

  
  M117 Before: {printer.toolhead.position.z}
  # Above displays position after G28
  G90
  G1 Z20


  M117 After: {printer.toolhead.position.z}
  # Above displays position after G1
```

Notice the large whitespaces. Three newline characters (two blank lines) between code segments denotes a variable update. However, some variables won't be preserevd across the whitespace.

```cfg
[gcode_macro VARIABLES]
gcode:
    {% set num = 10 %}
    M117 {num}


    M117 {num}
    # Above line outputs nothing
```

You can use the `update()` function to preserve certain variables across the whitespaces:

```cfg
[gcode_macro VARIABLES]
gcode:
    {% set num = update("num", 10) %}
    M117 {num}


    M117 {num}
    # Above line outputs 10
```

See [Examples](examples.md#receiving-position-updates) for examples.

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

- You changed the description

A `DYNAMIC_MACRO` refresh is required if:

- You created a new macro
- You renamed an existing macro
- You changed the contents of a macro
- You deleted an existing macro