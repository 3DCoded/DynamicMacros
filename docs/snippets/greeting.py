# --8<-- [start:code]
# --8<-- [start:cls]
# --8<-- [start:clsheader]
class Greeting:
# --8<-- [end:clsheader]
    # --8<-- [start:init]
    # --8<-- [start:initheader]
    def __init__(self, config):
    # --8<-- [end:initheader]
        # --8<-- [start:readcfg]
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.gcode = self.printer.lookup_object('gcode')
        self.name = config.get_name().split()[1]

        self.message = config.get('message', 'Welcome to Klipper!')
        self.delay = config.getint('delay', 0)
        # --8<-- [end:readcfg]

        # --8<-- [start:regcmd]
        self.gcode.register_mux_command(
            'GREETING',
            'NAME',
            self.name,
            self.cmd_GREETING,
            desc=self.cmd_GREETING_help
        )
        
        if self.delay > 0:
            self.printer.register_event_handler(
            'klippy:ready', self._ready_handler)
        # --8<-- [end:regcmd]
    # --8<-- [end:init]

    # --8<-- [start:handler]
    def _ready_handler(self):
        waketime = self.reactor.monotonic() + self.delay
        self.reactor.register_timer(self._greet, waketime)
    # --8<-- [end:handler]

    # --8<-- [start:agreet]
    def _greet(self, eventtime=None):
        self.gcode.respond_info(self.message)
        return self.reactor.NEVER
    # --8<-- [end:agreet]

    # --8<-- [start:greet]
    cmd_GREETING_help = "Greet the user"
    def cmd_GREETING(self, gcmd):
        self._greet()
    # --8<-- [end:greet]
# --8<-- [end:cls]

# --8<-- [start:loadcfg]
def load_config_prefix(config):
    return Greeting(config)
# --8<-- [end:loadcfg]
# --8<-- [end:code]