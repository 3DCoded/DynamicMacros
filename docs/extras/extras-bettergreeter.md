# BetterGreeter

!!! info
    This page is under construction.

For this tutorial, we are going to improve on the greeter code used in [Structure](extras-structure.md). 

For reference, the entire original greeter code is below:

???+ "Original Greeter"
    ```py
    --8<-- "greeter.py:code"
    ```

## Goals

For the `BetterGreeter`, we want the following features:

- Ability to have multiple different greetings
- Allow the user to choose if they want their greeting to display after Klipper starts, and if so, to set the delay
- Allow the user to set the message of the greeting

Here's an example configuration:

```cfg title="better_greeter.cfg"
--8<-- "better_greeter.cfg:full"
```

Here's the desired behavior (anything on the line of a `>` is a user-typed command):

```sh
> RESTART
Welcome to Klipper! # (1)!
Upload some GCode! # (2)!
> GREETING NAME=print_done
Print completed!
```

1. One second after `RESTART`
2. Two seconds after `RESTART`

## Creating the Base Class

The first step of creating a Klippy extra is to make the base class and the config function: 

```py
--8<-- "greeting.py:clsheader"
--8<-- "greeting.py:initheader"
        pass

# (1)!
--8<-- "greeting.py:loadcfg"
```

1. `load_config_prefix` is used here instead of `load_config` because there will be **multiple** `greeter` configuration sections.

## Reading the Configuration

The next step of our Klippy extra is to setup the class variables and read the parameters:

```py hl_lines="3-9"
--8<-- "greeting.py:clsheader"
--8<-- "greeting.py:initheader"
--8<-- "greeting.py:readcfg"
```

Here, the `printer`, `reactor`, `gcode`, and `message` variables are the same as in the previous Klippy extra. However, in this case, there are a couple new variables:

- `name` is explained in [the last section of Structure](extras-structure.md#other-things).
- `delay` is read as an `#!py int` from the `config` object, with default value `#!py 0`. The default value of `#!py 0` indicates it will not be run when Klippy starts.

## GCode Commands and Event Handler

After reading the configuration variables, we need to setup the GCode commands and event handler:

```py hl_lines="11-22"
--8<-- "greeting.py:clsheader"
--8<-- "greeting.py:initheader"
--8<-- "greeting.py:readcfg"

        #(1)!
--8<-- "greeting.py:regcmd"
```

1. `register_mux_command` is used here because there are **multiple** `greeting` configuration sections, and each should be called separately.

Here, a few parts are similar to the example in [Structure](extras-structure.md), but not identical. Let's start with the GCode command.

In the Structure example, the GCode command was registered with:

`#!py self.gcode.register_command('GREET', self.cmd_GREET, desc=self.cmd_GREET_help)`

In this new example, the GCode command is registered with:

```py
self.gcode.register_mux_command(
    'GREETING',
    'NAME',
    self.name,
    self.cmd_GREETING,
    desc=self.cmd_GREETING_help
)
```

The difference here is that there can be **multiple** `greeting` configuration sections, and as a result, multiple `Greeting` objects. To call each one separately, `register_mux_command` is used, passing the following parameters:

- Macro name: `#!py "GREETING"`
- Parameter name: `#!py "NAME"`
- Parameter value: `#!py self.name`
- Function: `#!py self.cmd_GREETING`
- Description `#!py self.cmd_GREETING_help`

Next, the `register_event_handler` is nearly identical to the Structure example, except in this case, it is run only `#!py if self.delay > 0`.

