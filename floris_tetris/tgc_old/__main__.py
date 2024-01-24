# enr - Charge gained during charging session (in kWh or %).
# rat - Charging rate (in kW).


# typ - Type of charger (e.g., Level 1, Level 2, DC Fast Charger).
# tch - Total charging time required to reach `dsc`.
# cst - Cost of charging per session.
# pwr - Power being drawn at any given moment (in kW).
# los - Energy loss during charging (as a percentage or kWh).


# dis -
# ecp -


# isc - initial state of charge
# csc - current state of charge
# dsc - desired state of charge

# iel - initial energy level
# cel - current energy level
# del - desired energy level


# sat - satisfaction

# ------------------------------------------------------------------------
# packages and coding import
# ------------------------------------------------------------------------

# packages
import salabim as sim
from config import *
from tgc_floris_padt.test_ev_charge_profile import *
from plotnine import ggplot, aes, geom_point
import matplotlib.pyplot as plt

# from tgcsim.models.generator import EV_Generator, SE_Generator

# from olp_abstract_model import *
# from energy_price import *

# --------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------


class EV(sim.Component):
    """Class to model the behavior of an Electrical Vehicle (ev).

    Args:
        duration_of_stay (float): Duration of the ev stay. [h]
        initial_state_of_charge (float): State of charge of the ev on arrival. [kWh]
        desired_state_of_charge (float): Desired state of charge of the ev on departure. [kWh]
        ev_battery_capacity (float): Maximum Capacity of the ev battery. [kWh]
        ev_max_power_input (float): Maximum power input of the ev. [kW]
        battery_degradation (float): Battery degradation factor of the ev. [kW]
    """

    def setup(
        self,
        duration_of_stay,
        initial_state_of_charge,
        desired_state_of_charge,
        ev_battery_capacity,
        ev_max_power_input,
        battery_degradation,
    ):
        # --- Constants ---
        self._dur = duration_of_stay
        self._isc = initial_state_of_charge
        self._dsc = desired_state_of_charge
        self._cap = ev_battery_capacity
        self._deg = battery_degradation
        # --- Static ---
        self._iel = self._isc * self._cap
        self._cel = self._iel
        self._del = self._dsc * self._cap
        # --- Dynamic ---
        self._mpi = ev_max_power_input
        self._rel = min(self._iel + self._dur * self._mpi, self._del)
        self._rtc = self._rel/self._cap

        # --- Variables ---
        self._toa = None  #
        self._tod = None
        self._tss = None  #                   time of start of time slot
        self._tch = self._rel / self._mpi  #  estimated time to charge to reach dsc
        self._llx = None  #                   least Laxity
        self._ses = None
        self._val = True  #                   valid entry which entered the system

        # --- Monitors ---
        # self.mon_kwh = sim.Monitor(name="EV kWh", level=False)
        self.mon_dur = sim.Monitor(name="EV Dur", level=False)

    # --- properties Read ---
    @property
    def cap(self):
        return self._cap

    # @property
    # def enr(self):
    #     return self._cel - self._iel

    @property
    def deg(self):
        return self._deg

    @property
    def dsc(self):
        return self._dsc

    @property
    def dur(self):
        return self._dur

    @property
    def llx(self):
        return self._llx

    @property
    def isc(self):
        return self._isc

    @property
    def rtc(self):
        rtc = max((self._rel - self._cel) / self._mpi, 0)
        if self._tod - app.now() < rtc:
            rtc = float("inf")
        return rtc

    @property
    def tch(self):
        return self._tch

    # TODO formula for > 80
    # TODO if cel = rel mpi = 0
    @property
    def mpi(self):
        mpi = 0
        if self._cel < self._rel:
            mpi = self._mpi
        return mpi

    @property
    def pwr(self):
        return self._pwr

    @property
    def sat(self):
        if self._rel <= self._iel:
            return np.nan
        else:
            return 100 * (self._cel - self._iel) / (self._rel - self._iel)

    @property
    def ses(self):
        return self._ses

    @property
    def toa(self):
        return self._toa

    @property
    def tod(self):
        return self._tod

    # --- properties Write ---
    # @enr.setter
    # def enr(self, value):
    #     self._cel += value
    #     # self.mon_kwh.tally(value)

    # @pwr.setter
    # def pwr(self, value):
    #     energy_charged = (app.now() - self._tss) * self._ppw
    #     self._cel += energy_charged
    #     # self.mon_kwh.tally(energy_charged)
    #     self._ppw = self._pwr
    #     self._tss = app.now()
    #     self._pwr = value

    @ses.setter
    def ses(self, session):
        self._ses = session

    @toa.setter
    def toa(self, start_time_of_charge):
        self._toa = start_time_of_charge
        self._tss = self._toa
        self._tod = self._toa + self._dur
        self._llx = self._tod - self._tch

    # --- Methods ---
    def update_energy_charged(self, power):
        energy_charged = (app.now() - self._tss) * power
        self._cel += energy_charged
        # self.mon_kwh.tally(energy_charged)
        self._tss = app.now()

    def process(self):
        if len(QUE) >= q:
            app.number_balked += 1
            self.cancel()
        # enter the waiting line
        self.enter(QUE)
        # check if any SE is available
        for se in HUB.ses:
            if se.ispassive():
                se.activate()
                break
        self.hold(w, priority=1)  # if not serviced within this time, renege
        if self in QUE:
            self.leave(QUE)
            app.number_reneged += 1
        else:
            self.passivate()  # wait for service to be completed


