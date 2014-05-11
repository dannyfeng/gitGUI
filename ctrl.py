from cmdfactory import CommandFactory
from decorators import memoize

class Controller(object):
    def __init__(self, model): #, view):
        self.model = model
        #self.view = view
        self.commands = {}
        self.factory = CommandFactory(model)

    def add_command(self, signal, handler=None):
        if handler is None:
            handler = self.do_wrapper(signal)
        #self.view.connect(self.view, SIGNAL(signal), handler)

    def add_commands(self, command_directory, handler=None):
        for signal, cmdclass in command_directory.items():
            self.factory.add_command(signal, cmdclass)
            self.add_command(signal, handler=handler)

    def add_global_command(self, signal):
        #self.view.connect(self.view, SIGNAL(signal), SLOT(signal))
        pass

    def do_wrapper(self, signal):
        def do(*args, **opts):
            return self.factory.do(signal, *args, **opts)
        return do

        
@memoize
def instance(model):
    """Return the Git singleton"""
    print 'controller'
    return Controller(model)


#controller = instance()

