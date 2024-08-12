# Experimental Features

!!! warning
    The features on this page are experimental, and untested or only lightly tested. Proceed at your own risk.

## Macro Clusters

Dynamic Macro clusters allow for multiple `[dynamicmacros]` configuration sections, and allow for security features. 

To configure a Dynamic Macro cluster, create a `[dynamicmacros name]` section shown below:

```cfg
[dynamicmacros mycluster]
configs: cluster.cfg
```

This section is configured mostly the same as a standard `[dynamicmacros]` config section. The differences between clusters and standard syntax are two parameters:

- `python_enabled`
- `printer_enabled`

By default, both of these are set to `true`. If you want to disable either the Python functionality, or accessing the `printer` object, you can change the configuration as shown below:

=== "Disable Python"
    ```cfg hl_lines="3"
    [dynamicmacros mycluster]
    configs: cluster.cfg
    python_enabled: false
    ```
=== "Disable Printer"
    ```cfg hl_lines="3"
    [dynamicmacros mycluster]
    configs: cluster.cfg
    printer_enabled: false
    ```
=== "Disable Both"
    ```cfg hl_lines="3-4"
    [dynamicmacros mycluster]
    configs: cluster.cfg
    python_enabled: false
    printer_enabled: false
    ```