class SE(sim.Component):
    """Class to model the behaviour of Supply Equipment (SE).

    Args:
        se_max_power_output (float): Maximum power output of the se. [kW]
        connected_to_grid (bool): True if connected to the grid, False if not.
    """

    def setup(self, se_max_power_output, connected_to_grid):
        # --- Constants ---
        self._mpo = se_max_power_output
        self._con = connected_to_grid
        # --- Variables ---
        self._pwr = 0
        self._ppw = 0  # previous power
        # --- Objects ---
        self._evc = None  # ev being charged
        # --- Monitors ---
        self.mon_kwh = sim.Monitor(name="SE kWh", level=True)
        self.mon_dur = sim.Monitor(name="SE Dur", level=False)

    # --- properties Read ---
    @property
    def con(self):
        return self._con

    @property
    def mpo(self):
        return self._mpo    

    @property
    def pwr(self):
        return self._pwr

    @property
    def evc(self):
        return self._evc

    @property
    def utl(self):
        return 100 * self.mon_kwh.mean(ex0=False) / self._mpo

    # --- properties Write ---
    @con.setter
    def con(self, value):
        self._con = value

    @pwr.setter
    def pwr(self, value):
        # self._ppw = self._pwr
        self._pwr = value
        self.mon_kwh.tally(self._pwr)

    # --- Methods ---
    def update_energy_charged(self):
        # self.mon_kwh.tally(self._pwr)
        self._evc.update_energy_charged(self._pwr)
        # self._evc.enr = self._ppw * slot_duration

    def get_charge_profile(self):
        if self._evc is None:
            return None
        else:
            return charge_profile(
                dur=self._evc.dur,
                soc=self._evc.isc,
                dsc=self._evc.dsc,
                cap=self._evc.cap,
                mpi=self._evc.mpi,
                mpo=self.mpo,
                deg=self._evc.deg,
            )

    def process(self):
        while True:
            # wait for EV to arrive
            while len(QUE) == 0:
                self.passivate()

            # assign EV
            self._evc = QUE.pop()
            self._evc.ses = self.name() + "-" + self._evc.name()
            self._evc.toa = app.now()

            # charge EV
            self.hold(self._evc.dur, priority=2)

            # update statistics
            self.update_energy_charged()
            self.mon_kwh.tally(0)
            self.mon_dur.tally(self._evc.dur)
            self._evc.mon_dur.tally(self._evc.dur)

            # register EV in list for Reporting
            self._evc.register(app.evs)

            # release EV
            self._evc = None

class TGC_clock(sim.Component):
    
    def process(self):
        while True:
            self.passivate()


