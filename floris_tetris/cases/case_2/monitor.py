import salabim as sim



# ------------------------------------------------------------
# Simulation code for M/M/c queue
# ------------------------------------------------------------
# function to run simulation
def sim_facility(
    inter_arr_time_distr,  # inter-arrival time distribution
    energy_request_distr,  # energy request distribution
    number_of_EVSE,  # number of EVSE's
    max_kw,
    sim_time,
    fixed_utilization=False,
    time_unit="minutes",
    random_seed="*",
    run=1,
    number_of_evs=1,
):
    """
    Simulate a charging facility for electric vehicles.

    Args:
        ev_arrival_rate (float): The rate of EV arrivals per hour.
        energy_req_rate (float): The rate of energy requirement per hour.
        number_of_EVSE (int, optional): The number of EVSE's (Electric Vehicle Supply Equipment). Defaults to 1.
        sim_time (int, optional): The simulation time in the specified time unit. Defaults to 50000.
        time_unit (str, optional): The time unit used in the simulation. Defaults to "minutes".
        random_seed (int, optional): The random seed for reproducibility. Defaults to 123456.
        run (int, optional): The run number of the simulation. Defaults to 1.

    Returns:
        dict: A dictionary containing the simulation results including aggregate statistics.
    """
    # ------------------------------------------------------------
    cnv_hr_to_mins = 60

    # Generator which creates EV's
    class EV_Generator(sim.Component):
        # setup method is called when the component is created
        # and is used to initialize the component
        # switch off monitoring for mode and status
        def setup(self, number_of_evs):
            self.mode.monitor(False)
            self.status.monitor(False)
            self.no_of_ev = number_of_evs

        def process(self):
            ev = 1
            while ev <= self.no_of_ev:
                EV()
                iat = inter_arr_time_distr.sample()
                if fixed_utilization:
                    iat = iat / number_of_EVSE
                self.hold(iat)
                ev += 1

    class EV(sim.Component):
        def setup(self):
            self.mode.monitor(False)
            self.status.monitor(False)

        def process(self):
            self.enter(waitingline)
            for EVSE in facility:
                if EVSE.ispassive():
                    EVSE.activate()
                    break  # activate at most one charging station
            self.passivate()
            print(f"EV charged at: {app.now()}")

    class EVSE(sim.Component):
        def setup(self, max_kw):
            self.mode.monitor(False)
            self.status.monitor(False)
            self.max_kw = max_kw

            self.length = sim.Monitor(
                name="length", monitor=True, level=True, type="int32"
            )
            self.length_of_stay = sim.Monitor(
                name="length_of_stay", monitor=True, level=False, type="float"
            )
            self.power_mon = sim.Monitor(
                name="power.", monitor=True, level=True, type="float"
            )

        def process(self):
            while True:
                self.length.tally(0)
                while len(waitingline) == 0:
                    self.set_mode("Waiting")
                    self.passivate()
                self.car = waitingline.pop()
                self.length.tally(1)
                # wf = app.now()
                energy_request = energy_request_distr.sample()
                self.power = max_kw
                print(
                    f"energy requested: {energy_request}, power delivered: {self.power}"
                )
                charging_time = energy_request / self.power
                # monEVSE_IDLE.tally(wf - ws)
                self.length_of_stay.tally(charging_time)
                self.power_mon.tally(self.power)
                self.set_mode("Charging")
                self.hold(charging_time)
                self.power_mon.tally(0)
                self.car.activate()

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
    EV_Generator(name="Electric Vehicles Generator", number_of_evs=number_of_evs)

    # Create Queue and set monitor to stats_only
    # https://www.salabim.org/manual/Queue.html
    waitingline = sim.Queue(name="Waiting EV's", monitor=True)
    # waitingline.length_of_stay.monitor(value=True)
    waitingline.length.reset_monitors(stats_only=True)
    waitingline.length_of_stay.reset_monitors(stats_only=True)

    # Instantiate the EVSE's, list comprehension
    facility = [EVSE(max_kw=max_kw) for _ in range(number_of_EVSE)]

    app.AnimateMonitor(
        facility[0].power_mon,
        x=100,
        y=550,
        width=890,
        height=300,
        vertical_scale=25,
        horizontal_scale=100,
        linewidth=3,
        linecolor="green",
        title="Power",
        labels=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        nowcolor="red",
    )
    app.animate(True)

    # Execute Simulation
    app.run(till=sim_time)

    # Calculate aggregate statistics
    total_evse_stay = sum(x.length_of_stay for x in facility).mean()
    total_evse_lngt = sum(x.length for x in facility).mean()

    # waitingline.mode.print_histogram(values=True)

    lmbda = cnv_hr_to_mins / inter_arr_time_distr.mean()
    if fixed_utilization:
        lmbda = lmbda * number_of_EVSE

    # Return results
    return {
        "run": run,
        "lambda": lmbda,
        "mu": cnv_hr_to_mins / energy_request_distr.mean(),
        "c": number_of_EVSE,
        "RO": total_evse_lngt / number_of_EVSE,
        "P0": 0,
        "Lq": waitingline.length.mean(),
        "Wq": waitingline.length_of_stay.mean(),
        "Ls": total_evse_lngt + waitingline.length.mean(),
        "Ws": total_evse_stay + waitingline.length_of_stay.mean(),
    }


# ------------------------------------------------------------
# arrival rate of EVs and energy requirement rate
ev_arrival_time = 10 / 7  # hours between two arrivals
energy__request = 10  # KW requested per EV
fix_utilization = True

# SetUp Charing Infrastructure
sim_evse = range(1, 11)

# Simulation distributions
# M/M/c
# inter_arr_time_distr = sim.Exponential(60 / ev_arrival_rate)  # minutes between EV's
# energy_request_distr = sim.Exponential(60 / energy_req_rate)  # minutes to charge EV

# D/D/c
inter_arr_time_distr = sim.Uniform(
    ev_arrival_time, ev_arrival_time
)  # fixed 1.5 minutes between EV's

energy_request_distr = sim.Uniform(
    energy__request, energy__request
)  # fixed 1.2 minutes to charge EV

# M/M/c
# inter_arr_time_distr = sim.Gamma(shape = 1, scale= 60/ev_arrival_rate)  # minutes between EV's
# energy_request_distr = sim.Gamma(shape = 1, scale= 60/energy_req_rate)  # minutes to charge EV

result = sim_facility(
    inter_arr_time_distr,  # inter-arrival time distribution
    energy_request_distr,  # energy request distribution
    number_of_EVSE=1,  # number of EVSE's
    max_kw=7,
    sim_time=None,
    fixed_utilization=False,
    time_unit="hours",
    random_seed="*",
    run=1,
    number_of_evs=20,
)

print(pd.DataFrame(result, index=[0]))
