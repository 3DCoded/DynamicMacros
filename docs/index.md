# Klipper Dynamic Macros

**Never restart Klipper again for simple macros.**

---

Klipper Dynamic Macros is an unofficial way to update macros without restarting Klipper, so you can update macros mid-print and see their results live. It also supports extra features that normal GCode Macros don't have.

## Features

- [Recursion](recursion.md)
- [Receiving Variables](receivingvariables.md)
- [Utility Functions](utilities.md)
- [Variables](variables.md)

## How Normal Macros Work

Your macros are written in a `.cfg` file, then included into your `printer.cfg`. When Klipper restarts, it parses these files and saves the macros internally (you can't change them without restarting Klipper). When a macro is called, the cached code is interpreted and run.

## How Dynamic Macros Work

Your macros are written in a `.cfg` file, then the relative path to that file is configured in a `[dynamicmacros]` config section. The config files are read and parsed every time you run the macro, allowing you to update macros without restarting Klipper.

## Get Started
Follow [Setup](setup.md) to get started with Dynamic Macros.

## Planned Features

See [Development Status](devstatus.md) for the currently available features, and planned features.

## Examples

See [Example Macros](examples.md) for examples of Dynamic Macros.

## More Projects

If you like this project, don't forget to give it a star! Also, check out the [3MS](https://github.com/3dcoded/3ms), a modular multimaterial system for Klipper!