class TGC(sim.Component):
    def setup(self):
        # --- Objects ---
        self.schedule = app.Queue("SCHEDULE")
        self._clock = TGC_clock()

    def set_clock(self):
        min_rtc = float("inf")
        for se in HUB.ses:
            if se.evc is not None and se.evc.isscheduled():
                if se.evc.rtc > 0:
                    tst =se.scheduled_time() - app.now()
                    min_rtc = min(min_rtc, se.evc.rtc)  
                if min_rtc <= 0:
                    min_rtc = float("inf") 
        self._clock.activate()
        self._clock.remaining_duration(min_rtc, priority=0, urgent=True)        

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
        for se in HUB.ses:
            if se.evc is None or se.con == False:
                property_value = float("inf")
            else:
                property_value = reverse * getattr(se.evc, property_name)
            self.schedule.add_sorted(se, property_value)

        return self.schedule

    def print_state(self, se):
        if se.evc is None:
            None
            # print(f"{app.now()}\t - NO_EV/{se.name()} ")
        else:
            #   toa: {se.ev.toa} - tod: {se.ev.tod} -  \
            print(
                f"""{app.now()}\t{se.evc.name()}/{se.name()}\tcsc: {se.evc.sat}"""
                # \tpwr: {se.pwr}\tdsc: {round(se.ev.dsc)}  rem: {se.remaining_duration()}\tsch: {se.scheduled_time()}"""
            )

    def print_charge(self, se):
        if se.evc is None:
            print(f"{app.now()}\t - NO_EV/{se.name()} ")
        else:
            print(
                se.get_charge_profile()
                # f"{env.now()}\t - {evse.ev.name()}/{evse.name()} - pwr: {evse.pwr}\
                #   dc: {round(evse.ev.dc)} - ckwh: {round(evse.ev.ckwh)} - \
                #   rem: {evse.remaining_duration()} sch: {evse.scheduled_time()}"
            )

    def assign_power(self):
        """Assign power to EVSEs according to priority
        Start with the total Power available fro Enexis
        assign according to priority set by sorting on property
        """
        # initialize the available power to the total power available
        available_power = EX_MPO
        # make a schedule
        order = self.make_schedule(RLS[RUL])
        # order.print_info()
        # assign power to EVSEs
        while len(order) > 0:
            se = order.pop()
            if se.evc == None:
                se.pwr = 0
            else:
                se.pwr = se.con * min(
                    [
                        se.mpo,
                        available_power,
                        se.evc.mpi,
                    ]
                )

            available_power -= se.pwr
            available_power = max(available_power, 0)  # note may not be negative
            # print(f"available_power: {available_power}")

    def update_se_enerygy_charged(self):
        for se in HUB.ses:
            if se.evc is not None and se.evc.isscheduled():
                se.update_energy_charged()

    # def determine_next_hold(self):
    #     min_time_slot = tgc_hold



    #     for se in HUB.ses:
    #         if se.evc is not None and se.isscheduled():
    #             st = se.scheduled_time() - app.now()
    #             if st > 0 and st < min_time_slot:
    #                 min_time_slot = se.scheduled_time() - app.now()
    #     return min_time_slot

    def process(self):
        ts = 0
        while True:
            ts = app.now()
            self.update_se_enerygy_charged()
            self.set_clock()            
            self.assign_power()            
            ts = app.now()
            # statistics
            # [self.print_state(x) for x in HUB.ses]
            # [self.print_charge(x) for x in HUB.ses]
            # next_hold = self.determine_next_hold()
            self.standby()
            # self.hold(next_hold, priority=0, urgent=True)  # makes it run every hour


# --------------------------------------------------------------------------
# Generators
class EV_Generator(sim.Component):
    """Class to model the behaviour of an Electrical Vehicle (ev).

    Args:
        number_of_evs (int): Number of EVs to be generated.
    """

    def setup(self, number_of_evs):
        self.cnt_evs = number_of_evs
        self.rnd_iat = create_random_generator(params_dict, "IAT")
        self.rnd_dur = create_random_generator(params_dict, "DUR")
        self.rnd_isc = create_random_generator(params_dict, "ISC")
        self.rnd_dsc = create_random_generator(params_dict, "DSC")
        self.rnd_cap = create_random_generator(params_dict, "CAP")
        self.rnd_mpi = create_random_generator(params_dict, "MPI")
        self.rnd_deg = create_random_generator(params_dict, "DEG")

    # def registrate(self, ev):
    #     ev.register(self._evs)

    def process(self):
        i = 1
        while i <= self.cnt_evs:
            # create random values and potentially link them
            dur = self.rnd_dur()
            cap = self.rnd_cap()
            mpi = self.rnd_mpi()
            isc = self.rnd_isc()
            dsc = self.rnd_dsc()  # 1 * dur * mpi / cap + isc # 
            deg = self.rnd_deg()
            # create EV and assign random values
            ev = EV(
                duration_of_stay=dur,
                initial_state_of_charge=isc,
                desired_state_of_charge=dsc,
                ev_battery_capacity=cap,
                ev_max_power_input=mpi,
                battery_degradation=deg,
            )

            # hold for interarrival time
            self.hold(self.rnd_iat(), priority=1)
            i += 1
            #
            if print_ev:
                print(f"EV {ev.name()}")
                print(f"dur {ev.dur}")
                print(f"soc {ev.soc}")
                print(f"dsc {ev.dsc}")
                print(f"cap {ev.cap}")
                print(f"mpi {ev.mpi}")
                print(f"deg {ev.deg}")
                print(" \n")


