class BasePlugin:
    """
    Base interface for attachable memory/hardware plugins.
    """
    name = "Base Plugin"
    
    def __init__(self, app):
        self.app = app
        
    def start(self):
        pass
        
    def stop(self):
        pass
        
    def on_reset(self):
        pass
