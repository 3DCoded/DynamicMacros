import jinja2
from .gcode_macro import TemplateWrapper
from pathlib import Path
import configparser
import os
import ast
import json

config_path = Path(os.path.expanduser('~')) / 'printer_data' / 'config'

class DynamicMacros:
    def __init__(self, config):
        self.printer = config.get_printer()
        DynamicMacros.printer = self.printer
        self.gcode = self.printer.lookup_object('gcode')
        self.fnames = config.getlist('configs')
        self.macros = {}
        self.placeholder = DynamicMacro('Error', 'RESPOND MSG="ERROR"', self.printer)
        
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
        self.macros[macro.name] = macro
        if (macro.name not in self.gcode.ready_gcode_handlers) and (macro.name not in self.gcode.base_gcode_handlers):
            self.gcode.register_command(macro.name.upper(), self.generate_cmd(macro), desc=macro.desc)
            self.printer.objects[f'gcode_macro {macro.name}'] = macro
    
    def cmd_SET_DYNAMIC_VARIABLE(self, gcmd):
        name = gcmd.get('MACRO')
        variable = gcmd.get('VARIABLE')
        value = gcmd.get('VALUE')
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
        self.gcode.register_command(macro.name.upper(), None)
        if macro in self.macros:
            self.macros[macro.name] = None
            del self.macros[macro.name]
    
    def cmd_DYNAMIC_MACRO(self, gcmd):
        try:
            self._update_macros()
            macro_name = gcmd.get('MACRO', '')
            if not macro_name:
                return
            params = gcmd.get_command_parameters()
            rawparams = gcmd.get_raw_command_parameters()
            macro = self.macros.get(macro_name, self.placeholder)
            self._run_macro(macro, params, rawparams)
            msg = macro.vars
            gcmd.respond_info(f'Message: {msg}')
        except Exception as e:
            gcmd.respond_info(str(e))
    
    def generate_cmd(self, macro):
        def cmd(gcmd):
            params = gcmd.get_command_parameters()
            rawparams = gcmd.get_raw_command_parameters()
            macro.run(params, rawparams)
        return cmd
    
    def _run_macro(self, macro, params, rawparams):
        macro.run(params, rawparams)
    
    def _update_macros(self):
        for macro in self.macros.values():
            self.unregister_macro(macro)
        for fname in self.fnames:
            path = config_path / fname
            config = configparser.RawConfigParser()
            config.read(path)
            for section in config.sections():
                if section.split()[0] == 'gcode_macro':
                    name = section.split()[1]
                    macro = DynamicMacro.from_section(config, section, self.printer)
                    self.macros[name] = macro
                    self.register_macro(macro)

class DynamicMacro:
    def __init__(self, name, raw, printer, desc='', variables={}, rename_existing=None):
        self.name = name
        self.raw = raw
        self.printer = printer
        self.gcode = self.printer.lookup_object('gcode')
        self.desc = desc
        self.variables = variables
        self.rename_existing = rename_existing
        self.vars = {}

        if self.rename_existing is not None:
            self.rename()

        self.gcodes = self.raw.split('\n\n\n')
        self.templates = []
        for gcode in self.gcodes:
            self.templates.append(self.generate_template(gcode))
    
    def generate_template(self, gcode):
        env = jinja2.Environment('{%', '%}', '{', '}')
        return TemplateWrapper(self.printer, env, self.name, gcode)
    
    def rename(self):
        prev_cmd = self.gcode.register_command(self.name, None)
        prev_desc = f'Renamed from {self.name}'
        if prev_cmd is None:
            return
        self.gcode.register_command(self.rename_existing, prev_cmd, desc=prev_desc)
    
    def update(self, name, val):
        self.vars[name] = val
        return val

    def get_macro_variables(self, macro_name):
        macro = self.printer.lookup_object(f'gcode_macro {macro_name}')
        return macro.variables

    def update_from_dict(self, dictionary):
        self.vars.update(dictionary)
        return dictionary
    
    def from_section(config: configparser.RawConfigParser, section, printer):
        raw = config.get(section, 'gcode')
        name = section.split()[1]
        desc = config.get(section, 'description') if config.has_option(section, 'description') else 'No Description'
        rename_existing = config.get(section, 'rename_existing') if config.has_option(section, 'rename_existing') else None
        variables = {}
        for key, value in config.items(section):
            if key.startswith('variable_'):
                variable = key[len('variable_'):]
                variables[variable] = value
        return DynamicMacro(name, raw, printer, desc=desc, variables=variables, rename_existing=rename_existing)
    
    def run(self, params, rawparams):
        for template in self.templates:
            self._run(template, params, rawparams)
    
    def _run(self, template, params, rawparams):
        kwparams = dict(self.variables)
        kwparams.update(self.vars)
        kwparams.update(template.create_template_context())
        kwparams['params'] = params
        kwparams['rawparams'] = rawparams
        kwparams['update'] = self.update
        kwparams['get_macro_variables'] = self.get_macro_variables
        kwparams['update_from_dict'] = self.update_from_dict
        template.run_gcode_from_command(kwparams)
    
def load_config(config):
    return DynamicMacros(config)