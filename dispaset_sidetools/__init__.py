#import logging.config
import os

# Sets the __version__ variable
from ._version import __version__
from .common import commons

def get_git_revision_tag():
    """Get version of DispaSET used for this run. tag + commit hash"""
    from subprocess import check_output
    try:
        return check_output(["git", "describe", "--tags", "--always"]).strip()
    except:
        return 'NA'
#from .preprocessing.preprocessing import get_git_revision_tag
__gitversion__ = get_git_revision_tag()

