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

zone_cmap = {'CD': '#fdf98b',
             'CF': '#f3e771',
             'CG': '#fbef45',
             'CM': '#fbf422',
             'GA': '#e6d313',
             'GQ': '#d2c503',
             'TD': '#8c8802',
             'BI': '#f196dc',
             'DJ': '#a590d4',
             'EG': '#a373cd',
             'ER': '#da42b3',
             'ET': '#b940b5',
             'KE': '#e637bd',
             'RW': '#6744b4',
             'SD': '#6d389e',
             'SO': '#951c76',
             'SS': '#692567',
             'TZ': '#9e137e',
             'UG': '#3b2767',
             'DZ': '#198309',
             'LY': '#c2f816',
             'MA': '#3dee0c',
             'MR': '#d5fa83',
             'TN': '#1c9c5c',
             'AO': '#f66e70',
             'BW': '#f26c4e',
             'MW': '#bd6360',
             'MZ': '#df1a1c',
             'NA': '#c80d11',
             'SZ': '#c8300d',
             'ZA': '#7e3634',
             'ZM': '#7f0e10',
             'ZW': '#640608',
             'BF': '#a1cfe7',
             'BJ': '#7dbae7',
             'CI': '#66aedb',
             'GH': '#779ca6',
             'GM': '#2e6dcb',
             'GN': '#68b2d8',
             'GW': '#419adc',
             'LR': '#2f8eca',
             'LS': '#547881',
             'ML': '#214e91',
             'NE': '#2b7fab',
             'NG': '#1b6296',
             'SL': '#1b5173',
             'SN': '#2a3c40',
             'TG': '#0d1f3a'
             }

zone_order = ['CD','CF','CG','CM','GA','GQ','TD',
             'BI','DJ','EG','ER','ET','KE','RW','SD','SO','SS','TZ','UG',
             'DZ','LY','MA','MR','TN',
             'AO','BW','MW','MZ','NA','SZ','ZA','ZM','ZW',
             'BF','BJ','CI','GH','GM','GN','GW','LR','LS','ML','NE','NG','SL','SN','TG']

adjust_text_dict = {
    # 'expand_points': (1.8, 2),
    'ha': 'center',
    'va': 'center',
}

data = pd.read_csv('data_fig_WEI_zonal.csv')
data1 = data[data['Variable'] != 'Thermal'].reset_index()

