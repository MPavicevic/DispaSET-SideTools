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

adjust_text_dict = {
    # 'expand_points': (1.8, 2),
    'ha': 'center',
    'va': 'center',
}

data = pd.read_csv('data_fig_WEI_zonal.csv')
data1 = data[data['Variable'] != 'Thermal'].reset_index()

g = (ggplot(data1) + aes(y=data1['WEI_Abs'], x=data1['WEI+'], color=data1['Pool']) +
     geom_point(alpha=0.25, size=3) +
     facet_wrap('Scenario', ncol=2, scales="free_x", labeller={'Baseline':'Baseline', 'Connected':'High Interconnections'}) +
     scale_color_manual(values=region_cmap, name="") +
     # scale_colour_manual(values="grey", name="") +
     labs(y='$WEI^{Abs}$', x='$WEI^{+}$',
          color='Power Pool') +
     scale_y_log10(limits=(0.000000001,150)) +
     scale_x_log10(limits=(0.000000001,10)) +
     geom_hline(yintercept=1, linetype='dotted', color='blue') +
     geom_hline(yintercept=5, linetype='dotted', color='red') +
     geom_vline(xintercept=0.2, linetype='dotted', color='blue') +
     geom_vline(xintercept=1, linetype='dotted', color='red') +
     geom_label(aes(label=data1['Label']), size=8,adjust_text=adjust_text_dict) +
     theme_minimal() +
     theme(panel_border=element_rect(color='black', size=1))
     )

g

(ggsave(g, "figureWEI_Tot.png", width=15.5 / 2.5, height=7 / 2.5))

g3 = (ggplot(data1) + aes(y=data1['WEI_AbsInt'], x=data1['WEI+_Int'], color=data1['Pool']) +
     geom_point(alpha=0.35) +
     facet_wrap('Scenario', ncol=2, scales="free_x", labeller={'Baseline':'Baseline', 'Connected':'High Interconnections'}) +
     scale_colour_manual(values=region_cmap, name="") +
     labs(y='$WEI^{Abs}_{Int}$', x='$WEI^{+}_{Int}$',
          color='Power Pool') +
     scale_y_log10(limits=(0.000000001,150)) +
     scale_x_log10(limits=(0.000000001,10)) +
      geom_hline(yintercept=1, linetype='dotted', color='blue') +
      geom_hline(yintercept=5, linetype='dotted', color='red') +
      geom_vline(xintercept=0.2, linetype='dotted', color='blue') +
      geom_vline(xintercept=1, linetype='dotted', color='red') +
     geom_label(aes(label=data1['Label']), size=8,adjust_text=adjust_text_dict) +
     theme_minimal() +
     theme(panel_border=element_rect(color='black', size=1))
     )

g3

(ggsave(g3, "figureWEI_Int.png", width=15.5 / 2.5, height=7 / 2.5))


data2 = data[data['Variable'] != 'Total'].reset_index()
g2 = (ggplot(data2) + aes(y=data2['WEI_Abs'], x=data2['WEI+'], color=data2['Pool']) +
     geom_point(alpha=0.35) +
     facet_wrap('Scenario', ncol=2, scales="free_x", labeller={'Baseline':'Baseline', 'Connected':'High Interconnections'}) +
     scale_colour_manual(values=region_cmap, name="") +
     labs(y='$WEI^{Abs}$', x='$WEI^{+}$',
          color='Power Pool') +
      scale_y_log10(limits=(0.000000001, 150)) +
      scale_x_log10(limits=(0.000000001, 10)) +
      geom_hline(yintercept=1, linetype='dotted', color='blue') +
      geom_hline(yintercept=5, linetype='dotted', color='red') +
      geom_vline(xintercept=0.2, linetype='dotted', color='blue') +
      geom_vline(xintercept=1, linetype='dotted', color='red') +
     geom_label(aes(label=data1['Label']), size=8,adjust_text=adjust_text_dict) +
     theme_minimal() +
     theme(panel_border=element_rect(color='black', size=1))
     )

g2

(ggsave(g2, "figureWEI_T_Tot.png", width=15.5 / 2.5, height=7 / 2.5))

g4 = (ggplot(data2) + aes(y=data2['WEI_AbsInt'], x=data2['WEI+_Int'], color=data2['Pool']) +
     geom_point(alpha=0.35) +
     facet_wrap('Scenario', ncol=2, scales="free_x", labeller={'Baseline':'Baseline', 'Connected':'High Interconnections'}) +
     scale_colour_manual(values=region_cmap, name="") +
     labs(y='$WEI^{Abs}_{Int}$', x='$WEI^{+}_{Int}$',
          color='Power Pool') +
      scale_y_log10(limits=(0.000000001, 150)) +
      scale_x_log10(limits=(0.000000001, 10)) +
      geom_hline(yintercept=1, linetype='dotted', color='blue') +
      geom_hline(yintercept=5, linetype='dotted', color='red') +
      geom_vline(xintercept=0.2, linetype='dotted', color='blue') +
      geom_vline(xintercept=1, linetype='dotted', color='red') +
     geom_label(aes(label=data1['Label']), size=8,adjust_text=adjust_text_dict) +
     theme_minimal() +
     theme(panel_border=element_rect(color='black', size=1))
     )

g4

(ggsave(g4, "figureWEI_T_Int.png", width=15.5 / 2.5, height=7 / 2.5))