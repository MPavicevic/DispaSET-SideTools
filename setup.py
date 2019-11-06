from setuptools import setup, find_packages
import codecs
import os

_here = os.path.abspath(os.path.dirname(__file__))

def read(*parts):
    """
    Build an absolute path from *parts* and and return the contents of the
    resulting file.  Assume UTF-8 encoding.
    """
    with codecs.open(os.path.join(_here, *parts), "rb", "utf-8") as f:
        return f.read()

# Sets the __version__ variable
__version__ = None
exec(open('dispaset_sidetools/_version.py').read())

setup(
    name='dispaset_sidetools',
    version=__version__,
    description='Side tools for the Dispa-SET model ',
    author='Matija Pavičević, Sylvain Quoilin',
    author_email='matija.pavicevic@kuleuven.be',
    url='https://github.com/MPavicevic/DispaSET-SideTools',
    license='EUPL v1.2',
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        'Intended Audience :: Science/Research',
        'Programming Language :: Python'
    ],
    keywords=['database', 'energy systems analysis']
)