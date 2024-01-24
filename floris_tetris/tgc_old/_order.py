# ------------------------------------------------------------------------
# packages and coding import
# ------------------------------------------------------------------------

from salabim import *
from config import *
from tgc_floris_padt.tgcsim.models._ev_charge_profile import *
from tgc_floris_padt.tgcsim.models._olp_abstract_model import *
from energy_price import *

# --------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------

class EV(Component):
    def setup(self, stay, soc, d_c, cap, ev_mpi, k):
        self.stay = stay  # stay time
        self.soc = soc  # state of charge
        self.d_c = d_c  # desired charge
        self.cap = cap  # capacity
        self.mpi = ev_mpi  # max power input
        self.k = k  # degradation cost
        # ----------------------------------
        self.toa = None  # time of arrival
        self.tod = None  # estimated time of departure
        self.tcb = None  # time of charge begin
        self.dc = d_c * cap  # desired charge in kWh
        self.ckwh = 0  # final charge in kWh
        # ----------------------------------
        self.m_stay = Monitor(name="stay", level=False)
        self.m_kwh = Monitor(name="kwh", level=False)

    def process(self):
        self.enter(waitingline)
        for evse in HUB:
            if evse.ispassive():
                evse.activate()
                break
        self.passivate()
        # self.register(EVS)


class EVSE(Component):
    def setup(self, se_mpo):
        self.mpo = se_mpo  # max power output
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
                  dc: {round(evse.ev.dc)} - ckwh: {round(evse.ev.ckwh)} - \
                  rem: {evse.remaining_duration()} sch: {evse.scheduled_time()}"
            )

    def assign_power(self):
        # self.request((ENX,0))
        # self.release(ENX)
        remaining_power = EX_MPO
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

# --------------------------------------------------------------------------
# Simulation
# --------------------------------------------------------------------------
            
env = Environment()

PRIO = "tod"  # FIFO = toa, LIFO = -toa, EDD = tod, LL = <to_e_developed>

ENX = env.Resource("ENX", capacity=EX_MPO, anonymous=False)
HUB = [EVSE(se_mpo = SE_MPO) for _ in range(3)]
EVS = [
    EV(
        stay=np.random.uniform(dur_l, dur_h),
        soc=np.random.uniform(soc_l, soc_h),
        d_c=np.random.uniform(d_c_l, d_c_h),
        cap=CAP,
        ev_mpi=EV_MPI,
        k=K,
    )
    for _ in range(m)
]


TGC(name="TGC")

waitingline = Queue("waitingline")
env.run()

# --------------------------------------------------------------------------
# Reporting Results
# --------------------------------------------------------------------------

for ev in EVS:
    print(
        f"""\
{ev.name()}\t\
stay: {round(ev.stay, 2)}\t\
dc: {round(ev.dc, 2)}\t\
ckwh: {round(ev.ckwh, 2)}\t\
toa: {round(ev.toa, 2)}\t\
tod: {round(ev.tod, 2)}"""
    )
