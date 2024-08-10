# Development Status

## Features

- Editing macros without restarting Klipper
- Accessing printer information from within Dynamic Macros
- Accessing parameters from within Dynamic Macros
- Adding new Dynamic Macros without restarting Klipper
- Removing existing Dynamic Macros without restarting Klipper
- Renaming Dynamic Macros without restarting Klipper
- Dynamic Macro descriptions
- Dynamic Macro variables
- Retrieving variables from other macros
- Support for `rename_existing`
- Running Python from within a Dynamic Macro
- Dynamic `delayed_gcode` implementation

## Planned Features

A checkmark indicates a feature is experimental.

- [X] Allow configuring multiple `dynamicmacros` config sections as clusters
    - [X] Disable Python per-cluster
    - [X] Disable `printer` object per-cluster
- [ ] Better error handling
- [ ] Klippy extras tutorial