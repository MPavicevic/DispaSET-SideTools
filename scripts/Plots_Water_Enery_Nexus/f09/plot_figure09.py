import pandas as pd
import numpy as np
from plotnine import *
import matplotlib as mpl
import seaborn as sns

toplot = pd.read_csv("data_figure09.csv")
# cat_order = ['Other', 'Biomass', 'Fossil_fuels', 'Nuclear', 'Hydro', 'Wind', 'Solar']
cat_order = ['BIO', 'GEO', 'PEA', 'OIL', 'GAS', 'HRD', 'NUC', 'WAT', 'SUN', 'WIN']
toplot['fuel_type'] = pd.Categorical(toplot['fuel_type'], categories=cat_order, ordered=True)

# fuel_cmap = {'Fossil_fuels': '#c781b2',
#              'Solid_fuels': '#c781b2',
#              'Solid fuels': '#c781b2',
#              'Fossil fuels': '#c781b2',
#              'Nuclear': '#466eb4ff',
#              'Other': '#facdd0',
#              'Gas': '#d7642dff',
#              'Wind': '#c9cf5c',
#              'Hydro': '#00a0e1ff',
#              'Solar': '#e6a532',
#              'Biomass': '#7daf4bff'}

fuel_cmap = {'LIG': '#af4b9180', 'PEA': '#af4b9199', 'HRD': 'darkviolet', 'OIL': 'magenta',
             'GAS': '#d7642dff',
             'NUC': '#466eb4ff',
             'SUN': '#e6a532ff',
             'WIN': '#41afaaff',
             'WAT': '#00a0e1ff',
             'BIO': '#7daf4bff', 'GEO': '#7daf4bbf',
             'Storage': '#b93c46ff', 'FlowIn': '#b93c46b2', 'FlowOut': '#b93c4666',
             'OTH': '#b9c33799', 'WST': '#b9c337ff',
             'HDAM': '#00a0e1ff',
             'HPHS': 'blue',
             'THMS': '#C04000ff',
             'BATS': '#41A317ff',
             'BEVS': '#b9c33799'}

g = (ggplot(toplot) + aes(x=toplot['Region'], y=toplot['Share'], fill=toplot['fuel_type']) +
     geom_bar(stat="identity") +
     labs(y="Share (%)", x="Power Pool") +
     scale_fill_manual(values=fuel_cmap, name="Fuel") +
     scale_y_continuous(labels=lambda l: ["%d%%" % (v * 100) for v in l]) +
     coord_flip() +
     theme_minimal()
     )

g

ggsave(g, "figure09.png", width=15.5/2.5, height=6/2.5)
