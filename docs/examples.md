# Example Macros

This page will hold several different Dynamic Macro examples. Note that most of the examples here can be used as normal macros, but were developed using Dynamic Macros.

## M900

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