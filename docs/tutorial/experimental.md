# Experimental Features

!!! warning
    The features on this page are experimental, and untested or only lightly tested. Proceed at your own risk.

## Running Python from within a Macro

!!! info "Disclaimer"
    This functionality allows Dynamic Macros to gain significant control over your printer and Klipper host. I am not responsible for whatever happens if you download a malicious macro.

There are three main reasons why this could be helpful:

1. Allowing for deeper control of Klipper and the Klipper host
2. A learning bridge for creating Klipper plugins/extras
3. A tool to help develop Klipper plugins/extras without restarting Klipper

First, get on the `dev` branch:

```sh
cd ~/DynamicMacros
git checkout dev
git pull origin
sh install.sh
sudo service klipper restart
```

To run Python from within a Dynamic Macro, use either the `python()` utility function, or the `python_file()` utility function. The `python()` function accepts python code as a multiline string, and the `python_file()` function accepts a filename (relative to your `printer.cfg` folder).

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