import pandas as pd
import numpy as np
from matplotlib import gridspec
from plotnine import *
import matplotlib.pyplot as plt
import seaborn as sns

toplot = pd.read_csv('data_f20.csv')

# g = (ggplot(toplot) + aes(x=toplot['id'], y=toplot['Congestion']) +
#      geom_area() +
#      facet_grid('Connection ~ Scenario') +
#      scale_x_continuous(breaks=range(1980, 2019, 13)) +
#      ylab("Weekly Net Flow (GWh)") +
#      xlab("Week of the year") +
#      theme_minimal()
#      )
# g


region_cmap = {'CAPP <-> EAPP': '#DF5F47',
               'CAPP <-> SAPP': '#F26C0F',
               'CAPP <-> WAPP': '#8E9A7F',
               'EAPP <-> NAPP': '#644C48',
               'EAPP <-> SAPP': '#D20D56',
               'NAPP <-> WAPP': '#128680'}

g = (ggplot(toplot) + aes(x=toplot['Connection'], y=toplot['Congestion'], color=toplot['Connection']) +
     geom_boxplot(color="black", alpha=0.4, fill=['#DF5F47', '#F26C0F', '#8E9A7F', '#644C48', '#D20D56', '#128680',
                                                  '#DF5F47', '#F26C0F', '#8E9A7F', '#644C48', '#D20D56', '#128680']) +
     facet_grid('Scenario ~', labeller={'Baseline': 'Baseline', 'Connected': 'High Interconnections'}) +
     scale_colour_manual(values=region_cmap, name="Interconnection") +
     geom_jitter(random_state=42, width=0.3) +
     ylab("Congestion (%)") +
     xlab("Interconnections (Both directions)") +
     theme_minimal() +
     theme(panel_border=element_rect(color='black', size=1))
     )
g

ggsave(g, "figure20.png", width=22 / 2.5, height=10 / 2.5)
