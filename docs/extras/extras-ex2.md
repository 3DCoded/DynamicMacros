# Example 2: BetterGreeter

For this tutorial, we are going to improve on the greeter code used in [Structure](extras-ex1.md). 

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

!!! question inline end "Quiz"
    === "Question"
        If there was a configuration option (int) named `repeats`, how would you get it in the initializer?
    === "Answer"
        `#!py config.getint('repeats')`

Here, the `printer`, `reactor`, `gcode`, and `message` variables are the same as in the previous Klippy extra. However, in this case, there are a couple new variables:

- `name` is explained in [the last section of Structure](extras-ex1.md#other-things).
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

Here, a few parts are similar to the example in [Structure](extras-ex1.md), but not identical. Let's start with the GCode command.

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

## Functions

The next part to creating this Klippy extra is the functions.

There are three functions in the `Greeting` class:

- `ready_handler`
- `_greet`
- `cmd_GREETING`

??? info "Flowchart"
    ```mermaid
    graph TD
    A[klippy:ready] --> B[_ready_handler]
        B --> C[Wait self.delay seconds]
        C --> D[_greet]
        D --> E[Display self.message]
        F[cmd_GREETING] --> E
    ```

The first function, `_ready_handler`:

```py title="greeting.py" hl_lines="22-24"
--8<-- "greeting.py:clsheader"
--8<-- "greeting.py:initheader"
--8<-- "greeting.py:readcfg"
--8<-- "greeting.py:regcmd"

--8<-- "greeting.py:handler"
```

This function takes no parameters, and runs when Klippy reports `#!py "klippy:ready"`.

Inside, the `waketime` variable is declared as `#!py self.reactor.monotonic() + self.delay`. Let's break this declaration down:

- `#!py self.reactor.monotonic()` This is the current Klippy time
- `#!py  + self.delay` This adds `#!py self.delay` to the current time.

The result is that `waketime` contains the Klippy time for `#!py self.delay` seconds in the future. Finally, we use `#!py self.reactor.register_timer` to register this time, telling it to run `#!py self._greet()` when the time occurs.

---

The next function, `_greet`:

```py title="greeting.py" hl_lines="26-28"
--8<-- "greeting.py:clsheader"
--8<-- "greeting.py:initheader"
--8<-- "greeting.py:readcfg"
--8<-- "greeting.py:regcmd"

--8<-- "greeting.py:handler"

--8<-- "greeting.py:agreet"
```

This function takes an optional `eventtime` parameter (unused) (1), and prints out `#!py self.message` to the Klipper console, using `#!py self.gcode.respond_info`.
{.annotate}

1. This is passed by Klippy when it calls `_greet()` after the timer occurs.

!!! tip
    If you want the timer function to repeat, you can return the provided `eventtime` plus any number of seconds in the future, and it will repeat.

---

The final function in this class is the `cmd_GREETING` function:

```py title="greeting.py" hl_lines="30-32"
--8<-- "greeting.py:clsheader"
--8<-- "greeting.py:initheader"
--8<-- "greeting.py:readcfg"
--8<-- "greeting.py:regcmd"

--8<-- "greeting.py:handler"

--8<-- "greeting.py:agreet"

--8<-- "greeting.py:greet"
```

This function simply calls `#!py self._greet()`, which displays `#!py self.message` to the Klipper terminal.

## Full Code

The full code of this Klippy extra is:

```py title="greeting.py"
--8<-- "greeting.py:code"
```

You can install it following [these](extras-ex1.md#install) instructions, replacing `greeter.py` with `greeting.py`.

---

Last example (so far):

[Example 3: KlipperMaintenance :fontawesome-solid-angle-right:](extras-ex3.md){ .md-button }