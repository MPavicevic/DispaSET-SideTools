import pandas as pd
import numpy as np
from plotnine import *
import matplotlib as mpl
import seaborn as sns

sel = pd.read_csv("data_figure04.csv")

g = (ggplot(sel) +
     aes(x=sel['year'], y=sel['Region'], fill=sel['perc_deviation'], alpha=sel['type_deviation']) +
     geom_point(aes(size=sel['type_deviation'], shape=sel['type_deviation'])) +
     scale_shape_manual(values=['v', '^', 'v', '^', 'v', '^', 'v', '^'], guide=False,
                        breaks=['Sp', 'Mp', 'Lp', 'XLp', 'Sm', 'Mm', 'Lm', 'XLm']) +
     scale_size_manual(values={"Sp": 1, "Mp": 2, "Lp": 4, "XLp": 8, "Sm": 1, "Mm": 2, "Lm": 4, "XLm": 8},
                       labels=[">15%", "10%", "5%", ">0", "<0", "-5%", "-10%", "<-15%"],
                       name=' ', drop=False, guide=False,
                       breaks=['XLp', 'Lp', 'Mp', 'Sp', 'Sm', 'Mm', 'Lm', 'XLm']) +
     scale_alpha_manual(values={"Sm": 0.2, "Mm": 0.3, "Lm": 0.7, "XLm": 0.9,
                                "Sp": 0.2, "Mp": 0.3, "Lp": 0.7, "XLp": 0.9}, guide=False) +
     scale_fill_distiller(type='div', palette='RdBu', direction=1) +
     guides(fill=False,
            size=guide_legend(override_aes={'shape': ['^', '^', '^', '^', 'v', 'v', 'v', 'v'],
                                            'fill': sns.color_palette("RdBu_r", 8),
                                            })) +
     scale_x_continuous(breaks=range(1980, 2019, 3)) +
     expand_limits(y=0) +
     labs(x="Climate year", y='Power Pool') +
     theme_minimal()
     )

(ggsave(g, "figure04.png", width=15.5/2.5, height=6/2.5))
