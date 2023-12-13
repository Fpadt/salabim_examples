import salabim as sim
import pandas as pd

# ------------------------------------------------------------
# Simulation code for D/D/1 
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
    video_name = None,
):
    
    # ------------------------------------------------------------
    cnv_hr_to_mins = 60
    breakpoint()
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
            print(f"numbering {ev}")
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
            print(f"EV: {self.name()} charged at: {app.now()}")

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

                energy_request = energy_request_distr.sample()
                self.power = max_kw
                print(
                    f"EV: {self.car.name()} energy requested: {energy_request}, power delivered: {self.power}"
                )
                charging_time = energy_request / self.power
                self.length_of_stay.tally(charging_time)
                self.power_mon.tally(self.power)

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
        y=150,
        width=890,
        height=300,
        vertical_scale=25,
        horizontal_scale=100,
        linewidth=3,
        linecolor="green",
        title="Power Consumption:   -> " + video_name,
        titlecolor="green",
        titlefontsize=20,
        nowcolor="red",
        labels=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    )
    
    app.animate(True)
    app.modelname("Tetris: the game charger")

    # Execute Simulation
    if video_name is not None:
        app.video(video_name + ".mp4")
        app.video_mode("2d")
        app.run(till=sim_time)
        app.video_close()
    else:
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



# user parameters
# ev_arrival_time = 10 / 7  # hours between two arrivals
ev_arrival_time = 14 / 7  # hours between two arrivals
energy__request = 10  # KW requested per EV

# D/D/c
inter_arr_time_distr = sim.Uniform(ev_arrival_time, ev_arrival_time)
energy_request_distr = sim.Uniform(energy__request, energy__request)
fixed_utilization = False

# Electric Vehicles
number_of_evs = 7

# EVSE's 
number_of_EVSE = 1
max_kw = 7

# Capacity Enexis
enexis_kw = 10 

# simulation parameters
sim_time = None
time_unit = "hours"
random_seed = "*"
run = 1

result = sim_facility(
    inter_arr_time_distr,  # inter-arrival time distribution
    energy_request_distr,  # energy request distribution
    number_of_EVSE,  # number of EVSE's
    max_kw,
    sim_time,
    fixed_utilization,
    time_unit,
    random_seed,
    run,
    number_of_evs,
    video_name = "case_evse-7kw-enx-10kw_util-71"
)

print(pd.DataFrame(result, index=[0]))