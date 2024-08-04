import jinja2
from .gcode_macro import TemplateWrapper
from pathlib import Path
import configparser
import os
import ast
import json
from secrets import token_hex

# Define the path to the configuration files
config_path = Path(os.path.expanduser('~')) / 'printer_data' / 'config'

class MacroConfigParser:
    def __init__(self, config_path):
        self.config_path = config_path

    def read_config_file(self, filename):
        path = self.config_path / filename
        config = configparser.RawConfigParser(strict=False, inline_comment_prefixes=(';', '#'))
        config.read(path)
        return config

    def extract_macros(self, config):
        macros = {}
        for section in config.sections():
            if section.startswith('gcode_macro'):
                macro = DynamicMacro.from_section(config, section, DynamicMacros.printer)
                macros[macro.name] = macro
        return macros

class DynamicMacros:
    clusters = {}

    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object('gcode')
        self.fnames = config.getlist('configs')
        DynamicMacros.printer = self.printer
        self.macros = {}
        self.placeholder = DynamicMacro('Error', 'RESPOND MSG="ERROR"', self.printer)

        # Register commands
        self.gcode.register_command('DYNAMIC_MACRO', self.cmd_DYNAMIC_MACRO, desc='Run Dynamic Macro')
        self.gcode.register_command('SET_DYNAMIC_VARIABLE', self.cmd_SET_DYNAMIC_VARIABLE, desc="Set macro variable value")

        self.config_parser = MacroConfigParser(config_path)
        self._update_macros()

    def register_macro(self, macro):
        self.macros[macro.name] = macro
        if (macro.name not in self.gcode.ready_gcode_handlers) and (macro.name not in self.gcode.base_gcode_handlers):
            self.gcode.register_command(macro.name.upper(), self.generate_cmd(macro), desc=macro.desc)
            self.printer.objects[f'gcode_macro {macro.name}'] = macro

    def cmd_SET_DYNAMIC_VARIABLE(self, gcmd):
        cluster = gcmd.get('CLUSTER')
        if cluster and cluster in self.clusters:
            return self.clusters[cluster]._cmd_SET_DYNAMIC_VARIABLE(gcmd)
        return self._cmd_SET_DYNAMIC_VARIABLE(gcmd)

    def _cmd_SET_DYNAMIC_VARIABLE(self, gcmd):
        name = gcmd.get('MACRO')
        variable = gcmd.get('VARIABLE')
        value = gcmd.get('VALUE')

        try:
            literal = ast.literal_eval(value)
            json.dumps(literal, separators=(',', ':'))
        except (SyntaxError, TypeError, ValueError) as e:
            raise gcmd.error(f"Unable to parse '{value}' as a literal: {e}")

        if name:
            macro = self.macros.get(name.upper())
            if macro:
                macro.variables[variable] = literal

    def unregister_macro(self, macro):
        macro.repeat = False
        self.gcode.register_command(macro.name.upper(), None)
        self.macros.pop(macro.name, None)

    def cmd_DYNAMIC_MACRO(self, gcmd):
        cluster = gcmd.get('CLUSTER')
        if cluster and cluster in self.clusters:
            return self.clusters[cluster]._cmd_DYNAMIC_MACRO(gcmd)
        return self._cmd_DYNAMIC_MACRO(gcmd)

    def _cmd_DYNAMIC_MACRO(self, gcmd):
        try:
            self._update_macros()
            macro_name = gcmd.get('MACRO', '')
            if macro_name:
                params = gcmd.get_command_parameters()
                rawparams = gcmd.get_raw_command_parameters()
                macro = self.macros.get(macro_name, self.placeholder)
                self._run_macro(macro, params, rawparams)
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
        self._unregister_all_macros()
        self._load_and_register_macros_from_files()

    def _unregister_all_macros(self):
        for macro in list(self.macros.values()):
            self.unregister_macro(macro)

    def _load_and_register_macros_from_files(self):
        for fname in self.fnames:
            self._load_and_register_macros_from_file(fname)

    def _load_and_register_macros_from_file(self, fname):
        config = self.config_parser.read_config_file(fname)
        new_macros = self.config_parser.extract_macros(config)
        self._register_new_macros(new_macros)

    def _register_new_macros(self, new_macros):
        for name, macro in new_macros.items():
            self.macros[name] = macro
            self.register_macro(macro)

