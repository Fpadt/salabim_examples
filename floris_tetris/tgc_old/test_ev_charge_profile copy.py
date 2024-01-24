from scipy.optimize import fsolve
import numpy as np

def cv_pwr(t: float, pm: float, k: float) -> float:
    """
    Calculate the charging power for a given time.

    Parameters
    ----------
    t : float
        Time in hours.
    pm : float
        Maximum power input of the EV in kW.
    k : float
        Charging curve constant.
        0.01-0.03 charge aggressively,
        0.05-0.1  prioritizing battery health and longevity
    """
    return pm * np.exp(-k * t)


def cv_eng(t2, t1, pm, k) -> float:
    """
    Calculate the charging energy for a given time interval (t2, t1)
    note: t2 > t1

    Parameters
    ----------
    t2 : float
        End time in hours.
    t1 : float
        Start time in hours.
    pm : float
        Maximum power input of the EV in kW.
    k : float
        Charging curve constant.
        0.01-0.03 charge aggressively,
        0.05-0.1  prioritizing battery health and longevity
    """
    return (-1 / k) * (cv_pwr(t2, pm, k) - cv_pwr(t1, pm, k))


# def cv_pwr_avg(t2, t1, pm, k) -> float:
#     return cv_eng(t2, t1, pm, k) / (t2 - t1)


def charge_profile(
    dur: float,
    soc: float,
    dsc: float,
    cap: float,
    mpi: float,
    mpo: float,
    deg: float,
) -> list:
    """
    Calculate the charging profile for a given EV.

    Parameters
    ----------
    dur : float
        Duration of stay in hours.
    soc : float
        State of charge of the battery in %.
    dsc : float
        Desired state of charge of the battery in %.
    cap : float
        Capacity of the battery in kWh.
    mpi : float
        Maximum power input of the EV in kW.
    mpo : float
        Maximum power output of the EVSE in kW.
    deg : float
        Charging curve constant.
        0.01-0.03 charge aggressively,
        0.05-0.1  prioritizing battery health and longevity

    Returns
    -------
    list
        List of the charging profile in the format [time, power, charge].
    """
    # --------------------------------------------------------------------------
    # Calculate the charging profile
    # https://www.homechargingstations.com/ev-charging-time-calculator/
    # --------------------------------------------------------------------------
    # Calculate the charge required to reach the desired capacity
    k = deg
    
    cv = 0.8 * cap  #                                charging curve flattens at cap.
    dc = dsc * cap  #                                soc + charge [kWh] required
    mp = min(mpi, mpo)  #                      max power [kW] for charging

    # current charge
    uc0 = soc * cap  #                                charge [kWh] at entry
    up0 = mp  #                                       max power [kW] at entry
    ut0 = uc0 / up0  #                                time required for charge at entry

    # first part of charge < 80% of cap
    uc1 = max(min(dc, cv) - min(uc0, cv), 0)  #      charge [kWh] required
    up1 = 0 if uc1 == 0 else mp  #                   max power [kW] for charging
    ut1 = 0 if uc1 == 0 else uc1 / up1  #            time [h] required
    # constrainted by duration
    ct1 = min(dur, ut1)  #                           time constrainted by duration
    cp1 = up1  #                                     max power [kW] for charging
    cc1 = ct1 * cp1  #                               charge constrainted by duration

    # second part of charge > 80% of cap
    uc2 = max(max(dc, cv) - max(uc0, cv), 0)  #      charge [kWh] required
    up2 = 0  #                                       initial power [kW] required
    ut2 = 0  #                                       initial time [h] required
    ct2 = 0  #                                       time constrainted by duration
    cp2 = 0  #                                       max power [kW] for charging
    cc2 = 0  #                                       charge constrainted by duration
    cp3 = 0  #                                       max power [kW] for charging
    cc3 = 0  #                                       charge constrainted by duration

    # Define the function for the given equation with specific ta, pm and k
    def zero_for_E(t2, t1, pm, k, E) -> float:
        """
        function to solve the root of the equation, so where it is 0

        Parameters
        ----------
        t2 : float
            End time in hours.
        t1 : float
            Start time in hours.
        pm : float
            Maximum power input of the EV in kW.
        k : float
            Charging curve constant.
            0.01-0.03 charge aggressively,
            0.05-0.1  prioritizing battery health and longevity
        E : float
            Energy in kWh to be charged
        """
        return cv_eng(t2, t1, pm, k) - E

    # determime time and power for 2nd part of charge CV
    if uc2 > 0:
        # Solve the equation numerically
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.fsolve.html
        solution = fsolve(func=zero_for_E, x0=ut1, args=(0, mp, k, uc2), xtol=1e-3)

        ut2 = solution[0]  #                         time [h] required during CV
        up2 = cv_pwr(ut2, mp, k)  #                  power [kW] at the end

        ct2 = max(0, min(dur - ut1, ut2))  #         real time [h] during CV

        if ct2 > 0:
            cc2 = cv_eng(ct2, 0, mp, k)  #           charge [kWh] during CV
            cp2 = cp1  # cv_pwr(ct2, mp, k)  #       real power [kW] at the end

    # --------------------------------------------------------------------------
    e2 = 0 if ut2 == 0 else float(zero_for_E(t2=ut2, t1=0, pm=mp, k=k, E=uc2))
    # --------------------------------------------------------------------------
    # Calculate the charging profile if more time is available
    ut3 = max(0, dur - (ut1 + ut2))  #               slack time [h] for parking
    ct3 = ut3  #                                     real slack time [h] for parking

    if ct3 > 0:
        cc3 = cv_eng(ct3, 0, mp, k)  #               charge [kWh] during CV
        cp3 = cp1  # cv_pwr(ct3, mp, k)  #           real power [kW] at the end

    return {
        "params": {
            "dur": dur,
            "soc": soc,
            "dsc": dsc,
            "cap": cap,
            "mxp": mp,
            "k": k,
        },
        "phase0": {"c0": uc0, "t": ut0, "p": up0},
        "phase1": {"c1": uc1, "t": ut1, "p": up1},
        "real_1": {"c1": cc1, "t": ct1, "p": cp1},  # + ut3
        "phase2": {"c2": uc2, "t": ut1 + ut2, "p": up2},
        "real_2": {"c2": cc2, "t": ct1 + ct2, "p": cp2},  # + ut3
        "real_3": {"c3": cc3, "t": ct1 + ct2 + ct3, "p": cp3},
        "result": {
            "ufc": uc0 + uc1 + uc2 + e2,
            "cfc": uc0 + cc1 + cc2 + e2,
            "rem": cc1 + cc2 + e2,
            "dec": dc,
            "err": dc - (uc0 + uc1 + uc2 + e2),
        },
        "tslots": {"t1": ut1, "T1": ct1, "t2": ut2, "T2": ct2, "t3": ut3, "T3": ut3},
    }