import pandas as pd
import numpy as np
from matplotlib import gridspec
from plotnine import *
import matplotlib.pyplot as plt
import seaborn as sns

region_cmap = {'CAPP': '#FFBE00',
               'EAPP': '#BF008E',
               'NAPP': '#089701',
               'SAPP': '#E51A1D',
               'WAPP': '#1C75FE'}
region_order = ['WAPP', 'SAPP', 'NAPP', 'EAPP', 'CAPP']

sel = pd.read_csv("data_figure17.csv")
sel['Location'] = pd.Categorical(sel['Location'], categories=region_order, ordered=True)
sel['category'] = pd.factorize(sel['Location'])[0] + 1

def percentile(n):
    def percentile_(x):
        return x.quantile(n)

    percentile_.__name__ = 'percentile_{:2.0f}'.format(n * 100)
    return percentile_


grouped_sel = sel.groupby(['label_tech', 'Location']).agg(
    {'OutputPower': ['min', percentile(0.25), percentile(0.75), 'max']})
grouped_sel.reset_index(inplace=True)
grouped_sel.columns = ['label_tech', 'Location', 'min', 'q25', 'q75', 'max']
for p in grouped_sel['Location']:
    grouped_sel.loc[grouped_sel['Location']==p,'category'] = sel.loc[sel['Location']==p]['category'].mean()
grouped_sel.sort_values(by=['category', 'label_tech'], ascending=[True, False], inplace=True)
grouped_sel['label'] = sel['label'].unique()

sel_ror=sel.loc[sel['label_tech']=='Run-of-river']
sel_dam=sel.loc[sel['label_tech']!='Run-of-river']

g1 = (ggplot(data=sel_ror, mapping=aes(y=sel_ror['OutputPower'], x=sel_ror['Location'], colour=sel_ror['Location'])) +
     geom_boxplot(color="black",alpha=0.4, fill=['#1C75FE','#E51A1D','#089701','#BF008E','#FFBE00']) +
     geom_jitter(random_state=42, width=0.2) +
     scale_colour_manual(values=region_cmap, name="Region") +
     labs(title="Run-of-river") + ylab('Output Power [TWh]') + xlab('Power Pool') +
     theme_minimal() +
     theme(subplots_adjust={'right': 0.85}) +
     coord_flip()
     )

g2 = (ggplot(data=sel_dam, mapping=aes(y=sel_dam['OutputPower'], x=sel_dam['Location'], colour=sel_dam['Location'])) +
     geom_boxplot(color="black",alpha=0.4, fill=['#1C75FE','#E51A1D','#089701','#BF008E','#FFBE00']) +
     geom_jitter(random_state=42, width=0.2) +
     scale_colour_manual(values=region_cmap, name="Region") +
     labs(title="Storage and Pumping") + ylab('Output Power [TWh]') + xlab('Power Pool') +
     theme_minimal() +
     theme(subplots_adjust={'right': 0.85}) +
     coord_flip()
     )


ggsave(g1, "figure17a.png", width=7.7/2.5, height=6/2.5)
ggsave(g2, "figure17b.png", width=7.7/2.5, height=6/2.5)




# New
fig, ax = plt.subplots()
fig._themeable = {}

#
gs = gridspec.GridSpec(1, 2)
ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])

_ = g1._draw_using_figure(fig, [ax1])
_ = g2._draw_using_figure(fig, [ax2])

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.tick_params(axis='x', colors='white', grid_alpha=0)
ax.patch.set_alpha(0)
ax.axes.get_yaxis().set_visible(False)



fig.set_figheight(2.5)
# fig.set_figwidth(6.5)

fig.show()

fig.savefig("figure17.png")



fig = plt.figure(figsize=(8,3))
# fig = plt.figure()
fig._themeable = {}
ax1 = fig.add_subplot(1,2,1)
ax2 = fig.add_subplot(1,2,2)

_ = g1._draw_using_figure(fig, [ax1])
_ = g2._draw_using_figure(fig, [ax2])

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.tick_params(axis='x', colors='white', grid_alpha=0)
ax.patch.set_alpha(0)
ax.axes.get_yaxis().set_visible(False)

plt.tight_layout()

fig.show()

fig.savefig("figure17.png")
