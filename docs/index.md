# Klipper Dynamic Macros

**Never restart Klipper again for simple macros.**

---

!!! warning
    This is still a work in progress.

Klipper Dynamic Macros is an unofficial way to update macros without restarting Klipper, so you can update macros mid-print and see their results live. 

## How Normal Macros Work

Your macros are written in a `.cfg` file, then included into your `printer.cfg`. When Klipper restarts, it parses these files and saves the macros internally (you can't change them without restarting Klipper). When a macro is called, the cached code is interpreted and run. This method is faster, as the macros don't have to be reread every time.

## How Dynamic Macros Work

Your macros are written in a `.cfg` file, then the relative path to that file is configured in a `[dynamicmacros]` config section. The config files are read and parsed every time you run the macro. This method is slightly slower, as the macros have to be reread every time.

## Variables

Dynamic Macros support all features of normal `gcode_macros`, EXCEPT variables. Here's a simple example of which kind of variables work and won't work with Dynamic Macros.

=== "Works"
    ```cfg
    [gcode_macro test]
    gcode:
        {% set number = params.NUMBER|int %}
        M117 Number: {number}
    ```
=== "Doesn't Work"
    ```cfg
    [gcode_macro test]
    variable_number: 10
    gcode:
        M117 Number: {printer["gcode_macro test"].number}
    ```

Dynamic Macros can still read macro variables from normal `gcode_macros`, but they can't store variables themselves.

## Should a Macro be Dynamic?

Not all macros will benefit from being dynamic. Here's a few questions you can ask about the macro to see if it should be dynamic:

- Is it a macro that is unstable/may break?
- Is it a macro that may need to be edited several times?

If your answer to either of those was yes, then your macro will likely benefit from being dynamic. Follow the [Tutorial](tutorial.md) to get started with Dynamic Macros.

## Examples

See [Example Macros](examples.md) for examples of Dynamic Macros.

## Features

See [Development Status](devstatus.md) for the currently available features, and planned features.