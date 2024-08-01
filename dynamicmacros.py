import jinja2
from .gcode_macro import TemplateWrapper
from pathlib import Path
import configparser
import os
import ast
import json
from secrets import token_hex

config_path = Path(os.path.expanduser('~')) / 'printer_data' / 'config'

class DynamicMacros:
    clusters = {}

    def __init__(self, config):
        # Initialize variables
        self.printer = config.get_printer()
        DynamicMacros.printer = self.printer
        self.gcode = self.printer.lookup_object('gcode')
        self.fnames = config.getlist('configs')

        self.macros = {} # Holds macros in name: DynamicMacro format
        self.placeholder = DynamicMacro('Error', 'RESPOND MSG="ERROR"', self.printer) # Placeholder macro if macro isn't found by name
        
        self.gcode.register_command(
            'DYNAMIC_MACRO',
            self.cmd_DYNAMIC_MACRO,
            desc='Run Dynamic Macro'
        )
        self.gcode.register_command(
            'SET_DYNAMIC_VARIABLE',
            self.cmd_SET_DYNAMIC_VARIABLE,
            desc="Set the value of a G-Code macro variable"
        )

        self._update_macros()
    
    def register_macro(self, macro):
        self.macros[macro.name] = macro # update internal macros list
        if (macro.name not in self.gcode.ready_gcode_handlers) and (macro.name not in self.gcode.base_gcode_handlers):
            self.gcode.register_command(macro.name.upper(), self.generate_cmd(macro), desc=macro.desc) # register GCode command
            self.printer.objects[f'gcode_macro {macro.name}'] = macro # trick Klipper into thinking this is a gcode_macro
    
    def cmd_SET_DYNAMIC_VARIABLE(self, gcmd):
        cluster = gcmd.get('CLUSTER', None)
        if cluster is not None and cluster in self.clusters:
            return self.clusters[cluster]._cmd_SET_DYNAMIC_VARIABLE(gcmd)
        return self._cmd_SET_DYNAMIC_VARIABLE(gcmd)

    def _cmd_SET_DYNAMIC_VARIABLE(self, gcmd):
        name = gcmd.get('MACRO')
        variable = gcmd.get('VARIABLE')
        value = gcmd.get('VALUE')

        # Convert to a literal, if possible
        try:
            literal = ast.literal_eval(value)
            json.dumps(literal, separators=(',', ':'))
        except (SyntaxError, TypeError, ValueError) as e:
            raise gcmd.error("Unable to parse '%s' as a literal: %s" %
                             (value, e))
        
        if name is not None:
            name = name.upper()
            if name in self.macros:
                macro = self.macros[name]
                macro.variables[variable] = literal

    def unregister_macro(self, macro):
        self.gcode.register_command(macro.name.upper(), None) # unregister GCode command
        if macro in self.macros:
            self.macros[macro.name] = None # update internal macros list
            del self.macros[macro.name] # remove macro from internal macros list
    
    def cmd_DYNAMIC_MACRO(self, gcmd):
        cluster = gcmd.get('CLUSTER', None)
        if cluster is not None and cluster in self.clusters:
            return self.clusters[cluster]._cmd_DYNAMIC_MACRO(gcmd)
        return self._cmd_DYNAMIC_MACRO(gcmd)
    
    def _cmd_DYNAMIC_MACRO(self, gcmd):
        try:
            self._update_macros()
            macro_name = gcmd.get('MACRO', '')
            if not macro_name:
                return
            params = gcmd.get_command_parameters()
            rawparams = gcmd.get_raw_command_parameters()
            macro = self.macros.get(macro_name, self.placeholder)
            self._run_macro(macro, params, rawparams) # Run macro
        except Exception as e:
            gcmd.respond_info(str(e))
    
    def generate_cmd(self, macro):
        def cmd(gcmd):
            params = gcmd.get_command_parameters()
            rawparams = gcmd.get_raw_command_parameters()
            self._run_macro(macro, params, rawparams)
        return cmd
    
    def _run_macro(self, macro, params, rawparams):
        macro.run(params, rawparams)
    
    def _update_macros(self):
        for macro in self.macros.values():
            self.unregister_macro(macro) # unregister all macros
        for fname in self.fnames:
            path = config_path / fname # create full file path

            # Pase config files
            config = configparser.RawConfigParser(strict=False, inline_comment_prefixes=(';', '#'))
            config.read(path)
            for section in config.sections():
                if section.split()[0] == 'gcode_macro': # Check if section is a gcode_macro
                    name = section.split()[1] # get name
                    macro = DynamicMacro.from_section(config, section, self.printer) # create DynamicMacro from config section
                    self.macros[name] = macro
                    self.register_macro(macro) # register new macro

