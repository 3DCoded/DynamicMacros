---
comments: true
---

# Converting to Dynamic Macros

Follow this tutorial to convert your standard `gcode_macro` to a Dynamic Macro. 

## printer.cfg

First, remove the `include` line in your `printer.cfg` referencing the file your macros are in. For example, if your macros are in `macros.cfg`, remove the line:

```cfg
[include macros.cfg]
```

from your `printer.cfg`.

## Dynamic Macros Configuration

Next, if you don't already have one, create a `[dynamicmacros]` config section in your `printer.cfg` and add your macro configuration to it:

```cfg title="printer.cfg"
[dynamicmacros]
configs: macros.cfg # You can add more files to this list, separated by commas.
```

??? tip "Interface Workaround (old Fluidd, KlipperScreen, Macro parameters)"
    If your Fluidd/Mainsail macros list is empty, your macro parameters don't show up in your favorite UI, or your dynamic macros don't appear in KlipperScreen's macros list, you can add the following parameter to your `[dynamicmacros]` config section:

    ```cfg
    interface_workaround: true
    ```

??? tip "KlipperScreen"
    If you convert your `LOAD_FILAMENT` and `UNLOAD_FILAMENT` macros to be dynamic, KlipperScreen may not recognize them and report an error. To fix this, add blank macros to your `printer.cfg`, before your `[dynamicmacros]` section. Example:
    ```cfg title="printer.cfg"
    [gcode_macro LOAD_FILAMENT]
    gcode:
        M117 LOAD
    [gcode_macro UNLOAD_FILAMENT]
    gcode:
        M117 UNLOAD
    ```
??? failure "Unknown config object 'gcode_macro'"
    If you are getting a "Unknown config object 'gcode_macro'" error after converting your macros to Dynamic Macros, move your `[dynamicmacros]` section to be after your `[virtual_sdcard]` section.

??? tip "Macro Names"
    Klipper has certain macro names reserved for core functionality. If you are experiencing errors, don't name your Dynamic Macros any of the following:
    
    - `PAUSE`
    - `RESUME`
    - `CANCEL_PRINT`

    If you want to make those macros dynamic, first define them as a **standard** GCode macro:

    ```cfg
    [gcode_macro PAUSE]
    gcode:
        DYNAMIC_PAUSE
    ```

Restart Klipper.

That's it. Your macros are now Dynamic Macros.