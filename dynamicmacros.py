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
            self.cmd_DYNAMIC_MACRO
        )
    
    def cmd_DYNAMIC_MACRO(self, gcmd):
        macro = gcmd.get('MACRO')
        params = gcmd.get_command_parameters()
        rawparams = gcmd.get_raw_command_parameters()
        self._run_macro(macro, params, rawparams)
    
    def _run_macro(self, macro_name, params, rawparams):
        self._update_macros()
        macro = self.macros[macro_name]
        macro.run(params, rawparams)
    
    def _update_macros(self):
        for fname in self.fnames:
            path = config_path / fname
            config = configparser.RawConfigParser()
            config.read(path)
            for section in config.sections():
                if section.split()[0] == 'gcode_macro':
                    name = section.split()[1]
                    self.macros[name] = DynamicMacro.from_section(config, section, self.printer)

class DynamicMacro:
    def __init__(self, name, raw, printer):
        self.name = name
        self.raw = raw
        self.printer = printer
        self.env = jinja2.Environment('{%', '%}', '{', '}')
        self.template = TemplateWrapper(self.printer, self.env, self.name, self.raw)
        self.variables = {}
    
    def from_section(config, section, printer):
        raw = config.get(section, 'gcode')
        name = section.split()[1]
        return DynamicMacro(name, raw, printer)
    
    def run(self, params, rawparams):
        kwparams = dict(self.variables)
        kwparams.update(self.template.create_template_context())
        kwparams['params'] = params
        kwparams['rawparams'] = rawparams
        self.template.run_gcode_from_command(kwparams)
    
def load_config(config):
    return DynamicMacros(config)