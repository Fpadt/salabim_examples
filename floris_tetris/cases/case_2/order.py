    "SRT": "rtc",  #         to be tested, dynamic - shortest remaining time       from salabim import *


class EV(Component):
    def setup(self, dur, dsc, mpi):
        # --- Constants ---
        self.mpi = mpi  #    max power input
        # --- Variables ---
        self.dur = dur  #    duration of stay
        self.toa = None  #   time of arrival
        self.tod = None  #   time of departure (estimated)
        self.dsc = dsc  #    desired state of charge in kWh
        self.csc = 0  #      current state f charge
        self.t2c = dsc/mpi # estimated time to charge
        self.llx = None  #   least Laxity
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
        # self.tcs = None  # time of charge start
        # self.pcs = None  # power at charge start
        self.pwr = 0  #      charging power
        # self.kwh = 0  #    kWh delivered
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
            self.ev.toa = env.now()
            self.ev.tod = self.ev.toa + self.ev.dur
            self.ev.llx = self.ev.tod - self.ev.t2c
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
        # --- Objects ---
        self.schedule = env.Queue("SCHEDULE")

    def make_schedule(self, property_name):
        """Make a schedule of EVSEs sorted on property_name"""
        # new schedule
        self.schedule.clear()

        # If property_name starts with a minus sign, reverse the order
        reverse = 1
        if property_name[0] == "-":
            reverse = -1
            property_name = property_name[1:]

        # Create schedule sorted on property_name
        # add the EVSE without EV at then end to make it complete
        for evse in HUB:
            if evse.ev is not None:
                property_value = reverse * getattr(evse.ev, property_name)
            else:
                property_value = float("inf")
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
        """Assign power to EVSEs according to priority
        Start with the total Power available fro Enexis
        assign according to priority set by sorting on property
        """
        # initialize the available power to the total power available
        available_power = ENX_MPO
        # make a schedule
        order = self.make_schedule(RLS[RUL])
        # order.print_info()
        # assign power to EVSEs
        while len(order) > 0:
            evse = order.pop()
            if evse.ev == None:
                evse.pwr = 0
            else:
                evse.pwr = min(
                    [
                        evse.mpo,
                        available_power,
                        evse.ev.mpi,
                    ]
                )

            available_power -= evse.pwr
            available_power = max(available_power, 0)  # note may not be negative
            print(f"available_power: {available_power}")

    def update_se_enerygy_charged(self):
        for evse in HUB:
            if evse.ev is not None:
                # note first update power next energy
                # evse.pwr = min([evse.mpo, evse.ev.mpi])
                evse.update_energy_charged()

    def process(self):
        while True:
            self.assign_power()  # TODO
            self.update_se_enerygy_charged()
            # statistics
            [self.print_state(x) for x in HUB]

            self.standby()  # makes it run every event


# --------------------------------------------------------------------------
# Simulation
# --------------------------------------------------------------------------
env = Environment(trace=False, random_seed=42)

RLS = {
    "EDD": "tod",  #         tested and Ok, static
    "LDD": "-tod",  #        tested and Ok, static
    "FIFO": "toa",  #        tested and Ok, static
    "LIFO": "-toa",  #       tested and Ok, static
    "SPT": "t2c",  #         tested and Ok, static
    "LPT": "-t2c",  #        tested and Ok, static
    "SRT": "rtc",  #         to be tested, dynamic - shortest remaining time       
    "LRT": "-rtc",  #        to be tested, dynamic - longest  remaining time       
    "LLX": "llx", #          tested and ok, static
    "RLX": "rlx", #          to be tested, dynamic - remaining laxity
}
RUL = "LLX"

ENX_MPO = 1 * 7
enx = env.Resource("enx", capacity=ENX_MPO, anonymous=False)

HUB = [EVSE(mpo=7) for _ in range(3)]

EV1 = EV(dur=20, dsc=140, mpi=7)
EV2 = EV(dur=50, dsc=280, mpi=7)
EV3 = EV(dur=70, dsc=290, mpi=7)

TGC(name="TGC")

EVS = []  # list of all EVs after simulation

waitingline = Queue("waitingline")
env.run()

# --------------------------------------------------------------------------
# Reporting Results
# --------------------------------------------------------------------------
for ev in EVS:
    print(f"\n{ev.name()}")
    ev.mon_kwh.print_statistics()
    print(f"EV kWh: {ev.mon_kwh.duration(ex0=True) * ev.mon_kwh.mean(ex0=True)}")
    # print(ev.mon_kwh.as_dataframe())
    # print(
    #     f"{ev.name()} - dsc: {ev.dsc} - csc: {ev.csc} - toa: {ev.toa} - tod: {ev.tod}"
    # )

# for evse in HUB:
#     print(f"\n{evse.name()}")
#     evse.mon_kwh.print_statistics()
#     print(f"SE kWh: {evse.mon_kwh.duration(ex0=False) * evse.mon_kwh.mean(ex0=False)}")
# print(f"test: {evse.mon_kwh.duration_zero()}")
# print(f"tot: {tot}")

# print(evse.mon_kwh.as_dataframe())
# print(
#     f"{evse.name()} - pwr: {evse.pwr} "
# )

# what if request is leass than time to charge TODO