class SE_Generator(sim.Component):
    """Class to model the behaviour of Supply Equipment (SE).

    Args:
        number_of_ses (int): Number of SEs to be generated.
        number_of_con (int): Number of SEs connected to the grid.
    """

    def setup(self, number_of_ses, number_of_con):
        self.nse = number_of_ses
        self.ncn = number_of_con
        self.ses = []

        self.rnd_mpo = create_random_generator(params_dict, "MPO")

    def process(self):
        i = 1
        while i <= self.nse:
            se = SE(se_max_power_output=self.rnd_mpo(), connected_to_grid=LAY[i - 1])
            se.register(self.ses)
            i += 1


# --------------------------------------------------------------------------
# Simulation
# --------------------------------------------------------------------------

app = sim.App(
    trace=False,  #                    defines whether to trace or not
    random_seed=random_seed,  #        if “*”, a purely random value (based on the current time)
    time_unit=time_unit,  #            defines the time unit used in the simulation
    name="Tetris Game Charger",  #     name of the simulation
    do_reset=True,  #                  defines whether to reset the simulation when the run method is called
    yieldless=True,  #                 defines whether the simulation is yieldless or not
)

app.number_balked = 0
app.number_reneged = 0
app.evs = []

# Create Queue and set monitor to stats_only
QUE = sim.Queue("waiting_line")
# https://www.salabim.org/manual/Queue.html
QUE.length_of_stay.monitor(value=True)
QUE.length_of_stay.reset_monitors(stats_only=True)

# note: order of creation is important
TGC = TGC(name="Tetris Game Charger")
HUB = SE_Generator(number_of_ses=m, number_of_con=c)
GEN = EV_Generator(number_of_evs=e)

# Execute Simulation
sim_start = datetime.now()
app.run(till=sim_time)


# --------------------------------------------------------------------------
# Reporting Results
# --------------------------------------------------------------------------

print("\n")
QUE.length_of_stay.print_statistics()
print(f"Wq: = {QUE.length_of_stay.mean()}\n")

print(f"\nEVs balked: {app.number_balked}")
print(f"EVs reneged: {app.number_reneged}")

# --- EV Statistics ---

if print_ev_details == True:
    print("\nEV Statistics:")
    for ev in app.evs:
        print(
            f"""{ev.name()}\t \
    toa: {round(ev._toa, 2)}\tdur: {round(ev._dur, 2)}\ttss: {round(ev._tss, 2)}\t \
    iel: {round(ev._iel, 2)}\tdel: {round(ev._del, 2)}\trel: {round(ev._rel, 2)}\tcel: {round(ev._cel, 2)}\t \
    sat: {round(ev.sat, 2)} %"""
        )

    # iel: {round(ev._iel, 2)} kWh\t \
# --- SE Statistics ---
if print_se_details == True:
    print("\nSE Statistics:")

    for se in HUB.ses:
        print(
            f"""{se.name()}\t \
            tot: {round(se.mon_kwh.duration(ex0=False) * se.mon_kwh.mean(ex0=False), 2)} kWh\t \
            dur: {round(se.mon_kwh.duration(ex0=False), 2)} hrs\t \
            avg: {round(se.mon_kwh.mean(ex0=False), 2)} kWh\t \
            utl: {round(se.utl, 2)} %"""
        )

    # se.mon_kwh.print_statistics()
    # se.mon_dur.print_statistics()
    # print(se.mon_kwh.as_dataframe())
# --- Customer Satisfaction ---
sat_values = [ev.sat for ev in app.evs]
mean_sat = np.nanmean(sat_values)

print(f"Customer Satisfaction: {round(mean_sat, 2)} %")

# --- Enexis ---
enx_mon = sum(se.mon_kwh for se in HUB.ses).rename("Enexis performance")
# enx_mon.print_statistics()

dlv = enx_mon.duration(ex0=False) * enx_mon.mean(ex0=False)
pot = enx_mon.duration(ex0=False) * (EX_MPO - enx_mon.mean(ex0=False))
utl = dlv / (dlv + pot)

print(
    f"""
      Enexis Grid Utilization: {round(100*utl)} %\t\
      Energy Delivered: {round(dlv, 2)} kWh\t\
      missed to deliver: {round(pot, 2)} kWh"""
)

print(f"\nSimulation time: {datetime.now() - sim_start}")

# --- Plot ---
dfRaw = enx_mon.as_dataframe()
dfRaw = dfRaw.rename(columns={"enxpwr": "B"})
dfResult = dfRaw.round(2)
dfResult.to_csv(
    "time"
    + str(sim_time)
    + "_enx_c"
    + str(c)
    + "_q"
    + str(q)
    + "_r"
    + str(r)
    + "_.csv",
    index=False,
    header=True,
    sep=";",
    decimal=".",
)


# check coding in EV generator TODO for dsc and isc
# check als tch charge less than duration TODO ??
# ev.mpi formule > 80% TODO
# OLP koppelen
# duration and iel dynamisch maken
