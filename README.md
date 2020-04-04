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

Projects
========
JRC-EU-TIMES
------------
Data extraction from [JRC-EU-TIMES](https://data.jrc.ec.europa.eu/dataset/8141a398-41a8-42fa-81a4-5b825a51761b) model (Tableau database) used in the soft-linging project with Dispa-SET. Main focus on ProRES and NearZeroCarbon scenarios
- ProRES - Projections up to 2050 (10 year interval), slightly less ambitious, sector coupling limited (without gas)
- NearZeroCarbon - Projections up tp 2050 (10 year interval), highly ambitious scenario with 95% carbon reduction compared to 1990. High focus on gas sector.

ENERGYscope
-----------
Soft linking between [ENERGYscope](http://www.energyscope.ch/) and Dispa-SET model.

OSE-MC
------
Model comparison project (Open Source Energy - Model Comparison). Dispa-SET soft-linked with the following six models:
- [CALLIOPE](https://calliope.readthedocs.io/en/stable/#)
- [DIETER](https://www.diw.de/en/diw_01.c.599753.en/models.html#ab_608464)                      
- [dynELMOD](https://gitlab.tubit.tu-berlin.de/wip/dynelmod_public)
- [EMMA](https://neon-energie.de/en/emma/)
- [URBS](https://urbs.readthedocs.io/en/latest/)
- [PLEXOS](https://energyexemplar.com/solutions/plexos/)

ARES-African Power Pools
------------------------
Soft linking between [LISFLOOD](https://ec.europa.eu/jrc/en/publication/eur-scientific-and-technical-research-reports/lisflood-distributed-water-balance-and-flood-simulation-model-revised-user-manual-2013), [TEMBA - OSeMOSYS](http://www.osemosys.org/temba.html) and Dispa-SET models applied to the following African Power Pools:
- Norht African Power Pool - NAPP
- Central African Power Pool - CAPP
- East African Power Pool - EAPP

Release date: TBD

Get involved
============
This project is an open-source project. Interested users are therefore invited to test, comment or [contribute](CONTRIBUTING.md) to the tool. Submitting issues is the best way to get in touch with the development team, which will address your comment, question, or development request in the best possible way. We are also looking for contributors to the main code, willing to contibute to its capabilities, computational-efficiency, formulation, etc. Finally, we are willing to collaborate with national agencies, reseach centers, or academic institutions on the use on the model for different data sets relative to EU countries.

Main developers
===============
Currently the main developers of the DispaSET-SideTools package are the following:

- Matija Pavičević  (KU Leuven, Belgium)
- Sylvain Quoilin (KU Leuven, Belgium)

Contributors:

- Andrea Mangipinto (Politecnico di Milano, Italy)
- Eva Joskin (University of Liège, Belgium)
- Damon Coates (UCLouvain, Belgium)
- Guillaume Percy (UCLouvain, Belgium)