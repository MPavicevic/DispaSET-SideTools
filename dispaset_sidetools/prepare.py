import sys, os
sys.path.append(os.path.abspath(r'..'))

import pandas as pd
import glob

from dispaset_sidetools import *
import numpy as np
import pandas as pd
import math

from dispaset_sidetools.common import mapping,outliers,fix_na,make_dir
from dispaset_sidetools.search import from_excel_to_dataFrame,get_TDFile
from dispaset_sidetools.constants import n_TD

input_folder = '../Inputs/EnergyScope/'  # to access DATA - DATA_brut & Typical_Units(to find installed power f [GW or GWh for storage])
output_folder = '../Outputs/EnergyScope/'

input_PP_folder = '../../Dispa-SET.git/Database/PowerPlants/'  # input file = PowerPlants.csv

#Run several functions from search.py
get_TDFile(n_TD)

