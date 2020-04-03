from setuptools import setup, find_packages
import codecs
import os

HERE = os.path.abspath(os.path.dirname(__file__))

# FINAL_RELEASE is the last stable version of Dispa-SET_sidetools
# A more precisely version try to be automatically determined from the git repository using setuptools_scm.
# If it's not possible (using git archive tarballs for example), FINAL_RELEASE will be used as fallback version.
# edited manually when a new release is out (git tag -a)
FINAL_RELEASE = open(os.path.join(HERE, 'VERSION')).read().strip()


def read(*parts):
    """
    Build an absolute path from *parts* and and return the contents of the
    resulting file.  Assume UTF-8 encoding.
    """
    with codecs.open(os.path.join(HERE, *parts), "rb", "utf-8") as f:
        return f.read()


# Sets the __version__ variable
__version__ = None
exec(open('dispaset_sidetools/_version.py').read())

setup(
    name='dispaset_sidetools',
    description='Side tools for the Dispa-SET model ',
    author='Matija Pavičević, Sylvain Quoilin',
    author_email='matija.pavicevic@kuleuven.be',
    url='https://github.com/MPavicevic/DispaSET-SideTools',
    license='EUPL v1.2',
    packages=find_packages(),
    include_package_data=True,
    use_scm_version={
        'version_scheme': 'post-release',
        'local_scheme': lambda version: version.format_choice("" if version.exact else "+{node}", "+dirty"),
        'fallback_version': FINAL_RELEASE,
    },
    setup_requires=["setuptools_scm"],
    install_requires=[
        "future >= 0.15",
        "click >= 3.3",
        "numpy >= 1.12",
        "pandas >= 0.19",
        "xlrd >= 0.9",
        "matplotlib >= 1.5.1",
        "setuptools_scm",
        "pycountry"
    ],
    classifiers=[
        'Intended Audience :: Science/Research',
        'Programming Language :: Python'
    ],
    keywords=['database', 'energy systems analysis']
)
