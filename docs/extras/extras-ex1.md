# Example 1: Greeter (Structure)

!!! info
    This page is under construction.

Before you start to write a Klippy extra, it is important to understand the structure of a Klippy extra. 

---

In Python, a Klippy extra is defined as a class, then referenced in a function at the end of the file. Example:

```py title="greeter.py"
--8<-- "greeter.py:clsheader"
...

--8<-- "greeter.py:loadcfg"
```

There are two functions that can be used at the end of a file:

- `load_config_prefix`, allows for configurations like `[greeter mygreeter]`
- `load_config`, like in this example, allows for configurations like `[greeter]`

## Initializer

In the last line of the above code block, you can see that a `config` object is passed as a parameter to the `Greeter` object. The initializer of the `Greeter` class is shown below in sections:

```py title="Get printer objects and configuration options"
--8<-- "greeter.py:initheader"
--8<-- "greeter.py:readcfg"
```

This section gets the `printer` object with `#!py config.get_printer()`.

It then gets the `gcode` object with `#!py self.printer.lookup_object('gcode')`.

Then, it gets the `reactor` object with `#!py self.printer.get_reactor()`.

After that, it reads the configuration to get the `message` parameter, specifying `#!py 'Welcome to Klipper!'` as the default, using `#!py config.get('message', 'Welcome to Klipper!')`.

The next part of the initializer:

```py title="Register GCode command and event handler"
--8<-- "greeter.py:regcmd"
```

The `self.gcode` object is used here to register the `GREET` command: 

`#!py self.gcode.register_command(
            'GREET', self.cmd_GREET, desc=self.cmd_GRRET_help)`

The `self.printer` object is then used to register an event handler to run when Klippy starts:

`#!py self.printer.register_event_handler(
            'klippy:ready', self._ready_handler)`

??? info "Event handlers"
    Klipper supports the following event handlers for extras to use:

    - `#!py "klippy:ready"`
    - `#!py "klippy:firmware_restart"`
    - `#!py "klippy:disconnect"`

The combined initializer is:
```py title="greeter.py"
--8<-- "greeter.py:init"
```

## Functions

The next part of this Klippy extra is the class functions. This class has three functions aside from the initializer, two of which were mentioned in the `__init__` function:

- `cmd_GREET`
- `_ready_handler`

This example will start with the `_ready_handler` function:

```py title="_ready_handler"
--8<-- "greeter.py:handler"
```

This event handler sets a timer for one second after Klippy starts to run `_greet()`. `#!py self.reactor.monotonic()` represents the current time, and `#!py + 1` adds one second. `#!py self.reactor.register_timer` registers `_greet()` to run when `waketime` occurs.

```py title="_greet()"
--8<-- "greeter.py:agreet"
```

This function uses the `#!py self.gcode` object declared in the initializer. Here, the `respond_info` command is used (similar to running `RESPOND MSG=""`) to display `#!py self.message`.

??? info "What is `eventtime`?"
    You may have noticed that `eventtime` is passed to the `_greet()` function. This is because when Klippy runs `_greet()` from the previous `register_timer`, it passes `eventtime` as a parameter. This is useful if you want a function to repeat itself after a specified interval. In this case, we only want it to run once, so `eventtime` is unused.

??? info "The `#!py self.gcode` object"
    The `#!py self.gcode` object has a few useful functions:

    - `register_command` (used in the initializer)
    - `register_mux_command` (explained later)
    - `respond_info` (used here)
    - `run_script_from_command` (runs the provided string as GCode. The provided string can be multiple lines long)

Finally, the `cmd_GREET` function:

```py title="cmd_GREET"
--8<-- "greeter.py:greet"
```

Here, you can see the `cmd_GREET_help` is set to a string. Next, the `cmd_GREET` function takes in a `gcmd` parameter (unused). Finally, the `cmd_GREET` function calls `_greet()`.

??? info "The `gcmd` parameter"
    The `gcmd` parameter allows functions to receive parameters. For example, if `GREET REPEAT=3` was called, the `REPEAT` parameter could be read as follows:

    ```py
    repeat = gcmd.get_int('REPEAT', 1)
    ```
    
    There are a few `get_` functions that can be used with the `gcmd` parameter:

    - `get` returns a `#!py str`
    - `getint` returns an `#!py int`
    - `getfloat` returns a `#!py float`

    `gcmd` also has a `respond_info` function, similar to the `#!py self.gcode.respond_info` function.

    ---

    The `repeat` variable can then be used:

    ```py
    for _ in range(repeat):
        self._greet()
    ```

## Install

To install a Klippy extra, it has to be placed in the `~/klipper/klippy/extras/` folder. Here's a simple command to install `greeter.py`:

```sh
cp greeter.py ~/klipper/klippy/extras/greeter.py
```

You can also create an install script that uses the `ln` command to create a link to the file, rather than a copy:

```sh title="install.sh"
ln -f greeter.py ~/klippy/klippy/extras/greeter.py
```

## Other Things

A few things that are good to know before moving on:

- If your Klippy extra uses `load_config_prefix`, instead of `load_config`, you can get the name of the configuration section (e.g. `[greeter first]` is named `first`) by using: 
    ```py
    config.get_name().split()[1]
    ```
- If you want to learn more about additional capabilities of Klippy extras, check out the [built-in Klippy extras](https://github.com/Klipper3d/klipper/tree/master/klippy/extras).
- For further explanation of topics on this page, open the dropdowns.

---

Next example:

[Example 2: BetterGreeter :fontawesome-brands-python:](extras-ex2.md){ .md-button }