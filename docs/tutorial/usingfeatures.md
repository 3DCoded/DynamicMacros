---
comments: true
---

# Using Dynamic Macros Features

Now that your macros are dynamic, you can use the powerful feature set of Dynamic Macros.

## [Recursion](recursion.md)

Recursion allows a macro to call itself, something standard GCode macros can't do. 

When using recursion, it's important to make sure your macro has an "end case". This is a case when the macro won't call itself again. Otherwise the macro will be stuck in an infinite loop and freeze Klipper.

Here are a few examples of recursion:

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

## [Receiving Variable Updates](receivingvariables.md)

Receiving variable updates allows Dynamic Macros to update variables without rerunning the macro. 

An example of this is getting the printer's position. A standard GCode macro will evaluate all the variables, then run the GCode. However, using three newlines (two blank lines) between code segments in Dynamic Macros will allow each segment to be evaluated at runtime, allowing for variable updates.

## [Utility Functions](utilities.md)

See the link above (the subtitle) for more information on utility functions.

## [Python](python.md)

Dynamic Macro's most powerful feature allows you to run Python code from within a macro. See the link above (the subtitle) for more information.

## [delayed_gcode](delayed.md)

Dynamic Macros supports a feature similar to `delayed_gcode`. See the link above (the subtitle) for more information.