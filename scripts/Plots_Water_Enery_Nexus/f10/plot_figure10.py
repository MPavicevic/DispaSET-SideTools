import pandas as pd
import numpy as np
from plotnine import *
import matplotlib as mpl
import seaborn as sns

region_cmap = {'CAPP': '#FFBE00',
               'EAPP': '#BF008E',
               'NAPP': '#089701',
               'SAPP': '#E51A1D',
               'WAPP': '#1C75FE'}
region_order = ['WAPP', 'SAPP', 'NAPP', 'EAPP', 'CAPP']

technology_cmap = {'HDAM': '#00a0e1ff',
                   'HPHS': 'blue',
                   'SCSP': 'yellow'
                   }


pp = pd.read_csv("data_figure10.csv")
pp['Region'] = pd.Categorical(pp['Region'], categories=region_order, ordered=True)

# g = (ggplot(pp) + aes(x=pp['Technology'], y=pp['share'], fill=pp['Region']) +
#      geom_bar(stat="identity") +
#      labs(y="Share (%)") +
#      geom_text(aes(y = pp['position'], label=pp['label'])) +
#      scale_fill_manual(values=region_cmap, name="Power Pool") +
#      scale_y_continuous(labels=lambda l: ["%d%%" % (v * 100) for v in l]) +
#      coord_flip() +
#      theme_minimal()
#      )
#
# g

g = (ggplot(pp) + aes(x=pp['Region'], y=pp['share2'], fill=pp['Technology']) +
     geom_bar(stat="identity") +
     # facet_grid('Region ~') +
     geom_text(aes(y = pp['position2'], label=pp['label2'])) +
     labs(y="Share (%)") +
     scale_fill_manual(values=technology_cmap, name="Technology") +
     scale_y_continuous(labels=lambda l: ["%d%%" % (v * 100) for v in l]) +
     coord_flip() +
     theme_minimal()
     )

g


ggsave(g, "figure10_2.png", width=15.5/2.5, height=6/2.5)
