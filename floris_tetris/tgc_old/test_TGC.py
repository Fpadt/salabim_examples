# Car.py
import salabim as sim


class Car(sim.Component):
    def setup(self, dur):
        self.prd = [5, 3, 5]
        self.prw = [4, 7, 1]
        self.dur = dur
        self._cap = 0
        self.mon = sim.Monitor(name="EV", level=False, type="float")

    @property
    def cap(self):
        return self._cap

    @cap.setter
    def cap(self, value):
        lic.append(value)
        self._cap += value
        self.mon.tally(value)

    def process(self):
        # while True:
        self.hold(self.dur, priority=2)
        # self.passivate()


class TGC(sim.Component):
    def process(self):
        t = None
        i = -1
        while EV1.isscheduled() or EV2.isscheduled():
            if EV1.isscheduled() and t is not None:
                EV1.cap = 7 * (env.now() - t)
            if EV2.isscheduled() and t is not None:
                EV2.cap = 5 * (env.now() - t)
            t = env.now()
            i += 1
            D1 = EV1.scheduled_time() - env.now()
            D2 = EV2.scheduled_time() - env.now()
            
            # print(f"old hold {min(EV1.prd[i], EV2.prd[i])}")
            # print(f"new hold {min(D1,D2)}")
            self.hold(max(min(D1, D2),1), urgent=True)


lic = []

env = sim.Environment(trace=False)

TGC()
EV1 = Car(dur=10)
EV2 = Car(dur=7)

env.run()

# -----------------  Results  -----------------
print(f"Environment end time: {env.now()}")
print(f"lid: {lic}")

print(EV1.mon.as_dataframe())
print(EV1.cap)
# EV1.mon.print_histogram()

print(EV2.mon.as_dataframe())
print(EV2.cap)
# EV2.mon.print_histogram()
