from salabim import *


class EV(Component):
    def setup(self, dur, dsc, mpi):
        # --- Constants ---
        self.mpi = mpi  #    max power input
        # --- Variables ---
        self.dur = dur  #    duration of stay
        self.toa = None  #   time of arrival
        self.tod = None  #   time of departure (estimated)
        self.tcb = None  #   time of charge begin
        self.dsc = dsc  #    desired state of charge in kWh
        self.csc = 0  #      current state f charge
        # --- Monitors ---
        self.mon_kwh = Monitor(name="EV kWh", level=True)
        self.mon_dur = Monitor(name="EV Dur", level=False)

    def process(self):
        # enter the waiting line
        self.enter(waitingline)
        # check if any EVSE is available
        for evse in HUB:
            if evse.ispassive():
                evse.activate()
                break
        self.passivate()
        self.mon_kwh.tally(0)        
        # register EV in list for Reporting
        self.register(EVS)


class EVSE(Component):
    def setup(self, mpo):
        # --- Constants ---
        self.mpo = mpo  #    max power output
        # --- Variables ---
        # self.tcs = None  #   time of charge start
        # self.pcs = None  #   power at charge start
        self.pwr = 0  #      charging power
        # self.kwh = 0  #      kWh delivered
        # --- Objects ---
        self.ev = None  #    EV being charged
        # --- Monitors ---
        self.mon_kwh = Monitor(name="SE kWh", level=True)


    def update_energy_charged(self):
        self.mon_kwh.tally(self.pwr)
        self.ev.mon_kwh.tally(self.pwr)


    def process(self):
        while True:
            # wait for EV to arrive
            while len(waitingline) == 0:
                self.passivate()
            # assign EV
            self.ev = waitingline.pop()
            # charge EV
            self.hold(self.ev.dur)

            # update statistics
            self.update_energy_charged()
            self.ev.mon_dur.tally(self.ev.dur)
            self.mon_kwh.tally(0)
            # release EV
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
            j = None
            # print(f"{env.now()}\t - NO_EV/{evse.name()} ")
        else:
            #   toa: {evse.ev.toa} - tod: {evse.ev.tod} -  \
            print(
                f"""{env.now()}\t{evse.ev.name()}/{evse.name()}\tcsc: {evse.ev.csc}"""
                # \tpwr: {evse.pwr}\tdsc: {round(evse.ev.dsc)}  rem: {evse.remaining_duration()}\tsch: {evse.scheduled_time()}"""
            )

    def assign_power(self):
        # self.request((enx,0))
        # self.release(enx)
        remaining_power = ENX_MPO
        order = self.make_schedule(PRIO)
        # order.print_info()
        while len(order) > 0:
            evse = order.pop()
            evse.ev.csc += evse.pwr * (
                env.now() - evse.ev.tcb
            )  # store charge, move to method of EV
            evse.ev.tcb = env.now()  # move to mthod of EV
            evse.pwr = min([evse.mpo, evse.ev.mpi, remaining_power])

            remaining_power -= evse.pwr  # note may not be negative
            remaining_power = max(remaining_power, 0)  # note may not be negative

    def update_se_enerygy_charged(self):
        for evse in HUB:
            if evse.ev is not None:
                # note first update power next energy
                evse.pwr = min([evse.mpo, evse.ev.mpi]) 
                evse.update_energy_charged()
            
          

    def process(self):
        while True:
            # self.assign_power() TODO
            self.update_se_enerygy_charged()
            # statistics
            [self.print_state(x) for x in HUB]

            self.standby()  # makes it run every event



# --------------------------------------------------------------------------
# Simulation
# --------------------------------------------------------------------------                        
env = Environment(trace=False, random_seed=42)

ENX_MPO = 3 * 7
PRIO = "tod"  # FIFO = toa, LIFO = -toa, EDD = tod, LL = <to_e_developed>
enx = env.Resource("enx", capacity=ENX_MPO, anonymous=False)

HUB = [EVSE(mpo=7) for _ in range(3)]

EV1 = EV(dur=40, dsc=294.4, mpi=7)
EV2 = EV(dur=50, dsc=294.4, mpi=7)
EV3 = EV(dur=70, dsc=294.4, mpi=7)

TGC(name="TGC")

EVS = []  # list of all EVs after simulation

waitingline = Queue("waitingline")
env.run()

# --------------------------------------------------------------------------
for ev in EVS:
    print(f"\n{ev.name()}")
    ev.mon_kwh.print_statistics()
    print(ev.mon_kwh.as_dataframe())
    # print(
    #     f"{ev.name()} - dsc: {ev.dsc} - csc: {ev.csc} - toa: {ev.toa} - tod: {ev.tod}"
    # )

for evse in HUB:
    print(f"\n{evse.name()}")
    evse.mon_kwh.print_statistics()
    print(evse.mon_kwh.as_dataframe())    
    # print(
    #     f"{evse.name()} - pwr: {evse.pwr} "
    # )
