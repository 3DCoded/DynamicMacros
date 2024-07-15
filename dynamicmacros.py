import jinja2
from .gcode_macro import TemplateWrapper
from pathlib import Path
import configparser
import os

config_path = Path(os.path.expanduser('~')) / 'printer_data' / 'config'

class DynamicMacros:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object('gcode')
        self.fnames = config.getlist('configs')
        self.macros = {}
        
        self.gcode.register_command(
            'DYNAMIC_MACRO',
            self.cmd_DYNAMIC_MACRO,
            desc='Run Dynamic Macro'
        )

        self._update_macros()
        # for name in self.macros.keys():
        #     self.gcode.register_command(name.upper(), self.generate_cmd(name))
    
    def register_macro(self, macro):
        self.gcode.register_command(macro.name.upper(), self.generate_cmd(macro.name.upper()), desc=macro.desc)
        self.macros[macro.name] = macro

    def unregister_macro(self, macro):
        if macro in self.macros:
            self.gcode.register_command(macro.name.upper())
            del self.macros[macro.name]
    
    def cmd_DYNAMIC_MACRO(self, gcmd):
        macro = gcmd.get('MACRO')
        params = gcmd.get_command_parameters()
        rawparams = gcmd.get_raw_command_parameters()
        self._run_macro(macro, params, rawparams)
    
    def generate_cmd(self, name):
        def cmd(gcmd):
            params = gcmd.get_command_parameters()
            rawparams = gcmd.get_raw_command_parameters()
            self._run_macro(name, params, rawparams)
        return cmd
    
    def _run_macro(self, macro_name, params, rawparams):
        self._update_macros()
        macro = self.macros[macro_name]
        macro.run(params, rawparams)
    
    def _update_macros(self):
        for macro in self.macros:
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
    def __init__(self, name, raw, printer, desc=''):
        self.name = name
        self.raw = raw
        self.printer = printer
        self.desc = desc
        self.env = jinja2.Environment('{%', '%}', '{', '}')
        self.template = TemplateWrapper(self.printer, self.env, self.name, self.raw)
        self.variables = {}
    
    def from_section(config, section, printer):
        raw = config.get(section, 'gcode')
        name = section.split()[1]
        desc = config.get(section, 'description') if config.has_option(section, 'description') else ''
        return DynamicMacro(name, raw, printer, desc=desc)
    
    def run(self, params, rawparams):
        kwparams = dict(self.variables)
        kwparams.update(self.template.create_template_context())
        kwparams['params'] = params
        kwparams['rawparams'] = rawparams
        self.template.run_gcode_from_command(kwparams)
    
def load_config(config):
    return DynamicMacros(config)