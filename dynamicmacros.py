class DynamicMacros:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object('gcode')
        self.fnames = config.getlist('configs')
        
        self.gcode.register_command(
            'DYNAMIC_MACRO',
            self.cmd_DYNAMIC_MACRO
        )
    
    def cmd_DYNAMIC_MACRO(self, gcmd):
        params = gcmd.get_command_parameters()
        with open('/home/pi/params.txt', 'w+') as file:
            file.write(str(params) + '\n\n\n' + str(type(params)))
        gcmd.respond_info("Wrote to ~/params.txt")
    
def load_config(config):
    return DynamicMacros(config)