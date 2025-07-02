---
comments: true
---

# Python

Dynamic Macros's most powerful feature allows you to run Python code directly from within a macro.

## Running Python from within a Macro

!!! note "Disclaimer"
    This functionality allows Dynamic Macros to gain significant control over your printer and Klipper host. I am not responsible for whatever happens if you download a malicious macro.

There are three main reasons why this could be helpful:

1. Allowing for deeper control of Klipper and the Klipper host
2. A learning bridge for creating Klipper plugins/extras
3. A tool to help develop Klipper plugins/extras without restarting Klipper

To run Python from within a Dynamic Macro, use either the `python()` utility function, or the `python_file()` utility function. The `python()` function accepts python code as a multiline string, and the `python_file()` function accepts a filename (relative to your `printer.cfg` folder).

!!! tip
    When using the `python()` utility function, Jinja2 (which converts the macro to GCode) may throw errors during parsing. If you are getting errors, it is recommended to switch to `python_file()`.

Here are a few examples:

### Python Math

```cfg title="macros.cfg"
[gcode_macro MATH]
gcode:
    {% set value = python("""
    a = kwargs['a']
    b = kwargs['b']
    c = a + b
    output(c)
    """, a=1, b=2) %}
    RESPOND MSG={value}
```

### Python File Running GCode

```cfg title="macros.cfg"
[gcode_macro PYFILE]
gcode:
    {% set value = python_file("test.py") %}
    RESPOND MSG={value}
```

```py title="test.py"
print("Hello from Python!")
gcode("G28\nG1 X100 Y100 Z100 F1200")
output("GCode Executed")
```

!!! info "Where does the Python file go?"
    Python files run by `python_file()` should be placed in the same folder as your `printer.cfg`

### No Return Variables

To run Python without a return variable, you can use `{% set _ = python... %}`

Example:

```cfg title="macros.cfg"
[gcode_macro NO_RETURN]
gcode:
    {% set _ = python("gcode('RESPOND MSG=\'hello!\'')) %}
```