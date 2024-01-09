from scipy.optimize import fsolve
import numpy as np
import pandas as pd
from openpyxl import Workbook
from datetime import datetime
import statistics
import os
import ntpath

np.random.seed(42)

m = 20  #                   number of EVSEs
n = 60  #                   time periods in the future (can become less)
r = 0.5  #                  factor of Enexis grid connection

# --------------------------------------------------------------------------
# The array's for all EV's & SE together and the resulting minimum.
# EV = np.random.choice([EV_MPI, EV_MPI / 2, 3.33, 3.33 / 2], size=(m, n))
# SE = np.random.choice([SE_MPO], size=(m, n))
# EVSE = np.minimum(EV, SE)


SE_MPO = 7  #               EVSE max Power output for each time period
EV_MPI = 7  #               EV max Power input for each time period
EX_MPO = m * r * SE_MPO  #  enexis max Power output for each time period (constant)
CAP = 70  #                 EV max capacity of battery
K = 0.075  #                EV battery degradation cost per kWh
# --------------------------------------------------------------------------

soc_l = 0.0  #              lower bound of state of charge
soc_h = 0.2  #              upper bound of state of charge
d_c_l = 0.4  #              lower bound of desired charge
d_c_h = 1.0  #              upper bound of desired charge
dur_l = 1.0  #              lower bound of parking duration
dur_h = 8.0  #              upper bound of parking duration
eng_l = 0.3  #              lower bound of energy price
eng_h = 0.6  #              upper bound of energy price
p_rnd = True  #             will energyprice be random of linear

alpha = 1.0  #              EVSE efficiency
beta = 1.0  #               customer satisfaction
gamma = 1.0  #              cost of energy

# --------------------------------------------------------------------------
print_solver_outcome = False
print_EVSE_power = False

print_session_max_charge = False
print_remaining_charge = False

print_parking_time = False
print_energy_price = False

print_tee = False

# Set the solver to be used
# solver = "ipopt" #        m 50 EVSE's, > 50 time periods
# solver = "mosek" #        m 50 EVSE's, > 50 time periods
# solver = "cplex"  #       m 50 EVSE's, 18 time periods
solver = "glpk"  #          m 50 EVSE's, > 50 time periods
# solver = "gurobi" #       m xx EVSE's, 19 time periods - no license yet