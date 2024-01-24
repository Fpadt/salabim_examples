import matplotlib
matplotlib.use('TkAgg')


import pandas as pd
from plotnine import ggplot, aes, geom_point
import matplotlib.pyplot as plt



# Generate a DataFrame with some fake data
dfRaw = pd.DataFrame({
    't': range(10),
    'Enexis performance.x': [i**2 for i in range(10)]
})

# Create the plot
plot = (ggplot(dfRaw, aes(x='t', y='Enexis performance.x'))
 + geom_point())

# Display the plot
plot.draw()
plt.show()