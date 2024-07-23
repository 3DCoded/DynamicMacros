# Variables

Dynamic Macro variables work nearly the same way as standard `gcode_macro` variables. This guide covers the differences.

## SET_DYNAMIC_VARIABLE

Instead of using `SET_GCODE_VARIABLE`, Dynamic Macros use `SET_DYNAMIC_VARIABLE` to update Dynamic Macro variables. Example (assuming `VAR_TEST` is defined from [Utilities](utilities.md)):

```
SET_DYNAMIC_VARIABLE MACRO=var_test VARIABLE=a VALUE=15
```