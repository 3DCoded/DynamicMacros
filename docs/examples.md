---
comments: true
---

# Example Macros

This page will hold several different Dynamic Macro examples. Note that most of the examples here are specific to Dynamic Macros only.

## M900

!!! info "Normal Macro"

In Marlin, M900 K is used to set pressure/linear advance. Now, you can use it in Klipper too:

```cfg
[gcode_macro M900]
description: Set Pressure Advance
gcode:
  {% set k = params.K|default(0)|float %}
  {% if k < 1 %}
    SET_PRESSURE_ADVANCE ADVANCE={k}
  {% endif %}
```

## Recursion

!!! success "Dynamic Macro"

These are a few example Dynamic Macros to demonstrate the recursive functionality of Dynamic Macros.

```cfg title="Counting to 10"
[gcode_macro COUNT]
gcode:
    {% set num = params.NUM|default(1)|int %}
    {% if num <= 10 %}
        RESPOND MSG={num}
        COUNT NUM={num+1} # Count up 1
    {% else %}
        RESPOND MSG="Done Counting"
    {% endif %}
```

```cfg title="Load to Filament Sensor"
[gcode_macro LOAD_TO_FSENSOR]
gcode:
    {% set val = printer["filament_sensor fsensor"].filament_detected %}
    {% if val == 0 %}
        M83
        G1 E50 F900 # Move filament 50mm forwards
        RESPOND MSG="Waiting for fsensor"
        LOAD_TO_FSENSOR # Recursion
    {% else %}
        G1 E65 F900 # Move filament to nozzle
        RESPOND MSG="Filament Loaded"
    {% endif %}
```

## Receiving Position Updates

!!! success "Dynamic Macro"

This is an example Dynamic Macro to demonstrate the ability to receive position updates from within the same macro.

```cfg
[gcode_macro DYNAMIC_MOVE]
gcode:
  G28


  M117 Before: {printer.toolhead.position.z}
  # Above displays position after G28
  G90
  G1 Z20


  M117 After: {printer.toolhead.position.z}
  # Above displays position after G1
```

## Preserving Variables

!!! success "Dynamic Macro"

This is an example of how to preserve variables across triple-newlines in Dynamic Macros.

```cfg
[gcode_macro VARIABLES]
gcode:
    {% set num = update("num", 10) %}
    M117 {num}


    M117 {num}
    # Above line outputs 10
```

## Advanced Macros

Thank you to [@mykepredko](https://klipper.discourse.group/u/mykepredko/summary) on the [Klipper Discourse](https://klipper.discourse.group/) for these macro ideas and for testing them.

### Query ADXL345 Accelerometer

!!! success "Dynamic Macro"

This macro reads the current acceleration values from an ADXL345 accelerometer.

```cfg
[gcode_macro READ_ADXL]
gcode:
  {% set values = python_file('read_adxl.py') %}
  RESPOND TYPE=command MSG="Response={values}"
#  {% if values == "Python Error" %}
  {% if values == "No ADXL345" %}
    RESPOND TYPE=command MSG="READ_ADXL: No ADXL345 Present"
  {% else %}
    RESPOND TYPE=command MSG="READ_ADXL: ADXL345 Present"
    RESPOND TYPE=command MSG="READ_ADXL: x={values.x}, y={values.y}, z={values.z}"
  {% endif %}
```

```python title="read_adxl.py"
try:
  adxl = printer.lookup_object('adxl345')
  aclient = adxl.start_internal_client()
  printer.lookup_object('toolhead').dwell(.1)
  aclient.finish_measurements()
  values = aclient.get_samples()
  _, x, y, z = values[-1]
  output({
    "x": x,
    "y": y,
    "z": z,
  })
except:
  output("No ADXL345")
```

### Query BLTouch

!!! success "Dynamic Macro"

This macro queries the status of a BLTouch sensor.

```cfg
[gcode_macro QUERY_BLTOUCH]
gcode:
  {% set values = python_file('read_blt.py') %}
  RESPOND TYPE=command MSG="BLT Object={values}"
```

```python title="read_blt.py"
blt = printer.lookup_object('bltouch')
toolhead = printer.lookup_object('toolhead')
print_time = toolhead.get_last_move_time()
status = blt.query_endstop(print_time)
output(status)
```

### Read TMC field

!!! success "Dynamic Macro"

This macro reads the given field on the given TMC2209 driver, but can be adapted to use any TMC driver.

```cfg
[gcode_macro READ_TMC_FIELD]
gcode:
  {% set field_name = params.FIELD %}
  {% set stepper_name = params.STEPPER %}
  {% set value = python_file('read_tmc_field.py', field=field_name, stepper=stepper_name) %}
  RESPOND MSG="\"tmc2209 {stepper_name}-{field_name}\" = {value}"
```

```python title="read_tmc_field.py"
field = kwargs['field']
stepper = kwargs['stepper']

tmc = printer.lookup_object(f'tmc2209 {stepper}')

register = tmc.fields.field_to_register[field] # Find register for given field

reg_val = tmc.mcu_tmc.get_register(register)
if reg_val == 0: # Queried register
  value = tmc.fields.get_field(field, reg_name=register)
else: # Write-only register
  value = tmc.fields.get_field(field, reg_value=reg_val, reg_name=register)
output(value)
```