import salabim as sim
import pandas as pd


# ------------------------------------------------------------
# Simulation code for D/D/1
# ------------------------------------------------------------
# function to run simulation
def sim_e_parking(
    inter_arr_time_distr,  # inter-arrival time distribution
    energy_request_distr,  # energy request distribution
    fixed_utilization,
    number_of_EVs,
    ev_max_kw,
    ev_stay,
    number_of_PARKING_LOTs,
    number_of_EVSEs,  # number of EVSE's
    evse_max_kw,
    enexis_kw,
    sim_time,
    time_unit,
    random_seed,
    run,
):
    # ------------------------------------------------------------
    cnv_hr_to_mins = 60

    # Generator which creates EV's up to a certain number
    class EV_Generator(sim.Component):
        # setup method is called when the component is created
        # and is used to initialize the component
        # switch off monitoring for mode and status
        def setup(self, number_of_EVs):
            self.no_of_ev = number_of_EVs

        def process(self):
            ev = 1
            while ev <= self.no_of_ev:
                EV()
                iat = inter_arr_time_distr.sample()
                if fixed_utilization:
                    iat = iat / number_of_EVSEs
                self.hold(iat)
                ev += 1

    class EV(sim.Component):
        def setup(self):
            # energy request in kwh
            self.max_kw = ev_max_kw
            self.kwh_req = energy_request_distr.sample()
            self.stay = ev_stay
            self.kwh_charged = 0
            self.evse_name = None

        def process(self):
            self.enter(waitingline)
            for PLOT in e_parking_plots:
                if PLOT.ispassive():
                    PLOT.activate()
                    break  # activate at most one parking lot
            self.passivate()
            print(
                f"EV: {self.name()} charged: {100*self.kwh_charged/self.kwh_req}% station: {self.evse_name} left at: {app.now()}"
            )

    class PLOT(sim.Component):
        def setup(self):

            self.length = sim.Monitor(
                name="length", monitor=True, level=True, type="int32"
            )
            self.length_of_park = sim.Monitor(
                name="length_of_park", monitor=True, level=False, type="float"
            )
            self.length_of_charge = sim.Monitor(
                name="length_of_charge", monitor=True, level=False, type="float"
            )
            self.power_consumption = sim.Monitor(
                name="power.", monitor=True, level=True, type="float"
            )

            if EVSE_POOL.available_quantity() > 0:
                self.request(EVSE_POOL)
                self.evse = True
            else:
                self.evse = False
            self.power = evse_max_kw

        def process(self):
            while True:
                # get an ev from the queue
                self.length.tally(0)
                while len(waitingline) == 0:
                    self.passivate()
                self.ev = waitingline.pop()
                self.length.tally(1)
                # determine power (if no EVSE then 0)
                power = min(
                    self.evse * self.ev.max_kw,  # if self.evse = false then 0
                    self.power,
                    ENEXIS_KW.available_quantity(),
                )
                if power > 0:
                    # request power from Eneixs
                    self.request((ENEXIS_KW, power))
                    # determine time to charge
                    time_charge_in_full = self.ev.kwh_req / power
                    time_constr_to_charge = min(time_charge_in_full, self.ev.stay)
                    # charging
                    self.power_consumption.tally(power)
                    enexis_monitor.activate()
                    self.hold(time_constr_to_charge)
                    self.release((ENEXIS_KW, power))
                else:
                    # no charging possible
                    time_constr_to_charge = 0
                # update statistics
                self.ev.kwh_charged = time_constr_to_charge * power
                self.ev.evse_name = self.name()
                self.length_of_charge.tally(time_constr_to_charge)
                enexis_monitor.activate()
                self.power_consumption.tally(0)
                # plain parking
                self.hold(self.ev.stay - time_constr_to_charge)
                self.ev.activate()

    class TMON(sim.Component):
        def setup(self):
            self.total_power_consumption = sim.Monitor(
                name="total_power", monitor=True, level=True, type="float"
            )

        def process(self):
            while True:
                tot_pwr = sum(x.power_consumption.get() for x in e_parking_plots)
                self.total_power_consumption.tally(tot_pwr)
                self.passivate()

    # ------------------------------------------------------------
    # https://www.salabim.org/manual/Reference.html#environment
    app = sim.App(
        trace=False,  # defines whether to trace or not
        random_seed=random_seed,  # if “*”, a purely random value (based on the current time)
        time_unit=time_unit,  # defines the time unit used in the simulation
        name="Charging Station",  # name of the simulation
        do_reset=True,  # defines whether to reset the simulation when the run method is called
        yieldless=True,  # defines whether the simulation is yieldless or not
    )

    # Instantiate and activate the client generator
    EV_Generator(name="Electric Vehicles Generator", number_of_EVs=number_of_EVs)

    # Create Queue and set monitor to stats_only
    # https://www.salabim.org/manual/Queue.html
    waitingline = sim.Queue(name="Waiting EV's", monitor=True)
    # waitingline.length_of_stay.monitor(value=True)
    waitingline.length.reset_monitors(stats_only=True)
    waitingline.length_of_stay.reset_monitors(stats_only=True)

    # Create EVSE Pool and ENEXIS connection as capacity Resources
    EVSE_POOL = sim.Resource("EVSE's", capacity=number_of_EVSEs)
    ENEXIS_KW = sim.Resource("ENEXIS", capacity=enexis_kw)

    # Instantiate the EVSE's, list comprehension
    e_parking_plots = [PLOT() for _ in range(number_of_PARKING_LOTs)]

    enexis_monitor = TMON()

    app.AnimateMonitor(
        e_parking_plots[0].power_consumption,
        x=100,
        y=150,
        width=300,
        height=200,
        vertical_offset=0,
        vertical_scale=8,
        horizontal_scale=100,
        titlefont="Ubuntu Bold",
        titlefontsize=20,
        titlecolor="#B6D300",          
        linewidth=5,
        linecolor="#B6D300",
        title="Power EVSE: 0",
        labels=list(range(0, ENEXIS_MAX_KW + 10 + 1, 5)),
        nowcolor="red",
    )

    app.AnimateMonitor(
        e_parking_plots[1].power_consumption,
        x=500,
        y=150,
        width=300,
        height=200,
        vertical_offset=0,
        vertical_scale=8,        
        horizontal_scale=100,
        titlefont="Ubuntu Bold",
        titlefontsize=20,
        titlecolor="#B6D300",        
        linewidth=5,
        linecolor="#B6D300",
        title="Power EVSE:1",
        labels=list(range(0, ENEXIS_MAX_KW + 10 + 1, 5)),
        nowcolor="red",
    )

    app.AnimateMonitor(
        enexis_monitor.total_power_consumption,
        x=100,
        y=450,
        width=400,
        height=200,
        vertical_offset=0,
        vertical_scale=8,
        horizontal_scale=100,
        titlefont="Ubuntu Bold",
        titlefontsize=20,
        titlecolor="#D8006F",
        linewidth=5,
        linecolor="#D8006F",
        title="ENEXIS - Total Power Consumption",
        labels=list(range(0, ENEXIS_MAX_KW + 10 + 1, 5)),
        nowcolor="red",
    )

    app.animate(True)

    # Execute Simulation
    app.run(till=sim_time)

    # lmbda = cnv_hr_to_mins / inter_arr_time_distr.mean()
    # if fixed_utilization:
    #     lmbda = lmbda * number_of_EVSEs

    # Return results
    return {
        "iat": inter_arr_time_distr.mean(),
        "pwr": energy_request_distr.mean(),
        # "run": run,
        # "lambda": lmbda,
        # "mu": cnv_hr_to_mins / energy_request_distr.mean(),
        "lots": number_of_PARKING_LOTs,
        "evse": number_of_EVSEs,
        # "RO": total_evse_lngt / number_of_EVSEs,
        "P0": 0,
        "Lq": waitingline.length.mean(),
        "Wq": waitingline.length_of_stay.mean(),
        # "Ls": total_evse_lngt + waitingline.length.mean(),
        # "Ws": total_evse_stay + waitingline.length_of_stay.mean(),
    }


