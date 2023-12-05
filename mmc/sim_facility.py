import salabim as sim
from datetime import datetime
import pandas as pd

# ------------------------------------------------------------
# Simulation code for M/M/c queue
# ------------------------------------------------------------
# function to run simulation
def sim_facility(
    ev_arrival_rate,  # EV's per hour
    energy_req_rate,  # KW per hour
    number_of_EVSE=1,  # number of EVSE's
    sim_time=50000,
    time_unit="minutes",
    random_seed=123456,
    run=1,
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
    # Generator which creates EV's
    class EV_Generator(sim.Component):
        # setup method is called when the component is created
        # and is used to initialize the component
        # switch off monitoring for mode and status
        def setup(self):
            self.mode.monitor(False)
            self.status.monitor(False)

        def process(self):
            while True:
                EV()
                self.hold(inter_arr_time_distr.sample())

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

    class EVSE(sim.Component):
        def setup(self):
            self.mode.monitor(False)
            self.status.monitor(False)

            self.length = sim.Monitor(
                name="length", monitor=True, level=True, type="int32"
            )
            self.length_of_stay = sim.Monitor(
                name="length_of_stay", monitor=True, level=False, type="float"
            )
            self.power_mon = sim.Monitor(
                name="power.", monitor=True, level=True, type="float"
            )
            self.power = 1.0

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
                charging_time = energy_request / self.power
                # monEVSE_IDLE.tally(wf - ws)
                self.length_of_stay.tally(charging_time)
                self.power_mon.tally(self.power)
                self.set_mode("Charging")
                self.hold(charging_time)
                self.car.activate()

    # Create distributions
    inter_arr_time_distr = sim.Exponential(60 / ev_arrival_rate)  # minutes between EV's
    energy_request_distr = sim.Exponential(60 / energy_req_rate)  # minutes to charge EV

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
    EV_Generator(name="Electric Vehicles Generator")

    # Create Queue and set monitor to stats_only
    # https://www.salabim.org/manual/Queue.html
    waitingline = sim.Queue(name="Waiting EV's", monitor=True)
    # waitingline.length_of_stay.monitor(value=True)
    waitingline.length.reset_monitors(stats_only=True)
    waitingline.length_of_stay.reset_monitors(stats_only=True)

    # Instantiate the EVSE's, list comprehension
    facility = [EVSE() for _ in range(number_of_EVSE)]

    # Execute Simulation
    app.run(till=sim_time)

    # Calculate aggregate statistics
    total_evse_stay = sum(x.length_of_stay for x in facility).mean()
    total_evse_lngt = sum(x.length for x in facility).mean()

    # waitingline.mode.print_histogram(values=True)

    # Return results
    return {
        "run": run,
        "lambda": ev_arrival_rate,
        "mu": energy_req_rate,
        "c": number_of_EVSE,
        "RO": total_evse_lngt / number_of_EVSE,
        "P0": 0,
        "Lq": waitingline.length.mean(),
        "Wq": waitingline.length_of_stay.mean(),
        "Ls": total_evse_lngt + waitingline.length.mean(),
        "Ws": total_evse_stay + waitingline.length_of_stay.mean(),
    }

# ------------------------------------------------------------
# function to run simulation X times per EVSE for all EVSE's
# ------------------------------------------------------------

# returns a DataFrame with the results
def sim_x_facility(
    ev_arrival_rate,
    energy_req_rate,
    number_of_EVSE=1,
    sim_time=50000,
    number_of_simulations=30,
    verbose=False,
):
    """
    Simulate the facility with multiple runs using different random seeds.

    Parameters:
    ev_arrival_rate (float): The rate of EV arrivals.
    energy_req_rate (float): The rate of energy requirement.
    number_of_EVSE (int, optional): The number of EVSEs. Defaults to 1.
    sim_time (int, optional): The simulation time. Defaults to 50000.
    number_of_simulations (int, optional): The number of simulations to run. Defaults to 30.
    verbose (bool, optional): Whether to print verbose output. Defaults to False.

    Returns:
    pandas.DataFrame: A DataFrame containing the results of all simulations.
    """
    # Create empty list to store results
    sim_runs = []

    # Run simulation X times with different random seeds for same number of EVSE's
    for i in range(number_of_simulations):
        sim_runs.append(
            sim_facility(
                ev_arrival_rate=ev_arrival_rate,
                energy_req_rate=energy_req_rate,
                number_of_EVSE=number_of_EVSE,
                sim_time=sim_time,
                random_seed=i,
                run=i,
            )
        )
        if verbose:
            print(f"EVSE's {number_of_EVSE}, run {i} completed at {datetime.now()}")

    # Concatenate all runs
    return pd.DataFrame(sim_runs)

# ------------------------------------------------------------
# function to run simulation X times per EVSE for all EVSE's
# ------------------------------------------------------------

# function to run simulation X times per EVSE for all EVSE's
def sim_x_facility_per_evse(
    ev_arrival_rate,
    energy_req_rate,
    range_of_EVSE=range(1,2),
    sim_time=50000,
    number_of_simulations=30,
    fixed_utilization=True,
    verbose=False,
):
    """
    Simulates the facility for different numbers of EVSEs and returns the concatenated results.

    Parameters:
    - ev_arrival_rate (float): The arrival rate of EVs.
    - energy_req_rate (float): The rate at which energy is required by EVs.
    - range_of_EVSE (range, optional): The range of EVSEs to simulate. Defaults to range(1,2).
    - sim_time (int, optional): The simulation time in seconds. Defaults to 50000.
    - number_of_simulations (int, optional): The number of simulations to run. Defaults to 30.
    - fixed_utilization (bool, optional): Whether to use fixed utilization or not. Defaults to True.
    - verbose (bool, optional): Whether to print verbose output or not. Defaults to False.

    Returns:
    - pandas.DataFrame: The concatenated results of all simulations.
    """
    # Initialize an empty list
    dfs = []

    # Execute the simulation for each EVSE
    for j in range_of_EVSE:
        # Execute simulation
        df = sim_x_facility(
            ev_arrival_rate=j * ev_arrival_rate if fixed_utilization else ev_arrival_rate,
            energy_req_rate=energy_req_rate,
            number_of_EVSE=j,
            sim_time=sim_time,
            number_of_simulations=number_of_simulations,
            verbose=verbose,
        )
        # Append df to dfs
        dfs.append(df)

    # Concatenate all DataFrames in dfs
    return pd.concat(dfs, axis =0, ignore_index=True)

# ------------------------------------------------------------
# Simulate Facitily
# ------------------------------------------------------------

def simulate_facility(
        ev_arrival_rate,
        energy_req_rate,
        range_of_EVSE,
        sim_time,
        number_of_simulations,
        ffn_results=None,
        verbose=True,
):
    """
    Simulates the facility based on the given parameters.

    Args:
        ev_arrival_rate (float): The arrival rate of electric vehicles.
        energy_req_rate (float): The energy request rate of electric vehicles.
        range_of_EVSE (int): The range of electric vehicle supply equipment.
        sim_time (int): The simulation time in minutes.
        number_of_simulations (int): The number of simulations to run.
        ffn_results (str, optional): The file path to save the simulation results. Defaults to None.
        verbose (bool, optional): Whether to print verbose output. Defaults to True.

    Returns:
        pandas.DataFrame: The total simulation results.
    """

    df_total = sim_x_facility_per_evse(
        ev_arrival_rate=ev_arrival_rate,
        energy_req_rate=energy_req_rate,
        range_of_EVSE=range_of_EVSE,
        sim_time=sim_time,
        number_of_simulations=number_of_simulations,
        verbose=verbose,
    )

    if ffn_results is not None:
        # save results of simulation
        df_total.to_csv(
            path_or_buf=ffn_results,
            sep=";",
            index=False,
            header=True,
            decimal=".",
            float_format="%.3f",
        )

    return df_total