# g = (ggplot(data1) + aes(y=data1['WEI_Abs'], x=data1['WEI+'], color=data1['Pool']) +
#      geom_point(alpha=0.25, size=3) +
#      facet_wrap('Scenario', ncol=2, scales="free_x", labeller={'Baseline':'Baseline', 'Connected':'High Interconnections'}) +
#      scale_color_manual(values=region_cmap, name="") +
#      # scale_colour_manual(values="grey", name="") +
#      labs(y='$WEI^{Abs}$', x='$WEI^{+}$',
#           color='Power Pool') +
#      scale_y_log10(limits=(0.000000001,150)) +
#      scale_x_log10(limits=(0.000000001,10)) +
#      geom_hline(yintercept=1, linetype='dotted', color='blue') +
#      geom_hline(yintercept=5, linetype='dotted', color='red') +
#      geom_vline(xintercept=0.2, linetype='dotted', color='blue') +
#      geom_vline(xintercept=1, linetype='dotted', color='red') +
#      geom_label(aes(label=data1['Label']), size=8,adjust_text=adjust_text_dict) +
#      theme_minimal() +
#      theme(panel_border=element_rect(color='black', size=1))
#      )
#
# g
#
# (ggsave(g, "figureWEI_Tot.png", width=15.5 / 2.5, height=7 / 2.5))
#
# g3 = (ggplot(data1) + aes(y=data1['WEI_AbsInt'], x=data1['WEI+_Int'], color=data1['Pool']) +
#      geom_point(alpha=0.35) +
#      facet_wrap('Scenario', ncol=2, scales="free_x", labeller={'Baseline':'Baseline', 'Connected':'High Interconnections'}) +
#      scale_colour_manual(values=region_cmap, name="") +
#      labs(y='$WEI^{Abs}_{Int}$', x='$WEI^{+}_{Int}$',
#           color='Power Pool') +
#      scale_y_log10(limits=(0.000000001,150)) +
#      scale_x_log10(limits=(0.000000001,10)) +
#       geom_hline(yintercept=1, linetype='dotted', color='blue') +
#       geom_hline(yintercept=5, linetype='dotted', color='red') +
#       geom_vline(xintercept=0.2, linetype='dotted', color='blue') +
#       geom_vline(xintercept=1, linetype='dotted', color='red') +
#      geom_label(aes(label=data1['Label']), size=8,adjust_text=adjust_text_dict) +
#      theme_minimal() +
#      theme(panel_border=element_rect(color='black', size=1))
#      )
#
# g3
#
# (ggsave(g3, "figureWEI_Int.png", width=15.5 / 2.5, height=7 / 2.5))
#
#
data2 = data[data['Variable'] != 'Total'].reset_index()
# g2 = (ggplot(data2) + aes(y=data2['WEI_Abs'], x=data2['WEI+'], color=data2['Pool']) +
#      geom_point(alpha=0.35) +
#      facet_wrap('Scenario', ncol=2, scales="free_x", labeller={'Baseline':'Baseline', 'Connected':'High Interconnections'}) +
#      scale_colour_manual(values=region_cmap, name="") +
#      labs(y='$WEI^{Abs}$', x='$WEI^{+}$',
#           color='Power Pool') +
#       scale_y_log10(limits=(0.000000001, 150)) +
#       scale_x_log10(limits=(0.000000001, 10)) +
#       geom_hline(yintercept=1, linetype='dotted', color='blue') +
#       geom_hline(yintercept=5, linetype='dotted', color='red') +
#       geom_vline(xintercept=0.2, linetype='dotted', color='blue') +
#       geom_vline(xintercept=1, linetype='dotted', color='red') +
#      geom_label(aes(label=data1['Label']), size=8,adjust_text=adjust_text_dict) +
#      theme_minimal() +
#      theme(panel_border=element_rect(color='black', size=1))
#      )
#
# g2
#
# (ggsave(g2, "figureWEI_T_Tot.png", width=15.5 / 2.5, height=7 / 2.5))
#
# g4 = (ggplot(data2) + aes(y=data2['WEI_AbsInt'], x=data2['WEI+_Int'], color=data2['Pool']) +
#      geom_point(alpha=0.35) +
#      facet_wrap('Scenario', ncol=2, scales="free_x", labeller={'Baseline':'Baseline', 'Connected':'High Interconnections'}) +
#      scale_colour_manual(values=region_cmap, name="") +
#      labs(y='$WEI^{Abs}_{Int}$', x='$WEI^{+}_{Int}$',
#           color='Power Pool') +
#       scale_y_log10(limits=(0.000000001, 150)) +
#       scale_x_log10(limits=(0.000000001, 10)) +
#       geom_hline(yintercept=1, linetype='dotted', color='blue') +
#       geom_hline(yintercept=5, linetype='dotted', color='red') +
#       geom_vline(xintercept=0.2, linetype='dotted', color='blue') +
#       geom_vline(xintercept=1, linetype='dotted', color='red') +
#      geom_label(aes(label=data1['Label']), size=8,adjust_text=adjust_text_dict) +
#      theme_minimal() +
#      theme(panel_border=element_rect(color='black', size=1))
#      )
#
# g4
#
# (ggsave(g4, "figureWEI_T_Int.png", width=15.5 / 2.5, height=7 / 2.5))

data_test = pd.read_csv('data_fig_WEI_zonal_test.csv')

data3 = data_test[data_test['Variable'] != 'Total'].reset_index()

levels = [0.005,0.05,0.1,0.15,0.2,0.25]
lim_x_min = 1e-12
lim_y_min = 1e-12
lim_x = 1e3
lim_y = 1e3


g5 = (ggplot(data3) + aes(y=data3['WEI_AbsInt'], x=data3['WEI+_Int']) +
      stat_density_2d(aes(fill='..level..'), geom="polygon", alpha=0.95, levels=levels, n=32) +
      scale_fill_distiller(type='div',palette='Spectral', direction=-1) +
      geom_density_2d(size=0.15, colour="black", alpha=0.5, levels=levels, n=32) +
      geom_point(aes(y=data3['WEI_AbsInt_Crit'], x=data3['WEI+_Int_Crit']), alpha=0.3, color='black') +
      facet_grid('Pool ~ Scenario', scales="free_x") +
      labs(y='$WEI^{Abs}_{Int}$', x='$WEI^{+}_{Int}$',
           color='Zone') +
      scale_y_log10(limits=(lim_y_min, lim_y)) +
      scale_x_log10(limits=(lim_x_min, lim_x)) +
      geom_hline(yintercept=1, linetype='dotted', color='blue') +
      geom_hline(yintercept=5, linetype='dotted', color='red') +
      geom_vline(xintercept=0.2, linetype='dotted', color='blue') +
      geom_vline(xintercept=1, linetype='dotted', color='red') +
     geom_label(aes(label=data3['Label_Int']), size=6,adjust_text=adjust_text_dict, color='black') +
     theme_minimal() +
     theme(panel_border=element_rect(color='black', size=1))
     )

