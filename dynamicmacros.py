import ast
import configparser
import glob
import json
import logging
import textwrap
import os
import re
import subprocess
from io import StringIO
from pathlib import Path
from secrets import token_hex

DYNAMICMACROS_PATH = Path.home() / 'DynamicMacros'

import jinja2

try:
    from .gcode_macro import TemplateWrapper  # Klipper
except:
    from .gcode_macro import TemplateWrapperJinja as TemplateWrapper  # Kalico

# Define the path to the configuration files
config_path = Path(os.path.expanduser('~')) / 'printer_data' / 'config'

logger = None

def clean_gcode(gcode):
    gcode = '\n' + gcode.strip() + '\n'
    gcode = re.sub(r'\n+', '\n', gcode)
    gcode = textwrap.indent(gcode, ' '*4)
    return gcode.strip()

class MacroConfigParser:
    def __init__(self, printer, delimiter):
        global config_path
        self.printer = printer
        self.delimiter = delimiter

        self.config_file = printer.start_args['config_file']
        self.config_path = Path(os.path.dirname(self.config_file))
        config_path = self.config_path

    def read_config_file(self, filename):
        buffer = self._read_file(filename)
        sbuffer = StringIO('\n'.join(buffer))
        config = configparser.RawConfigParser(
            strict=False, inline_comment_prefixes=(';', '#'))
        config.read_file(sbuffer, filename)
        return config

    def _read_file(self, filename, visited=[]):
        path = self.config_path / filename
        if not os.path.exists(path):
            raise MissingConfigError(f'Missing Configuration at {path}')
        if path in visited:
            raise RecursiveConfigError(f'Recursively included file at {path}')
        visited.append(path) # Keep a list of files previously included
        buffer = [] # List of lines in the file
        with open(path, 'r') as file:
            for line in file.readlines():
                mo = configparser.RawConfigParser.SECTCRE.match(line)
                header = mo and mo.group('header')
                # Handle [include xxx.cfg] sections
                if header and header.startswith('include '):
                    include_spec = header[8:].strip()
                    include_path = str(path.parent / include_spec)
                    include_filenames = glob.glob(include_path, recursive=True)
                    for filename in include_filenames:
                        buffer.extend(self._read_file(filename, visited))
                else:
                    buffer.append(line)
        visited.remove(path)
        return buffer

    def extract_macros(self, config):
        macros = {}
        for section in config.sections():
            logging.info(f'DynamicMacros: Reading section {section}')
            if section.startswith('gcode_macro') or \
                section.startswith('delayed_gcode'):
                macro = DynamicMacro.from_section(
                    config, section, DynamicMacros.printer, self.delimiter)
                macros[macro.name] = macro
        return macros

    def get_workaround_gcode(self, prev_gcode):
        lines = []
        for line in prev_gcode.splitlines():
            if '{% set ' in line and 'python' not in line:
                lines.append(line)
        compiled_gcode = '\n'.join(lines)
        return compiled_gcode

class MissingConfigError(Exception):
    pass

class RecursiveConfigError(Exception):
    pass

