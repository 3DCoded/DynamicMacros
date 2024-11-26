---
comments: true
---

# Receiving Variable Updates

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

## Custom Delimeters

To split a macro by something other than three empty lines, you can set the `delimeter` parameter in your `[dynamicmacros]` config section:

```cfg
[dynamicmacros]
configs: dynamic.cfg,macros.cfg
delimeter: SPLIT_HERE
```

To disable receiving variable updates entirely, you can set `delimeter` to `NO_DELIMETER`.