class DynamicMacrosCluster(DynamicMacros):
    def __init__(self, config):
        # Initialize variables
        self.printer = config.get_printer()
        self.name = config.get_name().split()[1]
        DynamicMacros.printer = self.printer
        self.gcode = self.printer.lookup_object('gcode')
        self.fnames = config.getlist('configs')

        DynamicMacros.clusters[self.name] = self

        # Cluster-specific settings
        self.python_enabled = config.getboolean('python_enabled', True)
        self.printer_enabled = config.getboolean('printer_enabled', True)

        self.macros = {} # Holds macros in name: DynamicMacro format
        self.placeholder = DynamicMacro('Error', 'RESPOND MSG="ERROR"', self.printer) # Placeholder macro if macro isn't found by name

        self._update_macros()
    
    def disabled_func(self, name, msg):
        def func(*args, **kwargs):
            self.gcode.respond_info(f'WARNING: {name} attempted to {msg} when disabled.')
            self.gcode.respond_info(f'{name} has been blocked from performing a disabled task.')
        return func

    def sandboxed_kwparams(self, macro, func):
        def func(template, params, rawparams):
            kwparams = func(template, params, rawparams)
            if not self.python_enabled:
                kwparams['python'] = self.disabled_func(macro.name, 'run Python code')
                kwparams['python_file'] = self.disabled_func(macro.name, 'run Python file')
            if not self.printer_enabled:
                kwparams['printer'] = self.disabled_func(macro.name, 'access printer object')
            macro.kwparams = kwparams
        return func
    
    def _run_macro(self, macro, params, rawparams):
        # If Python is disabled, prevent from running Python
        sandboxed = self.sandboxed_kwparams(macro, macro._update_kwparams)
        macro.update_kwparams = sandboxed
        macro.run(params, rawparams)

