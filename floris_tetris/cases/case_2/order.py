from salabim import *


class EV(Component):
    def setup(self, stay, dkwh):
        self.stay = stay  # stay time
        self.toa = None  # time of arrival
        self.tod = None  # estimated time of departure
        self.tcb = None  # time of charge begin
        self.dkwh = dkwh  # desired charge in kWh
        self.ckwh = 0  # final charge in kWh
        self.mpi = 7.36  # max power input
        self.m_stay = Monitor(name="stay", level=False)
        self.m_kwh = Monitor(name="kwh", level=False)

    def process(self):
        self.enter(waitingline)
        for evse in HUB:
            if evse.ispassive():
                evse.activate()
                break
        self.passivate()
        self.register(EVS)


class EVSE(Component):
    def setup(self):
        self.mpo = 7.36  # max power output
        self.ev = None  # assigned EV
        self.pwr = 0  # negotiated charging power

    def process(self):
        while True:
            while len(waitingline) == 0:
                self.passivate()
            self.ev = waitingline.pop()
            self.ev.tcb = env.now()
            self.ev.toa = env.now()
            self.ev.tod = self.ev.toa + self.ev.stay
            # charge
            self.hold(self.ev.stay)

            # statistics
            self.ev.m_stay.tally(self.ev.stay)
            self.ev.m_kwh.tally(self.ev.ckwh)

            self.ev.activate()
            self.ev = None


class TGC(Component):
    def setup(self):
        self.schedule = env.Queue("SCHEDULE")

    def make_schedule(self, property_name):
        # new schedule
        self.schedule.clear()
        # sort and reverse sort
        reverse = 1
        if property_name[0] == "-":
            reverse = -1
            property_name = property_name[1:]

        for evse in HUB:
            if evse.ev is not None:
                property_value = reverse * getattr(evse.ev, property_name)
                self.schedule.add_sorted(evse, property_value)

        return self.schedule

    def print_state(self, evse):
        if evse.ev is None:
            print(f"{env.now()}\t - NO_EV/{evse.name()} ")
        else:
            #   toa: {evse.ev.toa} - tod: {evse.ev.tod} -  \
            print(
                f"{env.now()}\t - {evse.ev.name()}/{evse.name()} - pwr: {evse.pwr}\
                  dkwh: {round(evse.ev.dkwh)} - ckwh: {round(evse.ev.ckwh)} - \
                  rem: {evse.remaining_duration()} sch: {evse.scheduled_time()}"
            )

    def assign_power(self):
        # self.request((enx,0))
        # self.release(enx)
        remaining_power = ENX_MPO
        order = self.make_schedule(PRIO)
        # order.print_info()
        while len(order) > 0:
            evse = order.pop()
            evse.ev.ckwh += evse.pwr * (env.now() - evse.ev.tcb)
            evse.ev.tcb = env.now()
            evse.pwr = min([evse.mpo, evse.ev.mpi, remaining_power])

            remaining_power -= evse.pwr

    def process(self):
        while True:
            self.assign_power()
            [self.print_state(x) for x in HUB]

            self.standby()


env = Environment()

ENX_MPO = 3 * 7.36
PRIO = "tod"  # FIFO = toa, LIFO = -toa, EDD = tod, LL = <to_e_developed>
enx = env.Resource("enx", capacity=ENX_MPO, anonymous=False)

HUB = [EVSE() for _ in range(3)]

EV1 = EV(stay=40, dkwh=294.4)
EV2 = EV(stay=50, dkwh=294.4)
EV3 = EV(stay=70, dkwh=294.4)
TGC(name="TGC")

EVS = [] # list of all EVs after simulation

waitingline = Queue("waitingline")
env.run()

for ev in EVS:
    print(
        f"{ev.name()} - dkwh: {ev.dkwh} - ckwh: {ev.ckwh} - toa: {ev.toa} - tod: {ev.tod}"
    )

