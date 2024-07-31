# Delayed GCode

Dynamic Macros supports a feature similar to `delayed_gcode`.

## Configuration

To configure a DynamicMacro to be run repeatedly/after a delay, update your macro as follows:

=== "Before"
    ```cfg
    [gcode_macro test]
    gcode:
        RESPOND MSG="test"
    ```
=== "After"
    ```cfg
    [gcode_macro test]
    initial_duration: 2 # Wait two seconds after Klipper starts to run this, and two seconds between repeats (if enabled)
    repeat: 1 # 1 means repeat, 0 means don't repeat
    gcode:
        RESPOND MSG="test"
    ```