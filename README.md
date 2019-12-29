![Image of License](https://img.shields.io/badge/license-EUPL%20v1.2-blue)

DispaSET-SideTools
==================
DispaSET Side tools for data handling and preprocessing

Description
-----------
The DispaSET-SideTools is a small side project that prepares various types of input data to the [Dispa-SET](http://www.dispaset.eu/en/latest/index.html) readable format:

- Typical units
- Load curves (both electricity and heating)
- Availability factors
- NTC's

The main purpose of this package is related to data analysis and preprocessing  

Quick start
===========

Prerequisites
-------------
If you want to download the latest version from github for use or development purposes, make sure that you have git and the [anaconda distribution](https://www.anaconda.com/distribution/) installed and type the following:

Anaconda Prompt
---------------
```bash
git clone https://github.com/MPavicevic/DispaSET-SideTools.git
cd Documents\git\dispaset-sidetools
conda env create  # Automatically creates environment based on environment.yml
conda activate dispaset_sidetools # Activate the environment
pip install -e . # Install editable local version
```

The above commands create a dedicated environment so that your anaconda configuration remains clean from the required dependencies installed.

Get involved
============
This project is an open-source project. Interested users are therefore invited to test, comment or [contribute](CONTRIBUTING.md) to the tool. Submitting issues is the best way to get in touch with the development team, which will address your comment, question, or development request in the best possible way. We are also looking for contributors to the main code, willing to contibute to its capabilities, computational-efficiency, formulation, etc. Finally, we are willing to collaborate with national agencies, reseach centers, or academic institutions on the use on the model for different data sets relative to EU countries.

Main developers
===============
Currently the main developers of the DispaSET-SideTools package are the following:

- Matija Pavičević  (KU Leuven, Belgium)
- Sylvain Quoilin (KU Leuven, Belgium)
