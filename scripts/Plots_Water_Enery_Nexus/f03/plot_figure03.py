import pandas as pd
from plotnine import *

data_toplot = pd.read_csv("data_figure03.csv")

g = (ggplot(data_toplot) +
     aes(x=data_toplot['year'], y=data_toplot['fraction'], fill=data_toplot['type_label']) +
     geom_area() +
     theme_light() +
     scale_fill_manual(values={'Wind power': "#c9cf5c", 'Hydro-power': "#00a0e1ff", 'Solar power': "#e6a532"},
                       name=' ') +
     scale_x_continuous(breaks=range(1990, 2017, 3)) +
     scale_y_continuous(labels=lambda l: ["%d%%" % (v * 100) for v in l]) +
     labs(x="year", y="Fraction of the total capacity") +
     theme_minimal()
     )

(ggsave(g, "figure03.png", width=6, height=3))