class DynamicMacro:
    def __init__(self, name, raw, printer, desc='', variables={}, rename_existing=None, initial_duration=None, repeat=False):
        # initialize variables
        self.name = name
        self.raw = raw
        self.printer = printer
        self.gcode = self.printer.lookup_object('gcode')
        self.desc = desc
        self.variables = variables
        self.rename_existing = rename_existing
        self.initial_duration = initial_duration
        self.repeat = repeat
        self.vars = {}

        if self.initial_duration is not None:
            self.reactor = self.printer.get_reactor()
            self.timer_handler = None
            self.inside_timer = False
            self.printer.register_event_handler("klippy:ready", self._handle_ready)

        if self.rename_existing is not None:
            self.rename() # rename previous macro if necessary

        self.gcodes = self.raw.split('\n\n\n') # split gcode by triple-newlines
        self.templates = []
        for gcode in self.gcodes:
            self.templates.append(self.generate_template(gcode))
    
    def _handle_ready(self):
        waketime = self.reactor.monotonic() + self.initial_duration
        self.timer_handler = self.reactor.register_timer(
            self._gcode_timer_event, waketime)
        
    def _gcode_timer_event(self, eventtime):
        self.inside_timer = True
        nextwake = self.reactor.NEVER
        if self.repeat:
            nextwake = eventtime + self.initial_duration
        self.run({}, '')
        self.inside_timer = False
        return nextwake
    
    def generate_template(self, gcode):
        env = jinja2.Environment('{%', '%}', '{', '}')
        return TemplateWrapper(self.printer, env, self.name, gcode)
    
    def rename(self):
        prev_cmd = self.gcode.register_command(self.name, None) # get previous command
        prev_desc = f'Renamed from {self.name}'
        if prev_cmd is None:
            return
        self.gcode.register_command(self.rename_existing, prev_cmd, desc=prev_desc) # rename previous command
    
    # --- Utility Functions ---

    # Update vars from within a macro
    def update(self, name, val):
        self.vars[name] = val
        return val

    # Get all the variables from another macro
    def get_macro_variables(self, macro_name):
        macro = self.printer.lookup_object(f'gcode_macro {macro_name}')
        return macro.variables

    # Update vars from a dictionary
    def update_from_dict(self, dictionary):
        self.vars.update(dictionary)
        return dictionary

    # Run Python code from within a macro
    def python(self, python, *args, **kwargs):
        key = f'_python{token_hex()}'
        def output(value):
            return self.update(key, value)
        python_vars = {}
        for k, v in self.kwparams.items():
            python_vars[k] = v
        python_vars['output'] = output
        python_vars['gcode'] = self.gcode.run_script_from_command
        python_vars['printer'] = self.printer
        python_vars['print'] = lambda *args: self.gcode.run_script_from_command('RESPOND MSG="' + ' '.join(map(str, args)) + '"')
        python_vars['args'] = args
        python_vars['kwargs'] = kwargs
        try:
            exec(
                python,
                python_vars,
            )
        except Exception as e:
            self.gcode.respond_info(f'Python Error:\n{e}')
        return self.vars.get(key)

    # Run Python file from within a macro
    def python_file(self, fname, *args, **kwargs):
        try:
            with open(config_path / fname, 'r') as file:
                text = file.read()
        except Exception as e:
            self.gcode.respond_info('Python file missing')
        return self.python(text, *args, **kwargs)
    
    def from_section(config: configparser.RawConfigParser, section, printer):
        raw = config.get(section, 'gcode')
        name = section.split()[1]
        desc = config.get(section, 'description') if config.has_option(section, 'description') else 'No Description'
        rename_existing = config.get(section, 'rename_existing') if config.has_option(section, 'rename_existing') else None
        initial_duration = config.getfloat(section, 'initial_duration') if config.has_option(section, 'initial_duration') else None
        repeat = config.getboolean(section, 'repeat') if config.has_option(section, 'repeat') else False
        variables = {}
        for key, value in config.items(section):
            if key.startswith('variable_'):
                variable = key[len('variable_'):]
                variables[variable] = value
        return DynamicMacro(name, raw, printer, desc=desc, variables=variables, rename_existing=rename_existing, initial_duration=initial_duration, repeat=repeat)
    
    def get_status(self, *args, **kwargs):
        return self.variables
    
    def _update_kwparams(self, template, params, rawparams):
        kwparams = dict(self.variables)
        kwparams.update(self.vars)
        kwparams.update(template.create_template_context())
        kwparams['params'] = params
        kwparams['rawparams'] = rawparams
        kwparams['update'] = self.update
        kwparams['get_macro_variables'] = self.get_macro_variables
        kwparams['update_from_dict'] = self.update_from_dict
        kwparams['python'] = self.python
        kwparams['python_file'] = self.python_file
        self.kwparams = kwparams
    
    def update_kwparams(self, template, params, rawparams):
        self._update_kwparams(template, params, rawparams)

    def run(self, params, rawparams):
        for template in self.templates:
            self._run(template, params, rawparams)
    
    def _run(self, template, params, rawparams):
        self.update_kwparams(template, params, rawparams)
        template.run_gcode_from_command(self.kwparams)
    
def load_config(config):
    return DynamicMacros(config)

def load_config_prefix(config):
    return DynamicMacrosCluster(config)