# Sets the __version__ variable
import logging.config
import os

from .common import commons
from .get_capacities.get_Capacities_ARES_APP import get_hydro_units

_LOGCONFIG = {
     "version": 1,
     "disable_existing_loggers": False,
     'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)-8s] (%(funcName)s): %(message)s',
            'datefmt': '%y/%m/%d %H:%M:%S'
        },
        'notime': {
            'format': '[%(levelname)-8s] (%(funcName)s): %(message)s',
            'datefmt': '%y/%m/%d %H:%M:%S'
        },
     },
     "handlers": {
         "console": {
            "class": "dispaset_sidetools.misc.colorstreamhandler.ColorStreamHandler",
             "stream": "ext://sys.stderr",
#             "stream": "sys.stdout",
             "level": "INFO",
             'formatter': 'notime',
         },

         "error_file": {
             "class": "logging.FileHandler",
             "level": "INFO",
             'formatter': 'standard',
             'filename': commons['logfile'],
             'encoding': 'utf8'

         }
     },

     "root": {
         "level": "INFO",
         "handlers": ["console", "error_file"],
     }
}

# Setting logging configuration:
try:
    logging.config.dictConfig(_LOGCONFIG)
except Exception:
    # if it didn't work, it might be due to ipython messing with the output
    # typical error: Unable to configure handler 'console': IOStream has no fileno
    # try without console output:
    print('WARNING: the colored console output is failing (possibly because of ipython). Switching to monochromatic output')
    _LOGCONFIG['handlers']['console']['class'] = "logging.StreamHandler"
    logging.config.dictConfig(_LOGCONFIG)

# Sets the __version__ variable
try:
    from setuptools_scm import get_version
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        version = get_version(version_scheme='post-release',
                              local_scheme=lambda version: version.format_choice("" if version.exact else "+{node}", "+dirty"),
                              root='..', relative_to=__file__)
except (ImportError, LookupError):
    try:
        from pkg_resources import get_distribution, DistributionNotFound
        version = get_distribution(__package__).version
    except DistributionNotFound:
        logging.warning("Unable to detect version, most probably because you did not install it properly. To avoid further errors, please install it by running 'pip install -e .'.")
        version = 'N/A'
__version__ = version

# if somebody does "from dispaset_sidetools import *", this is what they will
# be able to access:
__all__ = [
    'commons','get_hydro_units',
]

# Remove old log file:
for filename in (f for f in os.listdir('.') if f.endswith('.dispa_sidetools.log')):
    try:
        os.remove(filename)
    except OSError:
        print ('Could not erase previous log file ' + filename)