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

data1 = pd.read_csv("data_figure18.csv")
qq_01 = pd.read_csv('data_figure_qq_18.csv', index_col=0)
qq_02 = pd.read_csv('data_figure_qq2_18.csv', index_col=0)
# data1['Label'] = data1['Label'].astype('Int64')

adjust_text_dict = {
    'expand_points': (1.35, 1.35),
    'ha': 'center',
    'va': 'center',
    # 'arrowprops': {
    #     'arrowstyle': '->',
    #     'color': 'red'
    # }
}

data = data1[data1['Region'] != 'Africa']
data = data1

g = (ggplot(data=data) +
     aes(x=data['Costs'], y=data['CO2'], size=data['Inflow'], color=data['Region'], xmin=0, xmax=40) +
     geom_point(alpha=0.15) +
     facet_wrap('Scenario', ncol=2, scales="free_x") +
     # facet_grid('Scenario ~ Region') +
     scale_colour_manual(values=region_cmap, name="Power Pool") +
     scale_size(range=[0.1, 20],
                breaks=[250, 500, 1000, 2000, 4000, 6000],
                labels=["250", "500", "1000", "2000", "4000", "6000"],
                name = 'InFlows [MWh/h]') +
     labs(x = 'Average Price of Electricity [EUR/MWh]', y='CO2 intensity [kg/MWh]') +
     # geom_text(aes(label=data['Label']), nudge_x=2, nudge_y=2, size=10, adjust_text=adjust_text_dict) +
     # scale_x_continuous(breaks=[0,10,20,30,40]) +
     geom_hline(yintercept=qq_01['CAPP'], data=qq_01, linetype='dotted', color='#FFBE00') +
     geom_hline(yintercept=qq_01['EAPP'], data=qq_01, linetype='dotted', color='#BF008E') +
     geom_hline(yintercept=qq_01['NAPP'], data=qq_01, linetype='dotted', color='#089701') +
     geom_hline(yintercept=qq_01['SAPP'], data=qq_01, linetype='dotted', color='#E51A1D') +
     geom_hline(yintercept=qq_01['WAPP'], data=qq_01, linetype='dotted', color='#1C75FE') +
     geom_hline(yintercept=qq_01['Africa'], data=qq_01, linetype='dotted', color='grey') +
     geom_vline(xintercept=qq_02['CAPP'], data=qq_02, linetype='dotted', color='#FFBE00') +
     geom_vline(xintercept=qq_02['EAPP'], data=qq_02, linetype='dotted', color='#BF008E') +
     geom_vline(xintercept=qq_02['NAPP'], data=qq_02, linetype='dotted', color='#089701') +
     geom_vline(xintercept=qq_02['SAPP'], data=qq_02, linetype='dotted', color='#E51A1D') +
     geom_vline(xintercept=qq_02['WAPP'], data=qq_02, linetype='dotted', color='#1C75FE') +
     geom_vline(xintercept=qq_02['Africa'], data=qq_02, linetype='dotted', color='grey') +
     theme_minimal()
     )

g

(ggsave(g, "figure18.png", width=15.5 / 2.5, height=12 / 2.5))


adjust_text_dict = {
    'expand_points': (1.8, 2),
    'ha': 'center',
    'va': 'center',
}

g2 = (ggplot(data=data) +
      aes(x=data['Withdrawal'], y=data['Consumption'], size=data['Inflow'], fill=data['Costs']) +
      geom_point(alpha=0.35) +
      facet_wrap('Scenario', ncol=2, scales="free_x", labeller={'Baseline':'Baseline', 'Connected':'High Interconnections'}) +
      scale_colour_manual(values=region_cmap, name="") +
      geom_label(aes(label=data['Label_1']), size=10, adjust_text=adjust_text_dict) +
      # stat_smooth(method='lm') +
      # scale_y_log10() +
      # scale_x_log10() +
      scale_size(range=[4, 25],
                 breaks=[250, 500, 1000, 2000, 4000, 6000],
                 labels=["250", "500", "1000", "2000", "4000", "6000"],
                 name='Average Hydro Inflows [MWh/h]') +
      scale_fill_distiller(type='div', palette='RdBu', direction=-1) +
      labs(x='Water Withdrawal (Thermal) [$m^3$/MWh]', y='Water Consumption (Thermal) [$m^3$/MWh]',
           fill='Generation Cost [EUR/MWh]', color='Power Pool') +
      theme_minimal() +
      theme(legend_direction='horizontal', panel_border=element_rect(color='black', size=1))

      )

