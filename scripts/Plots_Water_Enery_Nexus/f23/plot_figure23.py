import pandas as pd
import numpy as np
from matplotlib import gridspec
from plotnine import *
import matplotlib.pyplot as plt
import seaborn as sns

toplot = pd.read_csv('data_figure23.csv')

toplot['Min_1'] = toplot['Min'].mask(toplot['Min'].gt(0), 0)
toplot['q1_1'] = toplot['q1'].mask(toplot['q1'].gt(0), 0)
toplot['qm_1'] = toplot['q_m'].mask(toplot['q_m'].gt(0), 0)
toplot['q3_1'] = toplot['q3'].mask(toplot['q3'].gt(0), 0)
toplot['Max_1'] = toplot['Max'].mask(toplot['Max'].gt(0), 0)

toplot['Min_2'] = toplot['Min'].mask(toplot['Min'].lt(0), 0)
toplot['q1_2'] = toplot['q1'].mask(toplot['q1'].lt(0), 0)
toplot['qm_2'] = toplot['q_m'].mask(toplot['q_m'].lt(0), 0)
toplot['q3_2'] = toplot['q3'].mask(toplot['q3'].lt(0), 0)
toplot['Max_2'] = toplot['Max'].mask(toplot['Max'].lt(0), 0)

# g = (ggplot(toplot) + aes(x=toplot['Week'], y=toplot['NetFlow'], fill=toplot['Sign'].astype(object)) +
#      geom_ribbon(aes(ymin=toplot['Min'],ymax=toplot['Max'])) +
#      geom_line(aes(y=toplot['NetFlow'])) +
#      scale_fill_manual(values=['green', 'red'],
#                        labels=['Exports', 'Imports']) +
#
#
#      facet_grid('Scenario ~ Zone', scales="free_x") +
#      geom_hline(yintercept=0) +
#      scale_x_continuous(breaks=range(1, 53, 10)) +
#      ylab("Weekly Net Flow (GWh)") +
#      xlab("Week of the year") +
#      theme_minimal()
#      )
#
# g

g = (ggplot(toplot) + aes(x=toplot['Week'], y=toplot['q_m']) +
     # geom_ribbon(aes(ymin=toplot['Min_1'],ymax=toplot['Max_1']), fill='Red') +
     # geom_ribbon(aes(ymin=toplot['Min_2'],ymax=toplot['Max_2']), fill='Green') +
     geom_ribbon(aes(ymin=toplot['Min_1'], ymax=toplot['q1_1']), fill='Green', alpha=0.3) +
     geom_ribbon(aes(ymin=toplot['q1_1'], ymax=toplot['qm_1']), fill='Green', alpha=0.7) +
     geom_ribbon(aes(ymin=toplot['qm_1'], ymax=toplot['q3_1']), fill='Green', alpha=0.7) +
     geom_ribbon(aes(ymin=toplot['q3_1'], ymax=toplot['Max_1']), fill='Green', alpha=0.3) +
     geom_ribbon(aes(ymin=toplot['Min_2'], ymax=toplot['q1_2']), fill='Red', alpha=0.3) +
     geom_ribbon(aes(ymin=toplot['q1_2'], ymax=toplot['qm_2']), fill='Red', alpha=0.7) +
     geom_ribbon(aes(ymin=toplot['qm_2'], ymax=toplot['q3_2']), fill='Red', alpha=0.7) +
     geom_ribbon(aes(ymin=toplot['q3_2'], ymax=toplot['Max_2']), fill='Red', alpha=0.3) +
     geom_line(aes(y=toplot['q_m'])) +
     facet_grid('Scenario ~ Zone', scales="free_x",
                labeller={'Baseline': 'Baseline', 'Connected': 'High Interconnections'}) +
     geom_hline(yintercept=0) +
     scale_x_continuous(breaks=range(1, 53, 10)) +
     ylab("Weekly Net Flow (GWh)") +
     xlab("Week of the year") +
     # scale_y_continuous(trans="symlog") +
     theme_minimal()
     )

g

ggsave(g, "figure23.png", width=20 / 2.5, height=10 / 2.5)
