from openspade.event.engine import EventEngine


class OpenSpadeEngineManager:
    def __init__(self):
        self.event_engine = EventEngine()
        self.main_engine = MainEngine(self.event_engine)
    def register_engine(self, name, engine):
        self.engines[name] = engine

    def get_engine(self, name):
        return self.engines.get(name)

    def list_engines(self):
        return list(self.engines.keys())
