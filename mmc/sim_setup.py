# Description: This file contains the setup for the simulation

import time as tm # for timing the simulation

from sim_facility import *
from sim_analysis import *

# https://brandfetch.com/enexis.nl?view=library&library=default&collection=colors

ENEXIS_G_0 = "#B6D300"
ENEXIS_G_1 = "#BDDB00"
ENEXIS_G_2 = "#A3C100"
ENEXIS_P_0 = "#DA1369"
ENEXIS_P_1 = "#EE6DAE"
ENEXIS_P_2 = "#DF0073"
ENEXIS_B_0 = "#04296C"

def session_name(report_no, sim_evse, sim_time, sim_reps):
    # Create a string with the simulation session name
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

def create_ffn_results(report_no, sim_evse, sim_time, sim_reps):
    # Create a string with the full filename of the simulation results
    ffn_session_name = "./sim_results/" + session_name(report_no, sim_evse, sim_time, sim_reps    )
    return ffn_session_name



