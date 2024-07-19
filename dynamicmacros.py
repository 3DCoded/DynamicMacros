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
        self.placeholder = DynamicMacro('Placeholder', 'M117 ERROR', self.printer)
        
        self.gcode.register_command(
            'DYNAMIC_MACRO',
            self.cmd_DYNAMIC_MACRO,
            desc='Run Dynamic Macro'
        )

        self._update_macros()
    
    def register_macro(self, macro):
        self.macros[macro.name] = macro
        if (macro.name not in self.gcode.ready_gcode_handlers) and (macro.name not in self.gcode.base_gcode_handlers):
            self.gcode.register_command(macro.name.upper(), self.generate_cmd(macro), desc=macro.desc)

    def unregister_macro(self, macro):
        self.gcode.register_command(macro.name.upper(), None)
        if macro in self.macros:
            self.macros[macro.name] = None
            del self.macros[macro.name]
    
    def cmd_DYNAMIC_MACRO(self, gcmd):
        self._update_macros()
        macro = gcmd.get('MACRO', '')
        if not macro:
            return
        params = gcmd.get_command_parameters()
        rawparams = gcmd.get_raw_command_parameters()
        self._run_macro(self.macros.get(macro, self.placeholder), params, rawparams)
    
    
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
        desc = config.get(section, 'description') if config.has_option(section, 'description') else 'No Description'
        return DynamicMacro(name, raw, printer, desc=desc)
    
    def run(self, params, rawparams):
        kwparams = dict(self.variables)
        kwparams.update(self.template.create_template_context())
        kwparams['dynamic_printer'] = DynamicPrinter(self.printer)
        kwparams['params'] = params
        kwparams['rawparams'] = rawparams
        self.template.run_gcode_from_command(kwparams)

class DynamicPrinter:
    def __init__(self, _printer):
        self._printer = _printer
    
    def __getattribute__(self, name: str):
        return self._printer.__getattribute__(name)

    def __getitem__(self, item: str):
        return self._printer.__getitem__(item)
    
def load_config(config):
    return DynamicMacros(config)