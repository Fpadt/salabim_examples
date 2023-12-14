import scipy.stats as stats
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv("Distribution/CSV/open_transactions.csv", sep=";", decimal=",")
data = df["TotalEnergy"]

fit_alpha, fit_loc, fit_beta = stats.gamma.fit(data)
print(fit_alpha, fit_loc, fit_beta)

# Generate x values
x = np.linspace(min(data), max(data), 1000)

# Generate the gamma distribution for these x values
gamma_distribution = stats.gamma.pdf(x, fit_alpha, loc=fit_loc, scale=fit_beta)

# Plot the histogram
plt.hist(data, bins=100, density=True)

# Plot the gamma distribution
plt.plot(x, gamma_distribution, "r-")

# Show the plot
plt.show()