g2

(ggsave(g2, "figure18a.png", width=15.5 / 2.5, height=10 / 2.5))



adjust_text_dict = {
    'expand_points': (1.8, 2),
    'ha': 'center',
    'va': 'center',
}

g3 = (ggplot(data=data) +
      aes(x=data['WAT'], y=data['Fossil'], fill=data['Costs'], size=data['CO2']) +
      geom_point(alpha=0.35) +
      geom_label(aes(label=data['Label_2']), size=10, adjust_text=adjust_text_dict) +
      scale_colour_manual(values=region_cmap, alpha=1) +
      scale_size(range=[0.1, 15],
                 breaks=[50, 150, 300, 600],
                 labels=["50", "150", "300", '600'],
                 name='CO2 [kg/MWh]') +
      scale_fill_distiller(type='div', palette='RdBu', direction=-1) +
      facet_wrap('Scenario', ncol=2, scales="free_x", labeller={'Baseline':'Baseline', 'Connected':'High Interconnections'}) +
      labs(x = 'Hydro Generation [TWh]', y='Fossil Generation [TWh]', fill='Generation Cost [EUR/MWh]', color='Power Pool') +
      theme_minimal() +
      theme(legend_direction='horizontal', panel_border=element_rect(color='black', size=1.5)) +
      scale_y_log10() +
      scale_x_log10()
      )

g3

(ggsave(g3, "figure18b.png", width=15.5 / 2.5, height=10 / 2.5))

data = data[data['id'] != 2000]
g4 = (ggplot(data=data) +
      aes(x=data['WAT'], y=data['Fossil'], fill=data['Curtailment'], size=data['ShedLoad']) +
      geom_point(alpha=0.35) +
      geom_label(aes(label=data['Label_2']), size=10, adjust_text=adjust_text_dict) +
      scale_colour_manual(values=region_cmap, alpha=1) +
      scale_size(range=[1, 20],
                 breaks=[0.001, 0.01, 0.1],
                 labels=["0.001", "0.01", '0.1'],
                 name='Shed Load [%]') +
      scale_fill_distiller(type='div', palette='RdYlGn', direction=-1) +
      facet_wrap('Scenario') +
      labs(x = 'Hydro Generation [TWh]', y='Fossil Generation [TWh]', fill='Curtailment [%]', color='Power Pool') +
      theme_minimal() +
      theme(legend_direction='horizontal', panel_border=element_rect(color='black', size=1.5)) +
      scale_y_log10() +
      scale_x_log10()
      )

g4

(ggsave(g4, "figure18c.png", width=15.5 / 2.5, height=10 / 2.5))

g4 = (ggplot(data=data) +
      aes(x=data['WAT'], y=data['Fossil'], size=data['Curtailment'], fill=data['ShedLoad']) +
      geom_point(alpha=0.35) +
      geom_label(aes(label=data['Label_2']), size=10, adjust_text=adjust_text_dict) +
      scale_colour_manual(values=region_cmap, alpha=1) +
      scale_size(range=[3, 25],
                 breaks=[0.1, 1, 10, 50, 100],
                 labels=["0.1", "1", '10', '50', '100'],
                 name='Curtailment [%]') +
      scale_fill_distiller(type='div', palette='RdYlBu', direction=-1) +
      facet_wrap('Scenario', ncol=2, scales="free_x", labeller={'Baseline':'Baseline', 'Connected':'High Interconnections'}) +
      labs(x = 'Hydro Generation [TWh]', y='Fossil Generation [TWh]', fill='Shed Load [%]', color='Power Pool') +
      theme_minimal() +
      theme(legend_direction='horizontal', panel_border=element_rect(color='black', size=1.5)) +
      scale_y_log10() +
      scale_x_log10()
      )

g4

(ggsave(g4, "figure18d.png", width=15.5 / 2.5, height=10 / 2.5))

