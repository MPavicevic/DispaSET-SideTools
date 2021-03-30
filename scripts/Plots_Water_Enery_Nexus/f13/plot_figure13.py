import pandas as pd
import numpy as np
from plotnine import *
import matplotlib as mpl
import seaborn as sns

scenario = 'Baseline'

mix1 = pd.read_csv("data_figure13.csv")
mix_min_max1 = pd.read_csv("data_figure13_minmax.csv")
mix_min_max1['min'] = mix_min_max1['min'] * 100
mix_min_max1['max'] = mix_min_max1['max'] * 100
cat_order = ['BIO', 'GEO', 'NUC', 'PEA', 'OIL', 'GAS', 'HRD', 'WAT', 'SUN', 'WIN']
mix1['fuel_class'] = pd.Categorical(mix1['fuel_class'], categories=cat_order, ordered=True)

if scenario == 'Baseline':
    mix = mix1[mix1['Scenario'] != 'Connected']
    mix_min_max1['Label'] = mix_min_max1['min'].round(1).astype(str) + '% - ' + mix_min_max1['max'].round(1).astype(
        str) + '%'
    mix_min_max = mix_min_max1[mix_min_max1['Scenario'] != "Connected"]
else:
    mix = mix1[mix1['Scenario'] != 'Baseline']
    mix_min_max1['Label'] = mix_min_max1['min'].round(1).astype(str) + '% - ' + mix_min_max1['max'].round(1).astype(
        str) + '%'
    mix_min_max = mix_min_max1[mix_min_max1['Scenario'] != "Baseline"]

mix.reset_index(inplace=True)
mix_min_max.reset_index(inplace=True)

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

g = (ggplot(mix) +
     aes(x=mix['r'], y=mix['fraction'], fill=mix['fuel_class']) +
     geom_bar(stat="identity", width=1, size=0.15, color="black") +
     facet_wrap('region', ncol=3, scales="free_x") +
     scale_y_continuous(labels=lambda l: ["%d%%" % (v * 100) for v in l]) +
     scale_fill_manual(values=fuel_cmap, name="") +
     labs(title = scenario,
          x="Rank (climate years sorted by \n renewable energy generation)",
          y="Share of annual generation (%)",
          fill = 'Fuel') +
     theme_minimal() +
     geom_hline(mix_min_max, aes(yintercept=mix_min_max['max'] / 100), color='white') +
     geom_hline(mix_min_max, aes(yintercept=mix_min_max['min'] / 100), color='white') +
     annotate('text', x=19, y=0.5, color="white", size=10, label=mix_min_max['Label']) +
     theme(axis_text_x=element_text(vjust=0), legend_margin=0, subplots_adjust={'wspace': 0.10, 'hspace': 0.25},
           legend_position=(.5, 0), legend_direction='horizontal') +
     coord_flip() +
     guides(fill = guide_legend(nrow = 1, reverse = True))
     )

g

if scenario == 'Baseline':
    (ggsave(g, "figure13_Baseline.png", width=15.5 / 2.5, height=12 / 2.5))
else:
    (ggsave(g, "figure13_Connected.png", width=15.5 / 2.5, height=12 / 2.5))