class DynamicMacros:
    clusters = {}

    def __init__(self, config):
        self._init(config)

    def _init(self, config, is_cluster=False):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object('gcode')
        self.fnames = config.getlist('configs')

        self.delimiter = config.get('delimiter', '---')

        if is_cluster:
            self.name = config.get_name().split()[1]
            DynamicMacros.clusters[self.name] = self
            self.python_enabled = config.getboolean('python_enabled', True)
            self.printer_enabled = config.getboolean('printer_enabled', True)
        else:
            self._setup_logging()
            DynamicMacros.printer = self.printer

            # Register commands
            self.gcode.register_command(
                'DYNAMIC_MACRO', self.cmd_DYNAMIC_MACRO, desc='Run a Dynamic Macro')
            self.gcode.register_command(
                'DYNAMIC_RENDER', self.cmd_DYNAMIC_RENDER, desc='Render a Dynamic Macro')
            self.gcode.register_command('SET_DYNAMIC_VARIABLE', self.cmd_SET_DYNAMIC_VARIABLE, desc="Set the variable of a Dynamic Macro.")

        self.macros = {}
        self.placeholder = DynamicMacro(
            'Error', 'RESPOND MSG="ERROR"', self.printer)

        self.configfile = self.printer.lookup_object('configfile')

        self.config_parser = MacroConfigParser(self.printer, self.delimiter)

        # Interface workaround
        # - Allows macros to display on KlipperScreen
        # - Allows macro parameters to display on all interfaces
        if config.getboolean('interface_workaround', True):
            self.interface_workaround()

        self._update_macros()

        self.reactor = self.printer.get_reactor()
        self.printer.register_event_handler(
            "klippy:ready", self._handle_ready)

    def _setup_logging(self):
        # Get git short version hash
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                check=True,
                cwd=DYNAMICMACROS_PATH
            )
            git_hash = result.stdout.strip()
        except subprocess.CalledProcessError:
            git_hash = 'unknown'

        # Setup logging
        if not globals().get('LOG_SETUP', False):
            logger = logging.Logger('DynamicMacros')
            klippy_log = self.printer.start_args['log_file']
            log_dir = os.path.dirname(klippy_log)
            mimo_log = os.path.join(log_dir, 'dynamicmacros.log')
            handler = logging.FileHandler(mimo_log, mode='w')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG)
            globals()['logging'] = logger
            globals()['LOG_SETUP'] = True
            logger.info('DynamicMacros Startup')
            logger.info(f'Git version: {git_hash}')

    def _handle_ready(self):
        self._update_macros()
        waketime = self.reactor.monotonic() + 1
        self.timer_handler = self.reactor.register_timer(
            self._gcode_timer_event, waketime)

    def _gcode_timer_event(self, eventtime):
        self._update_macros()
        return self.reactor.NEVER

    def interface_workaround(self):
        full_cfg = StringIO()
        for fname in self.fnames:
            cfg = self.config_parser.read_config_file(fname)
            for section in cfg.sections():
                if not section.startswith('gcode_macro'):
                    cfg.remove_section(section)
                    continue
                prev_gcode = cfg.get(section, 'gcode')
                compiled_gcode = self.config_parser.get_workaround_gcode(prev_gcode)
                if hasattr(self, 'name'):
                    cmd = f'DYNAMIC_MACRO MACRO={section.split()[1]} CLUSTER={self.name}' + ' {rawparams}'
                else:
                    cmd = f'DYNAMIC_MACRO MACRO={section.split()[1]}' + ' {rawparams}'
                cfg.set(section, 'gcode', f'{compiled_gcode}\n{cmd}')
            cfg.write(full_cfg)

        # Write cfg to config_path/.dynamicmacros.cfg
        with open(config_path / '.dynamicmacros.cfg', 'w+') as file:
            file.write(full_cfg.getvalue())

        # Update printer.cfg to [include .dynamicmacros.cfg]
        include_statement = '[include .dynamicmacros.cfg]'
        with open(config_path / 'printer.cfg', 'r') as file:
            lines = file.readlines()
            found = False
            for line in lines:
                if len(line.strip()) < 1:
                    # Ignore empty lines
                    continue
                if line.strip()[0] in ('#', ';', '//'):
                    # Ignore comments
                    continue
                if include_statement in line:
                    found = True
                    break
            if not found:
                lines.insert(0, include_statement+'\n')

        with open(config_path / 'printer.cfg', 'w+') as file:
            file.writelines(lines)

    def register_macro(self, macro):
        self.macros[macro.name.upper()] = macro
        if (macro.name not in self.gcode.ready_gcode_handlers) and (macro.name not in self.gcode.base_gcode_handlers):
            _ = self.gcode.register_command(macro.name.upper(), None, desc=macro.desc)
            self.gcode.register_command(
                macro.name.upper(), self.generate_cmd(macro), desc=macro.desc)
            if macro.is_delayed_gcode:
                prev = self.gcode.mux_commands.get('UPDATE_DELAYED_GCODE')
                if prev is not None:
                    prev_key, prev_values = prev
                    prev_values[macro.name] = None
                    del prev_values[macro.name]
                self.gcode.register_mux_command(
                    'UPDATE_DELAYED_GCODE', 'ID', macro.name, macro.cmd_UPDATE_DELAYED_GCODE)
            self.gcode._build_status_commands()
            self.printer.objects[f'gcode_macro {macro.name}'] = macro
            # self.configfile.status_raw_config[f'gcode_macro {macro.name}'] = macro.get_status()
            original_get_status = self.configfile.get_status
            def get_status(eventtime):
                status = original_get_status(eventtime)
                config = status['config']
                workaround_gcode = self.config_parser.get_workaround_gcode(macro.raw)
                config.update({f'gcode_macro {macro.name}': {'gcode': workaround_gcode}})
                status.update({'config': config})
                return status
            self.configfile.get_status = get_status

    def cmd_SET_DYNAMIC_VARIABLE(self, gcmd):
        macro = gcmd.get('MACRO').upper()
        if macro not in self.macros:
            for name, cluster in self.clusters.items():
                if macro in cluster.macros:
                    return cluster._cmd_SET_DYNAMIC_VARIABLE(gcmd)
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
            else:
                self.gcode.respond_info(f'ERROR: Macro {name} not found!')

    def unregister_macro(self, macro):
        macro.repeat = False
        self.gcode.register_command(macro.name.upper(), None)
        if macro.is_delayed_gcode:
            _, vals = self.gcode.mux_commands.get('UPDATE_DELAYED_GCODE')
            if macro.name in vals:
                del vals[macro.name]
        self.gcode._build_status_commands()
        self.macros.pop(macro.name.upper(), None)

    def cmd_DYNAMIC_RENDER(self, gcmd):
        cluster = gcmd.get('CLUSTER', None)
        if cluster and cluster in self.clusters:
            return self.clusters[cluster]._cmd_DYNAMIC_RENDER(gcmd)
        return self._cmd_DYNAMIC_RENDER(gcmd)

    def _cmd_DYNAMIC_RENDER(self, gcmd):
        try:
            # self._update_macros()
            logging.info('DynamicMacros Macros:')
            for name in self.macros:
                logging.info(f'    Name: {name}')
            macro_name = gcmd.get('MACRO', '').upper()
            if macro_name:
                params = gcmd.get_command_parameters()
                rawparams = gcmd.get_raw_command_parameters()
                macro = self.macros.get(macro_name, self.placeholder)
                rendered = self._render_macro(macro, params, rawparams)
                rendered = re.sub(r'\n+', '\n', rendered)
                gcmd.respond_info(f'Rendered {macro.name}:\n\n{rendered}')
        except Exception as e:
            gcmd.respond_info(str(e))

    def _render_macro(self, macro, params, rawparams):
        rendered = []
        for template in macro.templates:
            macro.update_kwparams(template, params, rawparams)
            rendered.append(template.template.render(macro.kwparams))
        return '\n'.join(rendered)

    def cmd_DYNAMIC_MACRO(self, gcmd):
        cluster_name = gcmd.get('CLUSTER', None)
        if cluster_name and cluster_name in self.clusters:
            cluster = self.clusters[cluster_name]
            return cluster._cmd_DYNAMIC_MACRO(gcmd)
        return self._cmd_DYNAMIC_MACRO(gcmd)

    def _cmd_DYNAMIC_MACRO(self, gcmd):
        try:
            self._update_macros()
            logging.info('DynamicMacros Macros:')
            for name in self.macros:
                logging.info(f'    Name: {name}')
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
        self._init(config, is_cluster=True)

    def disabled_func(self, name, msg):
        def func(*args, **kwargs):
            self.gcode.respond_info(
                f'WARNING: {name} attempted to {msg} when disabled.')
            self.gcode.respond_info(
                f'{name} has been blocked from performing a disabled task.')
        return func

    def sandboxed_kwparams(self, macro):
        def func(template, params, rawparams):
            macro._update_kwparams(template, params, rawparams)
            if not self.python_enabled:
                macro.kwparams['python'] = self.disabled_func(
                    macro.name, 'run Python code')
                macro.kwparams['python_file'] = self.disabled_func(
                    macro.name, 'run Python file')
            if not self.printer_enabled:
                macro.kwparams['printer'] = None
        return func

    def _run_macro(self, macro, params, rawparams):
        macro.update_kwparams = self.sandboxed_kwparams(macro)
        macro.run(params, rawparams)


