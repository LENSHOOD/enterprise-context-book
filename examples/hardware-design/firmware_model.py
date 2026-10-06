"""Host-only W2 behavior model; no MCU, drivers, flash or radio is simulated."""

from copy import deepcopy
import math


def positive_int(value, name, limit=1_000_000_000):
    if type(value) is not int or not 0 < value <= limit:
        raise ValueError(f"{name}: expected a positive integer <= {limit}")
    return value


def policy_values(policy):
    if not isinstance(policy, dict):
        raise ValueError("firmware policy must be a record")
    capacity = positive_int(policy.get("queue_capacity"), "queue capacity", 4096)
    delays = policy.get("retry_delays_s")
    if not isinstance(delays, list) or not 1 <= len(delays) <= 8:
        raise ValueError("retry delays must contain 1 to 8 entries")
    return capacity, tuple(positive_int(x, "retry delay", 86400) for x in delays)


class MemoryJournal:
    """Atomic old-or-new commits are a test assumption, not a flash implementation."""

    def __init__(self, device_id="W2-TEACHING-01"):
        if not isinstance(device_id, str) or not device_id.strip():
            raise ValueError("device ID required")
        self.device_id = device_id
        self.next_sequence = 1
        self._records = []
        self.fail_next_write = False

    @property
    def records(self):
        return deepcopy(self._records)

    def _commit(self, records, next_sequence):
        if self.fail_next_write:
            self.fail_next_write = False
            raise OSError("injected journal write failure")
        self._records, self.next_sequence = deepcopy(records), next_sequence

    def append(self, time_s, reading):
        record = {"device": self.device_id, "sequence": self.next_sequence,
                  "time_s": time_s, "temperature_c": reading[0], "humidity_pct": reading[1]}
        self._commit(self._records + [record], self.next_sequence + 1)

    def acknowledge(self, batch):
        if not batch or self._records[:len(batch)] != batch:
            raise ValueError("acknowledgement does not match journal prefix")
        self._commit(self._records[len(batch):], self.next_sequence)


class Receiver:
    """Synchronous test transport: a call represents a completed bounded attempt."""

    def __init__(self, outcomes=(), default="ack"):
        allowed = {"ack", "offline", "lost_ack", "wrong_ack"}
        if default not in allowed or any(x not in allowed for x in outcomes):
            raise ValueError("unknown transport outcome")
        self.outcomes = list(outcomes)
        self.default = default
        self.received = {}
        self.attempts = 0
        self.duplicates = 0

    def send(self, batch):
        self.attempts += 1
        outcome = self.outcomes.pop(0) if self.outcomes else self.default
        if outcome == "offline":
            return None
        for record in batch:
            key = (record["device"], record["sequence"])
            if key in self.received:
                if self.received[key] != record:
                    raise ValueError("same record identity has different content")
                self.duplicates += 1
            self.received[key] = deepcopy(record)
        if outcome == "lost_ack":
            return None
        if outcome == "wrong_ack":
            return ("OTHER-DEVICE", batch[-1]["sequence"])
        return (batch[-1]["device"], batch[-1]["sequence"])


class Device:
    """Single-owner event loop; time is an unbounded integer host clock in seconds."""

    def __init__(self, journal, sensor, transport, sample_period_s, upload_period_s,
                 policy, start_s=0):
        self.sample_period = positive_int(sample_period_s, "sample period")
        self.upload_period = positive_int(upload_period_s, "upload period")
        self.capacity, self.delays = policy_values(policy)
        if type(start_s) is not int or start_s < 0:
            raise ValueError("start time must be a nonnegative integer")
        self.journal, self.sensor, self.transport = journal, sensor, transport
        self.last_time = start_s
        self.next_sample = start_s + self.sample_period
        self.next_upload = start_s if journal.records else start_s + self.upload_period
        self.retry_at = None
        self.batch = []
        self.attempts_in_window = 0
        self.sensor_errors = self.queue_full_events = self.missed_samples = 0
        self.sampling_opportunities = self.samples_committed = 0
        self.events = []  # Host test trace, not a proposed MCU log buffer.

    def tick(self, now):
        if type(now) is not int or now < self.last_time:
            raise ValueError("clock must be an integer and cannot move backwards")
        self.last_time = now
        if now >= self.next_sample:
            missed = (now - self.next_sample) // self.sample_period
            self.missed_samples += missed
            self.sampling_opportunities += missed + 1
            self.next_sample += (missed + 1) * self.sample_period
            if len(self.journal.records) >= self.capacity:
                self.queue_full_events += 1
                self.events.append((now, "queue_full"))
            else:
                try:
                    reading = self.sensor(now)
                except OSError:
                    reading = None
                try:
                    valid = (isinstance(reading, (tuple, list)) and len(reading) == 2
                             and all(type(x) in (int, float) and math.isfinite(x) for x in reading))
                except OverflowError:
                    valid = False
                if not valid:
                    self.sensor_errors += 1
                    self.events.append((now, "sensor_error"))
                else:
                    self.journal.append(now, reading)
                    self.samples_committed += 1
                    self.events.append((now, "sample_committed"))

        due = False
        if now >= self.next_upload:
            self.next_upload += ((now - self.next_upload) // self.upload_period + 1) * self.upload_period
            self.attempts_in_window = 0
            self.retry_at = None
            self.batch = self.journal.records
            due = bool(self.batch)
        elif self.retry_at is not None and now >= self.retry_at:
            due = True
        if due:
            self.attempts_in_window += 1
            self.retry_at = None
            ack = self.transport.send(deepcopy(self.batch))
            expected = (self.journal.device_id, self.batch[-1]["sequence"])
            if ack == expected:
                self.journal.acknowledge(self.batch)
                self.batch = []
                self.events.append((now, "batch_acknowledged"))
            else:
                self.events.append((now, "unconfirmed_attempt"))
                if self.attempts_in_window <= len(self.delays):
                    self.retry_at = now + self.delays[self.attempts_in_window - 1]

    def next_wakeup(self):
        deadlines = [self.next_sample, self.next_upload]
        if self.retry_at is not None:
            deadlines.append(self.retry_at)
        return min(deadlines)
