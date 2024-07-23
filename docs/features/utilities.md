# Utility Functions

Dynamic Macros provides a few utility functions to make Dynamic Macros easier to write.

## update()

The `update()` function allows to save variables across whitespaces (see [Receiving Variables](receivingvariables.md) for more information). Example:

```cfg
[gcode_macro MY_MACRO]
gcode:
    {% set a = 10 %}
    {% set b = update("b", 20) %}
    RESPOND MSG="A: {a}" # 10
    RESPOND MSG="B: {b}" # 20


    RESPOND MSG="A: {a}" # ""
    RESPOND MSG="B: {b}" # 20
```

## get_macro_variables()

The `get_macro_variables()` function allows to retrieve all the variables from another macro in one line of code. Example:

```cfg
[gcode_macro MY_SETTINGS]
variable_a: 10
variable_b: 20
gcode:
    RESPOND MSG="settings"

[gcode_macro GET_SETTINGS]
gcode:
    {% set settings = get_macro_variables("MY_SETTINGS") %}
    RESPOND MSG="Settings: {settings}"
    RESPOND MSG="A: {settings.a}"
```

## update_from_dict()

The `update_from_dict()` function allows for saving the output of `get_macro_variables()` (or other dictionaries) across 