# BioMAJ cron service

biomaj-cron manages the cron task to update BioMAJ banks.

It can be used as a library or as a micro-service.

[![PyPI version](https://badge.fury.io/py/biomaj-cron.svg)](https://badge.fury.io/py/biomaj-cron)

# Install

    pip install biomaj-cron

# Micro service

## Run

    # to reload cron tasks from database (in case of micro service)
    biomaj_load_cron.py

    export BIOMAJ_CONFIG=path_to_config.yml
    gunicorn -b 0.0.0.0:5000 biomaj_cron.biomaj_cron_web:app

## API

    Endpoint /api/cron


# Generate documentation

    pip install sphinx
    pip install sphinxcontrib-httpdomain
    cd doc
    make html
