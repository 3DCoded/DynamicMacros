# Example Macros

This page will hold several different Dynamic Macro examples. Note that most of the examples here are specific to Dynamic Macros only.

## M900

!!! info "Normal Macro"

In Marlin, M900 K is used to set pressure/linear advance. Now, you can use it in Klipper too:

```cfg
[gcode_macro M900]
description: Set Pressure Advance
gcode:
  {% set k = params.K|default(0)|float %}
  {% if k < 1 %}
    SET_PRESSURE_ADVANCE ADVANCE={k}
  {% endif %}
```

## Recursion

!!! info "Dynamic Macros Only"

This is an example Dynamic Macro to demonstrate the recursive functionality of Dynamic Macros.

```cfg
[gcode_macro RECURSION_TEST]
gcode:
  {% set num = params.NUM|default(5)|int %}
  {% if num == 0 %}
  RESPOND MSG="End"
  {% else %}
  RESPOND MSG={num}
  RECURSION_TEST NUM={num-1}
  {% endif %}
  
```

## Receiving Position Updates

!!! info "Dynamic Macros Only"

This is an example Dynamic Macro to demonstrate the ability to receive position updates from within the same macro.

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

## Preserving Variables

!!! info "Dynamic Macros Only"

This is an example of how to preserve variables across triple-newlines in Dynamic Macros.

```cfg
[gcode_macro VARIABLES]
gcode:
    {% set num = update("num", 10) %}
    M117 {num}


    M117 {num}
    # Above line outputs 10
```