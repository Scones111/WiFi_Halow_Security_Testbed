
import time
import pandas as pd

class EventHandler:
    def __init__(self):
        self.start = time.time()
        self.events = pd.DataFrame(columns=["timestamp", "event_type", "details"])
        self.end = 0.0

    def log_event(self, event_type, details):
        print(self.events)
        timestamp = time.time() - self.start
        new_event = {"timestamp": timestamp, "event_type": event_type, "details": details}
        temp_pd = pd.DataFrame([new_event])
        self.events = pd.concat([self.events,temp_pd], ignore_index=True)

    def write_log_csv(self, filename):
        self.events.to_csv(filename, index=False)

    def write_log_json(self, filename):
        self.events.to_json(filename, orient="records", lines=True)

    def end_log(self):
        self.end = time.time()

test = EventHandler()

test.log_event("t","t")