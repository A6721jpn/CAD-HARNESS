"""VERIFY v3 only: one suite clock and independent generation/parse/repair slots."""
import math
import time
from datetime import datetime, timezone
from pathlib import Path

if __package__:
    from .cad_verify_guard import Guard as V1Guard, Stop, Fault, q_score, quota_snapshot
else:
    from cad_verify_guard import Guard as V1Guard, Stop, Fault, q_score, quota_snapshot


class Guard(V1Guard):
    def __init__(self, snapshot, seconds=10800, call_budget=163, clock=None, now=None, check_versions=None):
        if seconds != 10800 or type(call_budget) is not int or not 1 <= call_budget <= 163:
            raise ValueError("verify_v3_guard_contract")
        self.clock = clock or time.monotonic
        self.now = now or (lambda: datetime.now(timezone.utc))
        self.started = self.clock()
        self.deadline = self.started+seconds
        self.snapshot = Path(snapshot)
        self.call_budget, self.calls = call_budget, 0
        self.snapshots = []
        self.check_versions = check_versions or (lambda: None)

    def inherit(self,document,*,no_deadline=False):
        started,deadline=document['started_monotonic'],document['deadline_monotonic']
        calls=document['real_calls'];cap=document['call_budget']
        if (type(started) not in (int,float) or type(deadline) not in (int,float) or not math.isfinite(started) or not math.isfinite(deadline)
                or abs((deadline-started)-10800)>1e-6 or type(calls) is not int
                or cap!=163 or not 0<=calls<=cap or self.clock()<started):raise Stop('resume_clock_or_cap_binding')
        self.started,self.deadline,self.calls,self.call_budget=started,None if no_deadline else deadline,calls,cap
        self.remaining()

    def remaining(self, reserve=30):
        if self.deadline is None:return math.inf
        return super().remaining(reserve)

    def before_episode(self, maximum_calls):
        self.before_run(maximum_calls)
        if self.deadline is not None and self.deadline-self.clock() < 960:
            raise Stop("shared_deadline_insufficient_episode_reserve")


class Budget:
    def __init__(self, max_calls, clock=None, preview=False):
        if type(max_calls) is not int or not 1 <= max_calls <= 4:
            raise ValueError("verify_v3_episode_contract")
        self.clock = clock or time.monotonic
        self.started = self.clock()
        self.deadline = self.started+900
        self.stage_deadline = self.started+450
        self.stage = "initial"
        self.max_calls, self.preview = max_calls, preview
        self.calls = self.attempts = 0
        self.counts = {purpose: 0 for purpose in ("question", "interpretation", "source", "parse_repair", "repair")}
        self.generation_closed = False

    def remaining(self, reserve=30):
        left = min(self.deadline, self.stage_deadline)-self.clock()-reserve
        if left <= 0:
            raise Stop("episode_stage_deadline_exceeded")
        return left

    def check_call(self, purpose):
        self.remaining()
        if self.calls >= self.max_calls:
            raise Stop("episode_call_limit")
        if purpose not in self.counts or self.counts[purpose] >= 1:
            raise ValueError("parse_limit" if purpose == "parse_repair" else "stage_call_limit")
        if purpose == "parse_repair" and self.preview:
            raise ValueError("preview_parse_disabled")
        if purpose in ("interpretation", "source", "question") and self.generation_closed:
            raise ValueError("generation_closed")
        if purpose == "repair" and (self.stage != "repair" or self.preview):
            raise ValueError("repair_not_eligible")

    def call(self, purpose):
        self.check_call(purpose)
        self.counts[purpose] += 1
        self.calls += 1

    def cad(self):
        self.remaining()
        if self.preview or self.attempts >= 2:
            raise ValueError("cad_attempt_limit")
        self.generation_closed = True
        self.attempts += 1

    def begin_repair(self):
        if self.attempts != 1 or self.counts["repair"] or self.preview:
            raise ValueError("repair_not_eligible")
        if self.deadline-self.clock() < 450:
            raise Stop("repair_time_reservation_lost")
        self.stage = "repair"
        self.stage_deadline = min(self.deadline, self.clock()+450)

    def sol_timeout(self, purpose):
        cap = 180 if purpose == "repair" else 60 if purpose == "parse_repair" else 450
        # The R slot cannot consume the unused P/build/reimport/cleanup slots.
        reserve=30
        if self.stage=='repair':reserve=210+(60 if purpose=='repair' and not self.counts['parse_repair'] else 0)
        return min(cap, self.remaining(reserve))

    def cad_timeout(self):
        return min(90 if self.stage == "repair" else 300, self.remaining(120 if self.stage=='repair' else 30))

    def settings(self):
        return dict(max_calls=self.max_calls, max_cad_attempts=0 if self.preview else 2, parse_calls=0 if self.preview else 1,
                    repair_calls=0 if self.preview else 1, deadline_s=900, initial_s=450, repair_s=450,
                    cleanup_reserve_s=30, repair_sol_s=180, repair_parse_s=60,
                    repair_cad_s=90, repair_reimport_s=90)