# user parameters
ev_arrival_time = 0  # 10 / 7  # hours between two arrivals
energy__request = 10  # KW requested per EV

# D/D/c
INTER_ARR_TIME_DISTR = sim.Uniform(ev_arrival_time, ev_arrival_time)
ENERGY_REQUEST_DISTR = sim.Uniform(energy__request, energy__request)
FIXED_UTILIZATION = True

# Electric Vehicles
NUMBER_OF_EVS = 16
EV_MAX_KW = 10
EV_STAY = 1.0

# number of parking lots
NUMBER_OF_LOTS = 2

# EVSE's 
NUMBER_OF_EVSES = 2
EVSE_MAX_KW = 10

# Capacity Enexis
ENEXIS_MAX_KW = 10

# simulation parameters
SIM_TIME = None
TIME_UNIT = "hours"
RANDOM_SEED = "*"
RUN = 1

result = sim_e_parking(
    INTER_ARR_TIME_DISTR,  # inter-arrival time distribution
    ENERGY_REQUEST_DISTR,  # energy request distribution
    FIXED_UTILIZATION,
    NUMBER_OF_EVS,
    EV_MAX_KW,
    EV_STAY,
    NUMBER_OF_LOTS,
    NUMBER_OF_EVSES,  # number of EVSE's
    EVSE_MAX_KW,
    ENEXIS_MAX_KW,
    SIM_TIME,
    TIME_UNIT,
    RANDOM_SEED,
    RUN,
)

# print(pd.DataFrame(result, index=[0]))
