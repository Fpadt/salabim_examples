# energy price in euro/kWh for each time period


EP = {
    "00": 0.34,
    "01": 0.34,
    "02": 0.31,
    "03": 0.31,
    "04": 0.31,
    "05": 0.31,
    "06": 0.34,
    "07": 0.35,
    "08": 0.38,
    "09": 0.38,
    "10": 0.36,
    "11": 0.37,
    "12": 0.35,
    "13": 0.34,
    "14": 0.35,
    "15": 0.38,
    "16": 0.38,
    "17": 0.40,
    "18": 0.40,
    "19": 0.38,
    "20": 0.37,
    "21": 0.36,
    "22": 0.36,
    "23": 0.35,
}


def cost(t1, t2, kW, EP) -> float:
    """
    Calculate the cost for a given time interval (t2, t1)
    note: t2 > t1

    Parameters
    ----------
    t2 : float
        End time in hours.
    t1 : float
        Start time in hours.
    kW : float
        Power in kW.
    EP : dict
        Dictionary of energy prices for each time period.
    """
    t2 = t2 % 24 + 1
    t1 = t1 % 24
    cost = statistics.mean(list(EP.values())[t1:t2])
    return (t2 - t1) * kW * cost

EnergyPrice = list(EP.values())

# if p_rnd:
#     EnergyPrice = np.random.uniform(eng_l, eng_h, n)
# else:
#     EnergyPrice = list(EP.values())
    # EnergyPrice = np.linspace(eng_l, eng_h, n)

# if print_energy_price:
#     print(f"\nenergy_price:\n {EnergyPrice}\n")