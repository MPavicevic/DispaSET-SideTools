# Sets the __version__ variable
from ._version import __version__
from .common import *
from .search import *
from .constants import *

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