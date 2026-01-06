class SimulationClock:
    def __init__(self, start_time: int):
        self.current_time = start_time

    def advance_to(self, timestamp: int):
        self.current_time = timestamp

    def advance_by(self, seconds: int):
        self.current_time += seconds

