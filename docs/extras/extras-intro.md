---
comments: true
---

# Introduction to Writing Klippy Extras

This page contains many things that are useful to know before writing Klippy extras.

## The `config` object

Every Klippy extra is a class. Everything in a Klippy extra starts when the class is initialized, passing a `config` object into the class. This `config` object allows access to many parts of Klipper discussed next.

## The `printer` object

This is probably the most useful object you can use in a Klippy extra. This code block below shows how to get it:

```py
printer = config.get_printer()
```

It's that simple!

The printer object lets you access all sorts of useful parts of Klippy, which will be explained later in this page.

## The `gcode` object

The next object you will want to get familiar with is the `gcode` object. This code block below shows how to get it:

```py
gcode = printer.lookup_object('gcode')
```

This `gcode` object is useful for many things. Here are a few of its functions:

- `run_script_from_command` Runs any GCode provided as a string
- `respond_info` Displays text to the Klipper terminal; essentially the same as running `RESPOND MSG=` in a macro
- `register_command` Allows for defining custom GCode commands
- `register_mux_command` A different way to definine custom GCode commands. This is explained later in the examples.

For example, if you wanted to run a `G28` command (home all axes), you would run:

```py
gcode.run_script_from_command('G28')
```

## Configuration options

The `config` object also allows reading of the configuration options present in the `printer.cfg` file. Here's an example config:

```cfg
[myextra]
integer: 5
float: 2.5
string: hello
list: 3d,printing
```

This configuration shows four main option types:

- `int`
- `float`
- `str`
- `list`

To read them, you can use the corresponding functions of `config`:

- `getint`
- `getfloat`
- `get`
- `getlist`

Here's how to use them in code:

```py
number = config.getint('integer')
decimal_number = config.getfloat('float')
text = config.get('string')
my_list = config.getlist('list')
```

!!! tip
    To make a configuration option optional, pass another parameter to the `get` function as a default value. Example:

    ```py
    number = config.getint('integer', 0)
    ```

## Where do Klippy Extras go?

Before we go much further into this tutorial, it's good to know how Klippy reads the extras files. First, there's one last missing part of our Python file:

```py
def load_config(config):
    return MyExtra(config)
```

This is explained later in the examples.

For Klippy to read your extras file, you need to put it in `~/klipper/klippy/extras`. The filename, in this case `myextra.py`, becomes the config name, in this case `[myextra]`. After putting your file in the `extras` folder, you can put a corresponding section into your `printer.cfg` and restart Klipper. Your extra is installed!

However, every time you want to change something, you have to copy your file to the extras folder and restart Klipper. This is a very slow way to develop extras, as each Klipper restart turns off your heaters, loses your home position, and wastes too much time. 

Fortunately, DynamicMacros provides a better solution.

## DynamicMacros

Follow the installation instructions [here](setup.md).

DynamicMacros supports running Python code from a macro. This makes testing parts of Klippy extras much quicker. Here's the current example, as a Klippy extra, excluding the config reading:

```py
class MyExtra:
    def __init__(self, config):
        printer = config.get_printer()
        gcode = printer.lookup_object('gcode')

def load_config(config):
    return MyExtra(config)
```

Here it is as a DynamicMacro (use the tabs to navigate between the two files):

=== "macros.cfg"
    ```cfg
    [gcode_macro myextra]
    gcode:
        {% _  = python_file("myextra.py") %}
    ```
=== "myextra.py"
    ```py
    printer_gcode = printer.lookup_object('gcode')
    ```

Now, you can change anything without restarting Klipper! Whenever you change the macro/Python code, simply run the `DYNAMIC_MACRO` command to internally refresh DynamicMacros.

!!! note
    This setup is intended for development, and not release, as this approach has a few limitations:

    - This approach can't read configuration sections
    - This approach isn't as structured as a full Klippy extra

    For these reasons, this approach is only intended for testing parts of a Klippy extra, and isn't a replacement of extras.

This tutorial won't go in depth about testing extras with DynamicMacros. Instead, this tutorial focuses on writing traditional Klippy extras.

## The `reactor` object

Another useful object from the `config` object is the `reactor`. The code block below shows how to get it:

```py
self.reactor = printer.get_reactor()
```

The reactor opens up a new possibility of Klippy extras: scheduling code to run/repeat at any time. This ability is explained in more detail in the third example.

## Other Extras

This is one more good-to-know about Klippy extras before continuing to the examples:

You can access other extras from an extra. This allows for extended capabilities of extras. For example, this project, DynamicMacros invokes the `gcode_macro` extra to run macros internally. The code blocks below shows two ways to access any other extra:

=== "Method 1"
    ```py
    gcode_macro = printer.lookup_object('gcode_macro')
    ```
=== "Method 2"
    ```py
    from . import gcode_macro
    ```

## Examples

I hope this introduction was helpful. The next part of this tutorial consists of three examples. The first one is linked below:

[Example 1: Greeter :fontawesome-solid-angle-right:](extras-ex1.md){ .md-button }