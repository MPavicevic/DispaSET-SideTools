import pandas as pd
import numpy as np
from matplotlib import gridspec
from plotnine import *
import matplotlib.pyplot as plt
import seaborn as sns

region_cmap = {'Africa': 'grey',
               'CAPP': '#FFBE00',
               'EAPP': '#BF008E',
               'NAPP': '#089701',
               'SAPP': '#E51A1D',
               'WAPP': '#1C75FE'}
region_order = ['WAPP', 'SAPP', 'NAPP', 'EAPP', 'CAPP']

data = pd.read_csv('data_figure22.csv')
data_1 = pd.read_csv('data_figure22_1.csv')
data_1.loc[:,'Level'] = data_1.loc[:,'Level']/1e6

toplot = data[data['Scenario'] != 'Connected']
toplot = toplot[toplot['id'] != 2000]
toplot = toplot[toplot['id'] != 1981]
toplot.reset_index(inplace=True)
toplot.loc[:,'Level']=toplot.loc[:,'Level']/1e6

g = (ggplot() +
     geom_area(toplot, aes(x=toplot['Week'], y=toplot['Level'], fill=toplot['Region'])) +
     facet_wrap('id', ncol=2) +
     geom_line(data_1, aes(x=data_1['Week'], y=data_1['Level'])) +
     scale_fill_manual(values=region_cmap, name="Power Pool") +
     labs(
         x="Week of the year",
         y="Stored Energy (TWh)"
     ) +
     theme_minimal()
     # theme(legend_position = "bottom")
     )


g

(ggsave(g, "figure22.png", width=15.5 / 2.5, height=8 / 2.5))