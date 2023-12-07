# Description: This file contains the setup for the simulation

import time as tm # for timing the simulation

# Import the simulation modules
from sim_facility import *
from sim_analysis import *
from sim_runs import *

# https://brandfetch.com/enexis.nl?view=library&library=default&collection=colors
# Enexis colors
ENEXIS_G_0 = "#B6D300"
ENEXIS_G_1 = "#BDDB00"
ENEXIS_G_2 = "#A3C100"
ENEXIS_P_0 = "#DA1369"
ENEXIS_P_1 = "#EE6DAE"
ENEXIS_P_2 = "#DF0073"
ENEXIS_B_0 = "#04296C"

# define a session name based on parameters
def session_name(report_no, sim_evse, sim_time, sim_reps):
    """
    Generate a simulation session name based on the given parameters.

    Args:
        report_no (int): The report number.
        sim_evse (list): The list of EVSE numbers.
        sim_time (int): The simulation time.
        sim_reps (int): The number of simulation repetitions.

    Returns:
        str: The generated simulation session name.
    """
    sim_session_name = (
        "R" + str(report_no) + "_"
        + "EVSE_"
        + str(sim_evse[0])
        + "-"
        + str(sim_evse[-1])
        + "_time_"
        + str(sim_time)
        + "_reps_"
        + str(sim_reps)
        + ".csv"
    )
    return sim_session_name

# define a name for the simulation results
def create_ffn_results(report_no, sim_evse, sim_time, sim_reps):
    """
    Create the full filename of the simulation results.

    Args:
        report_no (int): The report number.
        sim_evse (str): The EVSE identifier.
        sim_time (str): The simulation time.
        sim_reps (int): The number of simulation repetitions.

    Returns:
        str: The full filename of the simulation results.
    """
    ffn_session_name = "./sim_results/" + session_name(report_no, sim_evse, sim_time, sim_reps)
    return ffn_session_name



