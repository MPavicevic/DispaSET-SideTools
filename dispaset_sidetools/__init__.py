# Sets the __version__ variable
from ._version import __version__
from .common import *
from .search import *
from .constants import *
from .get_demand.get_demand_es_multi_cell import get_demand_from_es
from .get_heat_demand.get_heat_demand_es_multi_cell import get_heat_demand_from_es
from .get_renewables.get_availability_factors_es_multi_cell import get_availability_factors_from_es
from .get_capacities.get_capacities_es import get_capacities_from_es

def get_git_revision_tag():
    """Get version of DispaSET used for this run. tag + commit hash"""
    from subprocess import check_output
    try:
        return check_output(["git", "describe", "--tags", "--always"]).strip()
    except:
        return 'NA'

#from .preprocessing.preprocessing import get_git_revision_tag
__gitversion__ = get_git_revision_tag()

# if somebody does "from dispaset_sidetools import *", this is what they will be able to access:
__all__ = ['commons',
           'search',
           'constants',
          ]