class DynamicMacro:
    def __init__(self,
                name,
                raw,
                printer,
                desc='',
                variables={},
                delimiter='---',
                rename_existing=None,
                initial_duration=None,
                repeat=False,
                is_delayed_gcode=False):
        self.name = name
        self.raw = raw
        self.printer = printer
        self.gcode = self.printer.lookup_object('gcode')
        self.desc = desc
        self.variables = variables
        self.delimiter = delimiter if delimiter != 'NO_DELIMITER' else None
        self.rename_existing = rename_existing
        self.duration = initial_duration
        self.repeat = repeat
        self.vars = {}

        self.is_delayed_gcode = is_delayed_gcode

        if self.duration:
            self.reactor = self.printer.get_reactor()
            self.timer_handler = None
            self.inside_timer = self.repeat
            self.printer.register_event_handler(
                "klippy:ready", self._handle_ready)

        if self.rename_existing:
            self.rename()

        if self.delimiter:
            self.gcodes = self.raw.split(self.delimiter)
        else:
            self.gcodes = [self.raw]
        self.templates = [self.generate_template(
            gcode) for gcode in self.gcodes]

    def _handle_ready(self):
        waketime = self.reactor.NEVER
        if self.duration:
            waketime = self.reactor.monotonic() + self.duration
        self.timer_handler = self.reactor.register_timer(
            self._gcode_timer_event, waketime)

    def _gcode_timer_event(self, eventtime):
        self.inside_timer = True
        try:
            self.run({}, '')
        except Exception:
            pass
        nextwake = self.reactor.NEVER
        if self.repeat:
            nextwake = eventtime + self.duration
        self.inside_timer = False
        return nextwake

    def generate_template(self, gcode):
        env = jinja2.Environment('{%', '%}', '{', '}')
        logging.info(f'DynamicMacros [{self.name}]: \n{clean_gcode(gcode)}')
        return TemplateWrapper(self.printer, env, self.name, gcode)

    def rename(self):
        prev_cmd = self.gcode.register_command(self.name, None)
        if prev_cmd:
            self.gcode.register_command(
                self.rename_existing, prev_cmd, desc=f'Renamed from {self.name}')

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
        python_vars = {**self.kwparams, 'output': output,
                       'gcode': self.gcode.run_script_from_command, 'printer': self.printer}
        python_vars['print'] = lambda *args: self.gcode.run_script_from_command(
            'RESPOND MSG="' + ' '.join(map(str, args)) + '"')
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
            self.gcode.respond_info(f'Python file missing: {config_path / fname}')
            return
        return self.python(text, *args, **kwargs)

    @staticmethod
    def from_section(config, section, printer, delimiter):
        raw = config.get(section, 'gcode')
        raw = clean_gcode(raw)

        name = section.split()[1]
        # logging.info(f'DynamicMacros [{name}] Raw:\n{raw}')

        desc = config.get(section, 'description', fallback='No Description')
        rename_existing = config.get(section, 'rename_existing', fallback=None)

        initial_duration = config.getfloat(
            section, 'initial_duration', fallback=None)
        repeat = config.getboolean(section, 'repeat', fallback=False)
        is_delayed_gcode = 'delayed_gcode' in section

        variables = {key[len('variable_'):]: value for key, value in config.items(
            section) if key.startswith('variable_')}
        for k, v in variables.items():
            try:
                variables[k] = ast.literal_eval(v)
            except:
                pass

        return DynamicMacro(name,
                            raw,
                            printer,
                            desc=desc,
                            variables=variables,
                            delimiter=delimiter,
                            rename_existing=rename_existing,
                            initial_duration=initial_duration,
                            repeat=repeat,
                            is_delayed_gcode=is_delayed_gcode)

    def get_status(self, eventtime=None):
        return self.variables

    def _update_kwparams(self, template, params, rawparams):
        kwparams = {**self.variables, **self.vars,
                    **template.create_template_context()}
        kwparams.update({'params': params, 'rawparams': rawparams, 'update': self.update, 'get_macro_variables': self.get_macro_variables,
                        'update_from_dict': self.update_from_dict, 'python': self.python, 'python_file': self.python_file})
        self.kwparams = kwparams

    def update_kwparams(self, template, params, rawparams):
        self._update_kwparams(template, params, rawparams)

    def run(self, params, rawparams):
        for template in self.templates:
            self._run(template, params, rawparams)

    def _run(self, template, params, rawparams):
        self.update_kwparams(template, params, rawparams)
        template.run_gcode_from_command(self.kwparams)

    # Handle UPDATE_DELAYED_GCODE command
    def cmd_UPDATE_DELAYED_GCODE(self, gcmd):
        if not self.is_delayed_gcode:
            raise gcmd.error('Not a [delayed_gcode]!')
        self.duration = gcmd.get_float('DURATION', minval=0)
        if self.inside_timer:
            self.repeat = (self.duration != 0.)
        else:
            waketime = self.reactor.NEVER
            if self.duration:
                waketime = self.reactor.monotonic() + self.duration
            self.reactor.update_timer(self.timer_handler, waketime)

def load_config(config):
    return DynamicMacros(config)


def load_config_prefix(config):
    return DynamicMacrosCluster(config)