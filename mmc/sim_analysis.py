# analysis functions for simulation results
import pandas as pd
import scipy.stats as st
import numpy as np

# student-t distribution
# https://en.wikipedia.org/wiki/Student%27s_t-distribution#Table_of_selected_values
# https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.t.html
def t_sd(df, col, confidence_interval, sides="both", decimals=3):
    if sides != "both":
        ci = confidence_interval
    else:
        ci = confidence_interval + (1 - confidence_interval) / 2

    # column of interest
    x = df[col]

    # number of SD for confidence interval 
    # Note: ddof=1 for sample
    tdst = st.t.ppf(ci, df=len(x) - 1)

    return pd.DataFrame(
        {
            "c": df["c"].unique()[0],
            "name": col,
            "mean": x.mean().round(decimals),
            "lbnd": (x.mean() - tdst * x.std(ddof=1) / np.sqrt(len(x))).round(decimals),
            "ubnd": (x.mean() + tdst * x.std(ddof=1) / np.sqrt(len(x))).round(decimals),
            "stdv": x.std(ddof=1).round(decimals),
            "tdst": tdst.round(decimals),
            "runs": len(x),
        },
        index=[0],
    )


# Calculate mean and confidence interval for waiting time
# df_evse = df_sim.groupby('c')['Wq'].agg(['mean', 'count']).reset_index()

# def mean_confidence_interval(data, confidence=0.95):
#     a = 1.0 * np.array(data)
#     n = len(a)
#     # m, se = np.mean(a), scipy.stats.sem(a)
#     m, se = np.mean(a), st.t.interval(confidence, n - 1, loc=np.mean(a), scale=st.sem(a))
#     return m, se


def sim_mean_and_ci(df_sim, col):
    # Calculate the mean and count for each 'c' group

    res = []
    for c in df_sim["c"].unique():
        df_evse = df_sim[df_sim["c"] == c]

        res.append(
            t_sd(df_evse, col, confidence_interval=0.95, sides="both", decimals=2)
        )

    # return results
    return pd.concat(res, axis=0, ignore_index=True)

def get_mean_with_ci(df_sim):
    # Create an empty DataFrame to store the results
    res = []

    # Loop over each column in the DataFrame
    for column in ['lambda', 'mu', 'RO', 'P0', 'Lq', 'Wq', 'Ls', 'Ws']:
        # Apply the function to the column and store the result
        res.append(sim_mean_and_ci(df_sim, df_sim[column].name))

    return pd.concat(res, axis=0, ignore_index=True)

def get_sim_summary(df_sim, output=False):
    # get the index
    idx = 'c'

    # aggregate to get the means
    df_res = get_mean_with_ci(df_sim)

    # get the maximum number of runs
    max_runs = df_res['runs'].max()

    # pivot the results
    df_pivot = (
        df_res.pivot(columns="name", values="mean", index=idx)
        .assign(runs=max_runs)
        [["lambda", "mu", "RO", "P0", "Lq", "Wq", "Ls", "Ws", "runs" ]]
        )
    # df_pivot.index.name = None
    df_pivot = df_pivot.reset_index().rename(columns={'index': idx})

    # print the results
    if output == True:
        print(df_pivot.to_string(index=False))

    # return the results
    return df_pivot
