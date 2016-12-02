import os
import yaml
import logging

from pymongo import MongoClient

from biomaj_cron.cron import add_cron_task
from biomaj_core.utils import Utils


config_file = 'config.yml'
if 'BIOMAJ_CONFIG' in os.environ:
        config_file = os.environ['BIOMAJ_CONFIG']

config = None

with open(config_file, 'r') as ymlfile:
    config = yaml.load(ymlfile)
    Utils.service_config_override(config)


client = MongoClient(config['mongo']['url'])
db = client[config['mongo']['db']]
mongo_cron = db.cron


def load_cron_tasks():
    logging.info("Load saved cron tasks")
    cron_jobs = mongo_cron.find({})
    if not cron_jobs:
        return
    for cron_job in cron_jobs:
        add_cron_task(cron_job['time'], cron_job['cmd'], cron_job['name'])


if __name__ == "__main__":
    load_cron_tasks()
