from tgc_floris_padt.test_ev_charge_profile import *

tst= charge_profile(
    dur= 10,
    soc= 0,
    dsc=1,
    cap=70,
    ev_mpi=7,
    se_mpo=7,
    k=0.075
)

print(tst)