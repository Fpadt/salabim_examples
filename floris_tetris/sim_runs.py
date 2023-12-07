# https://www.geeksforgeeks.org/parallel-processing-in-python/
# import multiprocessing as mp

# https://stackoverflow.com/questions/8804830/python-multiprocessing-picklingerror-cant-pickle-type-function
from pathos.multiprocessing import ProcessingPool as Pool

from sim_facility import *

# ------------------------------------------------------------
# function to run simulation X times per EVSE for all EVSE's
# ------------------------------------------------------------


# returns a DataFrame with the results
def sim_facility_with_c_EVSE(
    inter_arr_time_distr,
    energy_request_distr,
    number_of_EVSE,
    sim_time,
    fixed_utilization,
    number_of_simulations,
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
                inter_arr_time_distr=inter_arr_time_distr,
                energy_request_distr=energy_request_distr,
                number_of_EVSE=number_of_EVSE,
                sim_time=sim_time,
                fixed_utilization=fixed_utilization,
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
# processing in parallel
def sim_facility_for_range_of_EVSE(
    inter_arr_time_distr,
    energy_request_distr,
    range_of_EVSE,
    sim_time,
    fixed_utilization,
    number_of_simulations,
    ffn_results=None,
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

    def sim_facility_with_c_EVSE_wrapper(c):
        # Call the original function with all the arguments
        return sim_facility_with_c_EVSE(
            inter_arr_time_distr,
            energy_request_distr,
            c,
            sim_time,
            fixed_utilization,
            number_of_simulations,
            verbose,
        )
    
    # Create a pool of workers
    with Pool() as p:
        results = p.map(sim_facility_with_c_EVSE_wrapper, range_of_EVSE)

    df_total = pd.concat(results)

    # # Initialize an empty list
    # dfs = []

    # return results_df

    # Execute the simulation for each EVSE
    # for c in range_of_EVSE:
    #     # Execute simulation
    #     df = sim_facility_with_c_EVSE(
    #         inter_arr_time_distr=inter_arr_time_distr,
    #         energy_request_distr=energy_request_distr,
    #         number_of_EVSE=c,
    #         sim_time=sim_time,
    #         fixed_utilization=fixed_utilization,
    #         number_of_simulations=number_of_simulations,
    #         verbose=verbose,
    #     )
    #     # Append df to dfs
    #     dfs.append(df)

    # Concatenate all DataFrames in dfs
    # df_total = pd.concat(dfs, axis =0, ignore_index=True)

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


# ------------------------------------------------------------
# Simulate Facitily
# ------------------------------------------------------------

# def simulate_facility(
#         inter_arr_time_distr,
#         energy_request_distr,
#         range_of_EVSE,
#         sim_time,
#         fixed_utilization,
#         number_of_simulations,
#         ffn_results=None,
#         verbose=True,
# ):
#     """
#     Simulates the facility based on the given parameters.

#     Args:
#         ev_arrival_rate (float): The arrival rate of electric vehicles.
#         energy_req_rate (float): The energy request rate of electric vehicles.
#         range_of_EVSE (int): The range of electric vehicle supply equipment.
#         sim_time (int): The simulation time in minutes.
#         number_of_simulations (int): The number of simulations to run.
#         ffn_results (str, optional): The file path to save the simulation results. Defaults to None.
#         verbose (bool, optional): Whether to print verbose output. Defaults to True.

#     Returns:
#         pandas.DataFrame: The total simulation results.
#     """
#     pool = multiprocessing.Pool()
#     result_async = [pool.apply_async(sim_x_facility_per_evse, args = (i, )) for i in
# 					range(10)]
# 	results = [r.get() for r in result_async]
# 	print("Output: {}".format(results))

#     df_total = sim_x_facility_per_evse(
#         inter_arr_time_distr=inter_arr_time_distr,
#         energy_request_distr=energy_request_distr,
#         range_of_EVSE=range_of_EVSE,
#         sim_time=sim_time,
#         fixed_utilization=fixed_utilization,
#         number_of_simulations=number_of_simulations,
#         verbose=verbose,
#     )

#     if ffn_results is not None:
#         # save results of simulation
#         df_total.to_csv(
#             path_or_buf=ffn_results,
#             sep=";",
#             index=False,
#             header=True,
#             decimal=".",
#             float_format="%.3f",
#         )

#     return df_total
