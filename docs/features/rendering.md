---
comments: true
---

# Dynamic Rendering

DynamicMacros includes a `DYNAMIC_RENDER` command, useful for developing new macros.

## How Macros are Run

All Klipper macros (including standard macros) are "rendered" before being run. For example, the following macro:

```cfg
[gcode_macro test]
gcode:
    M117 {params.A}
```

When the command `test A=2` is run, `2` is displayed on the printer's screen. 

When a macro is run, it is first rendered, then run. For example (click on the tabs):

=== "macros.cfg"
    ```cfg
    M117 {params.A}
    ```
=== "Rendered"
    Assuming the macro is run with `A=2`:
    ```cfg
    M117 2
    ```
=== "Result"
    ```
    2
    ```

## Using the `DYNAMIC_RENDER` command

The `DYNAMIC_RENDER` command is used the same way as the `DYNAMIC_MACRO` command. However, instead of running the macro, it will render the macro, as explained above, then print out the result to the Klipper console. Example:

```
DYNAMIC_RENDER MACRO=test A=2
```

will display

```
Rendered TEST:

M117 2
```