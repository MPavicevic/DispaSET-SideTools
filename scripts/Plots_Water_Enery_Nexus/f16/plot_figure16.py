import pandas as pd
import numpy as np
from matplotlib import gridspec
from plotnine import *
import matplotlib.pyplot as plt
import seaborn as sns

toplot_01 = pd.read_csv("data_figure16_01.csv")
qq_01 = pd.read_csv("data_figure16_qq_01.csv")

toplot_01['label_CE'] = toplot_01['label_CE'].astype('Int64')
toplot_01['label_CS'] = toplot_01['label_CS'].astype('Int64')
toplot_01['label_CW'] = toplot_01['label_CW'].astype('Int64')
toplot_01['label_EN'] = toplot_01['label_EN'].astype('Int64')
toplot_01['label_ES'] = toplot_01['label_ES'].astype('Int64')
toplot_01['label_NW'] = toplot_01['label_NW'].astype('Int64')

toplot_01 = toplot_01[toplot_01['id'] != 2000]

adjust_text_dict = {
    # 'expand_points': (2, 2),
    'ha':'center',
    'va':'center',
    # 'arrowprops': {
    #     'arrowstyle': '->',
    #     'color': 'red'
    # }
}

g1 = (ggplot(toplot_01) +
      aes(x=toplot_01['e_CAPP'], y=toplot_01['e_EAPP']) +
      geom_point(aes(colour='factor(color_CE)'), show_legend=False) +
      scale_colour_manual(values=['grey', 'blue', 'green','red']) +
      geom_text(aes(label=toplot_01['label_CE']), nudge_x=0.2, nudge_y=1, size=10, adjust_text=adjust_text_dict) +
      guides(alpha=0.5) +
      geom_hline(aes(yintercept=qq_01['EAPP']), data=qq_01, linetype='dotted', color='black') +
      geom_vline(aes(xintercept=qq_01['CAPP']), data=qq_01, linetype='dotted', color='black') +
      theme_minimal()
      )

g2 = (ggplot(toplot_01) +
      aes(x=toplot_01['e_CAPP'], y=toplot_01['e_SAPP']) +
      geom_point(aes(colour='factor(color_CS)'), show_legend=False) +
      scale_colour_manual(values=['grey', 'blue', 'green','red']) +
      geom_text(aes(label=toplot_01['label_CS']), nudge_x=0.2, nudge_y=1.2, size=10, adjust_text=adjust_text_dict) +
      guides(alpha=False) +
      geom_hline(aes(yintercept=qq_01['SAPP']), data=qq_01, linetype='dotted', color='black') +
      geom_vline(aes(xintercept=qq_01['CAPP']), data=qq_01, linetype='dotted', color='black') +
      theme_minimal()
      )

g3 = (ggplot(toplot_01) +
      aes(x=toplot_01['e_CAPP'], y=toplot_01['e_WAPP']) +
      geom_point(aes(colour='factor(color_CW)'), show_legend=False) +
      scale_colour_manual(values=['grey', 'blue', 'green','red']) +
      geom_text(aes(label=toplot_01['label_CW']), nudge_x=0.2, nudge_y=0.8, size=10, adjust_text=adjust_text_dict) +
      guides(alpha=False) +
      geom_hline(aes(yintercept=qq_01['WAPP']), data=qq_01, linetype='dotted', color='black') +
      geom_vline(aes(xintercept=qq_01['CAPP']), data=qq_01, linetype='dotted', color='black') +
      theme_minimal()
      )

g4 = (ggplot(toplot_01) +
      aes(x=toplot_01['e_EAPP'], y=toplot_01['e_NAPP']) +
      geom_point(aes(colour='factor(color_EN)'), show_legend=False) +
      scale_colour_manual(values=['grey', 'blue', 'green','red']) +
      geom_text(aes(label=toplot_01['label_EN']), nudge_x=0.2, nudge_y=0.1, size=10, adjust_text=adjust_text_dict) +
      guides(alpha=False) +
      geom_hline(aes(yintercept=qq_01['NAPP']), data=qq_01, linetype='dotted', color='black') +
      geom_vline(aes(xintercept=qq_01['EAPP']), data=qq_01, linetype='dotted', color='black') +
      theme_minimal()
      )

g5 = (ggplot(toplot_01) +
      aes(x=toplot_01['e_EAPP'], y=toplot_01['e_SAPP']) +
      geom_point(aes(colour='factor(color_ES)'), show_legend=False) +
      scale_colour_manual(values=['grey', 'blue', 'green','red']) +
      geom_text(aes(label=toplot_01['label_ES']), nudge_x=0.2, nudge_y=1, size=10, adjust_text=adjust_text_dict) +
      guides(alpha=False) +
      geom_hline(aes(yintercept=qq_01['SAPP']), data=qq_01, linetype='dotted', color='black') +
      geom_vline(aes(xintercept=qq_01['EAPP']), data=qq_01, linetype='dotted', color='black') +
      theme_minimal()
      )

g6 = (ggplot(toplot_01) +
      aes(x=toplot_01['e_NAPP'], y=toplot_01['e_WAPP']) +
      geom_point(aes(colour='factor(color_NW)'), show_legend=False) +
      scale_colour_manual(values=['grey', 'blue', 'green','red']) +
      geom_text(aes(label=toplot_01['label_NW']), nudge_x=0.2, nudge_y=0.8, size=10, adjust_text=adjust_text_dict) +
      guides(alpha=False) +
      geom_hline(aes(yintercept=qq_01['WAPP']), data=qq_01, linetype='dotted', color='black') +
      geom_vline(aes(xintercept=qq_01['NAPP']), data=qq_01, linetype='dotted', color='black') +
      theme_minimal()
      )

# Empty plotnine figure to place the subplots on. Needs junk data (for backend "copy" reasons).
fig = (ggplot() + geom_blank() + theme_void()).draw()
# fig = plt.figure()

# Create gridspec for adding subpanels to the blank figure
gs = gridspec.GridSpec(2, 3)
ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])
ax3 = fig.add_subplot(gs[0, 2])
ax4 = fig.add_subplot(gs[1, 0])
ax5 = fig.add_subplot(gs[1, 1])
ax6 = fig.add_subplot(gs[1, 2])

ax1.set_xlabel("CAPP")
ax1.set_ylabel("EAPP")
ax2.set_xlabel("CAPP")
ax2.set_ylabel("SAPP")
ax2.set_title('Hydro Generation (TWh)')
ax3.set_xlabel("CAPP")
ax3.set_ylabel("WAPP")
ax4.set_xlabel("EAPP")
ax4.set_ylabel("NAPP")
ax5.set_xlabel("EAPP")
ax5.set_ylabel("SAPP")
ax6.set_xlabel("NAPP")
ax6.set_ylabel("WAPP")

# Add subplots to the figure
_ = g1._draw_using_figure(fig, [ax1])
_ = g2._draw_using_figure(fig, [ax2])
_ = g3._draw_using_figure(fig, [ax3])
_ = g4._draw_using_figure(fig, [ax4])
_ = g5._draw_using_figure(fig, [ax5])
_ = g6._draw_using_figure(fig, [ax6])

fig.show()

fig.savefig("figure16.png")
