# --8<-- [start:code]
# --8<-- [start:cls]
# --8<-- [start:clsheader]
class Greeter:
# --8<-- [end:clsheader]
    # --8<-- [start:init]
    # --8<-- [start:initheader]
    def __init__(self, config):
    # --8<-- [end:initheader]
        # --8<-- [start:readcfg]
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.gcode = self.printer.lookup_object('gcode')

        self.message = config.get('message', 'Welcome to Klipper!')
        # --8<-- [end:readcfg]

        # --8<-- [start:regcmd]
        self.gcode.register_command(
            'GREET', self.cmd_GREET, desc=self.cmd_GREET_help)
        self.printer.register_event_handler(
            'klippy:ready', self._ready_handler)
        # --8<-- [end:regcmd]
    # --8<-- [end:init]

    # --8<-- [start:handler]
    def _ready_handler(self):
        waketime = self.reactor.monotonic() + 1
        self.reactor.register_timer(self._greet, waketime)
    # --8<-- [end:handler]

    # --8<-- [start:agreet]
    def _greet(self, eventtime=None):
        self.gcode.respond_info(self.message)
        return self.reactor.NEVER
    # --8<-- [end:agreet]

    # --8<-- [start:greet]
    cmd_GREET_help = "Greet the user"
    def cmd_GREET(self, gcmd):
        self._greet()
    # --8<-- [end:greet]
# --8<-- [end:cls]

# --8<-- [start:loadcfg]
def load_config(config):
    return Greeter(config)
# --8<-- [end:loadcfg]
# --8<-- [end:code]