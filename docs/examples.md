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

!!! success "Dynamic Macro"

These are a few example Dynamic Macros to demonstrate the recursive functionality of Dynamic Macros.

```cfg title="Counting to 10"
[gcode_macro COUNT]
gcode:
    {% set num = params.NUM|default(1)|int %}
    {% if num <= 10 %}
        RESPOND MSG={num}
        COUNT NUM={num+1} # Count up 1
    {% else %}
        RESPOND MSG="Done Counting"
    {% endif %}
```

```cfg title="Load to Filament Sensor"
[gcode_macro LOAD_TO_FSENSOR]
gcode:
    {% set val = printer["filament_sensor fsensor"].filament_detected %}
    {% if val == 0 %}
        M83
        G1 E50 F900 # Move filament 50mm forwards
        RESPOND MSG="Waiting for fsensor"
        LOAD_TO_FSENSOR # Recursion
    {% else %}
        G1 E65 F900 # Move filament to nozzle
        RESPOND MSG="Filament Loaded"
    {% endif %}
```

## Receiving Position Updates

!!! success "Dynamic Macro"

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

!!! success "Dynamic Macro"

This is an example of how to preserve variables across triple-newlines in Dynamic Macros.

```cfg
[gcode_macro VARIABLES]
gcode:
    {% set num = update("num", 10) %}
    M117 {num}


    M117 {num}
    # Above line outputs 10
```