g5

(ggsave(g5, "figureWEI_T_Int_2.png", width=15.5 / 2.5, height=13 / 2.5))

g6 = (ggplot(data3) + aes(y=data3['WEI_Abs'], x=data3['WEI+']) +
      stat_density_2d(aes(fill='..level..'), geom="polygon", alpha=0.95, levels=levels, n=32) +
      scale_fill_distiller(type='div',palette='Spectral', direction = -1) +
      geom_density_2d(size=0.15, colour="black", alpha=0.5, levels=levels, n=32) +
      geom_point(aes(y=data3['WEI_Abs_Crit'], x=data3['WEI+_Crit']), alpha=0.3, color='black') +
      facet_grid('Pool ~ Scenario', scales="free_x") +
      labs(y='$WEI^{Abs}$', x='$WEI^{+}$',
           color='Zone') +
      scale_y_log10(limits=(lim_y_min, lim_y)) +
      scale_x_log10(limits=(lim_x_min, lim_x)) +
      geom_hline(yintercept=1, linetype='dotted', color='blue') +
      geom_hline(yintercept=5, linetype='dotted', color='red') +
      geom_vline(xintercept=0.2, linetype='dotted', color='blue') +
      geom_vline(xintercept=1, linetype='dotted', color='red') +
     geom_label(aes(label=data3['Label']), size=6,adjust_text=adjust_text_dict, color='black') +
     theme_minimal() +
     theme(panel_border=element_rect(color='black', size=1))
     )

g6

(ggsave(g6, "figureWEI_T_Tot_2.png", width=15.5 / 2.5, height=13 / 2.5))


data3 = data_test[data_test['Variable'] != 'Thermal'].reset_index()

g7 = (ggplot(data3) + aes(y=data3['WEI_AbsInt'], x=data3['WEI+_Int']) +
      stat_density_2d(aes(fill='..level..'), geom="polygon", alpha=0.95, levels=levels, n=32) +
      scale_fill_distiller(type='div',palette='Spectral', direction=-1) +
      geom_density_2d(size=0.15, colour="black", alpha=0.5, levels=levels, n=32) +
      geom_point(aes(y=data3['WEI_AbsInt_Crit'], x=data3['WEI+_Int_Crit']), alpha=0.3, color='black') +
      facet_grid('Pool ~ Scenario', scales="free_x") +
      labs(y='$WEI^{Abs}_{Int}$', x='$WEI^{+}_{Int}$',
           color='Zone') +
      scale_y_log10(limits=(lim_y_min, lim_y)) +
      scale_x_log10(limits=(lim_x_min, lim_x)) +
      geom_hline(yintercept=1, linetype='dotted', color='blue') +
      geom_hline(yintercept=5, linetype='dotted', color='red') +
      geom_vline(xintercept=0.2, linetype='dotted', color='blue') +
      geom_vline(xintercept=1, linetype='dotted', color='red') +
     geom_label(aes(label=data3['Label_Int']), size=6,adjust_text=adjust_text_dict, color='black') +
     theme_minimal() +
     theme(panel_border=element_rect(color='black', size=1))
     )

g7

(ggsave(g7, "figureWEI_Int_2.png", width=15.5 / 2.5, height=13 / 2.5))

g8 = (ggplot(data3) + aes(y=data3['WEI_Abs'], x=data3['WEI+']) +
      stat_density_2d(aes(fill='..level..'), geom="polygon", alpha=0.95, levels=levels, n=32) +
      scale_fill_distiller(type='div',palette='Spectral', direction = -1) +
      geom_density_2d(size=0.15, colour="black", alpha=0.5, levels=levels, n=32) +
      geom_point(aes(y=data3['WEI_Abs_Crit'], x=data3['WEI+_Crit']), alpha=0.3, color='black') +
      facet_grid('Pool ~ Scenario', scales="free_x") +
      labs(y='$WEI^{Abs}$', x='$WEI^{+}$',
           color='Zone') +
      scale_y_log10(limits=(lim_y_min, lim_y)) +
      scale_x_log10(limits=(lim_x_min, lim_x)) +
      geom_hline(yintercept=1, linetype='dotted', color='blue') +
      geom_hline(yintercept=5, linetype='dotted', color='red') +
      geom_vline(xintercept=0.2, linetype='dotted', color='blue') +
      geom_vline(xintercept=1, linetype='dotted', color='red') +
     geom_label(aes(label=data3['Label']), size=6,adjust_text=adjust_text_dict, color='black') +
     theme_minimal() +
     theme(panel_border=element_rect(color='black', size=1))
     )

g8

(ggsave(g8, "figureWEI_Tot_2.png", width=15.5 / 2.5, height=13 / 2.5))