class DynamicMacrosCluster(DynamicMacros):
    def __init__(self, config):
        self.printer = config.get_printer()
        self.name = config.get_name().split()[1]
        self.gcode = self.printer.lookup_object('gcode')
        self.fnames = config.getlist('configs')
        self.macros = {}
        self.placeholder = DynamicMacro('Error', 'RESPOND MSG="ERROR"', self.printer)
        DynamicMacros.printer = self.printer
        DynamicMacros.clusters[self.name] = self

        self.python_enabled = config.getboolean('python_enabled', True)
        self.printer_enabled = config.getboolean('printer_enabled', True)

        self.config_parser = MacroConfigParser(config_path)
        self._update_macros()

    def disabled_func(self, name, msg):
        def func(*args, **kwargs):
            self.gcode.respond_info(f'WARNING: {name} attempted to {msg} when disabled.')
            self.gcode.respond_info(f'{name} has been blocked from performing a disabled task.')
        return func

    def sandboxed_kwparams(self, macro):
        def func(template, params, rawparams):
            macro._update_kwparams(template, params, rawparams)
            if not self.python_enabled:
                macro.kwparams['python'] = self.disabled_func(macro.name, 'run Python code')
                macro.kwparams['python_file'] = self.disabled_func(macro.name, 'run Python file')
            if not self.printer_enabled:
                macro.kwparams['printer'] = None
        return func

    def _run_macro(self, macro, params, rawparams):
        macro.update_kwparams = self.sandboxed_kwparams(macro)
        macro.run(params, rawparams)

class DynamicMacro:
    def __init__(self, name, raw, printer, desc='', variables={}, rename_existing=None, initial_duration=None, repeat=False):
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

        if self.initial_duration:
            self.reactor = self.printer.get_reactor()
            self.timer_handler = None
            self.inside_timer = False
            self.printer.register_event_handler("klippy:ready", self._handle_ready)

        if self.rename_existing:
            self.rename()

        self.gcodes = self.raw.split('\n\n\n')
        self.templates = [self.generate_template(gcode) for gcode in self.gcodes]

    def _handle_ready(self):
        waketime = self.reactor.monotonic() + self.initial_duration
        self.timer_handler = self.reactor.register_timer(self._gcode_timer_event, waketime)

    def _gcode_timer_event(self, eventtime):
        self.inside_timer = True
        nextwake = eventtime + self.initial_duration if self.repeat else self.reactor.NEVER
        self.run({}, '')
        self.inside_timer = False
        return nextwake

    def generate_template(self, gcode):
        env = jinja2.Environment('{%', '%}', '{', '}')
        return TemplateWrapper(self.printer, env, self.name, gcode)

    def rename(self):
        prev_cmd = self.gcode.register_command(self.name, None)
        if prev_cmd:
            self.gcode.register_command(self.rename_existing, prev_cmd, desc=f'Renamed from {self.name}')

    def update(self, name, val):
        self.vars[name] = val
        return val

    def get_macro_variables(self, macro_name):
        macro = self.printer.lookup_object(f'gcode_macro {macro_name}')
        return macro.variables

    def update_from_dict(self, dictionary):
        self.vars.update(dictionary)
        return dictionary

    def python(self, python, *args, **kwargs):
        key = f'_python{token_hex()}'
        def output(value):
            return self.update(key, value)
        python_vars = {**self.kwparams, 'output': output, 'gcode': self.gcode.run_script_from_command, 'printer': self.printer}
        python_vars['print'] = lambda *args: self.gcode.run_script_from_command('RESPOND MSG="' + ' '.join(map(str, args)) + '"')
        python_vars['args'] = args
        python_vars['kwargs'] = kwargs
        try:
            exec(python, python_vars)
        except Exception as e:
            self.gcode.respond_info(f'Python Error:\n{e}')
        return self.vars.get(key)

    def python_file(self, fname, *args, **kwargs):
        try:
            with open(config_path / fname, 'r') as file:
                text = file.read()
        except Exception as e:
            self.gcode.respond_info('Python file missing')
        return self.python(text, *args, **kwargs)

    @staticmethod
    def from_section(config, section, printer):
        raw = config.get(section, 'gcode')
        name = section.split()[1]
        desc = config.get(section, 'description', fallback='No Description')
        rename_existing = config.get(section, 'rename_existing', fallback=None)
        initial_duration = config.getfloat(section, 'initial_duration', fallback=None)
        repeat = config.getboolean(section, 'repeat', fallback=False)
        variables = {key[len('variable_'):]: value for key, value in config.items(section) if key.startswith('variable_')}
        return DynamicMacro(name, raw, printer, desc=desc, variables=variables, rename_existing=rename_existing, initial_duration=initial_duration, repeat=repeat)

    def get_status(self, *args, **kwargs):
        return self.variables

    def _update_kwparams(self, template, params, rawparams):
        kwparams = {**self.variables, **self.vars, **template.create_template_context()}
        kwparams.update({'params': params, 'rawparams': rawparams, 'update': self.update, 'get_macro_variables': self.get_macro_variables, 'update_from_dict': self.update_from_dict, 'python': self.python, 'python_file': self.python_file})
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
