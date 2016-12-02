import ssl
import os
import sys
import yaml
import logging

from flask import Flask
from flask import jsonify
from flask import request
from flask import abort

import requests
import consul

from pymongo import MongoClient

from biomaj_cron.cron import add_cron_task
from biomaj_cron.cron import remove_cron_task
from biomaj_cron.cron import list_cron_tasks
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


app = Flask(__name__)


def consul_declare(config):
    if config['consul']['host']:
        consul_agent = consul.Consul(host=config['consul']['host'])
        consul_agent.agent.service.register('biomaj-cron', service_id=config['consul']['id'], address=config['web']['hostname'], port=config['web']['port'], tags=['biomaj'])
        check = consul.Check.http(url='http://' + config['web']['hostname'] + ':' + str(config['web']['port']) + '/api/cron', interval=20)
        consul_agent.agent.check.register(config['consul']['id'] + '_check', check=check, service_id=config['consul']['id'])


consul_declare(config)

def load_cron_tasks():
    logging.info("Load saved cron tasks")
    cron_jobs = mongo_cron.find({})
    if not cron_jobs:
        return
    for cron_job in cron_jobs:
        add_cron_task(cron_job['time'], cron_job['cmd'], cron_job['name'])


load_cron_tasks()


@app.route('/api/cron', methods=['GET'])
def ping():
    '''
    .. http:get:: /api/cron

       Ping endpoint to test service availability
       :>json dict: pong message
       :statuscode 200: no error
    '''
    return jsonify({'msg': 'pong'})


@app.route('/api/cron/jobs', methods=['GET'])
def list_cron():
    '''
    .. http:get:: /api/cron/jobs

       Get list of cron tasks

       :>json dict: list of cron tasks and query status
       :statuscode 200: no error
    '''
    jobs = []
    try:
        user_cron  = list_cron_tasks()
    except Exception as e:
        logging.error('cron:error:'+str(e))
        return jsonify({'cron': jobs, 'status': False})
    if not user_cron:
        return jsonify({'cron': jobs, 'status': True})
    for job in user_cron:
      jobs.append(str(user_cron))
    return jsonify({'cron': jobs, 'status': True})


@app.route('/api/cron/jobs/<cron_name>', methods=['DELETE'])
def delete_cron(cron_name):
    '''
    .. http:delete:: /api/cron/jobs/(str:id)

       Delete a cron task

       :>json dict: status message
       :statuscode 200: no error
    '''
    try:
        remove_cron_task(cron_name)
    except Exception as e:
        logging.error('cron:error:'+str(e))
        return jsonify({'msg': 'cron task could not be deleted', 'cron': cron_name, 'status': False})

    mongo_cron.remove({'name': cron_name})

    return jsonify({'msg': 'cron task deleted', 'cron': cron_name, 'status': True})


@app.route('/api/cron/jobs/<cron_name>', methods=['POST'])
def add_cron(cron_name):
    '''
    .. http:post:: /api/cron/jobs/(str:id)

       Update or add a cron task

       :<json dict: cron info containing slices, banks and comment
                    comment is the name to be used for the new task
                    banks is the list of banks to be udpated, comma separated
                    slices is the cron time info in cron format (example: * * * * *)
       :>json dict: status message
       :statuscode 200: no error
    '''
    param = request.get_json()
    cron_time = param['slices']
    cron_banks = param['banks']
    cron_newname = param['comment']
    cron_user = 'biomaj'
    if 'user' in param:
        cron_user = param['user']

    r = requests.get(config['web']['endpoint'] + '/api/user/info/user/' + cron_user)
    if not r.status_code == 200:
        return jsonify({'msg': 'cron task could not be updated', 'cron': cron_name, 'status': False})
    user_info = r.json()
    api_key = user_info['user']['apikey']

    try:
        remove_cron_task(cron_name)
    except Exception as e:
        logging.error('cron:error:'+str(e))
        return jsonify({'msg': 'cron task could not be updated', 'cron': cron_name, 'status': False})

    mongo_cron.remove({'name': cron_name})

    biomaj_cli = 'biomaj-cli.py'
    if 'cron' in config and config['cron']['cli']:
        biomaj_cli = config['cron']['cli']
    cmd = biomaj_cli + " --update --bank " + cron_banks + " >> /var/log/cron.log 2>&1"
    try:
        add_cron_task(cron_time, cron_cmd, cron_newname)
    except Exception as e:
        logging.error('cron:error:'+str(e))
        return jsonify({'msg': 'cron task deleted but could not update it', 'cron': cron_name, 'status': False})

    mongo_cron.insert({'name': cron_newname, 'cmd': cmd, 'time': cron_time})

    return jsonify({'msg': 'cron task added', 'cron': cron_newname, 'status': True})


if __name__ == "__main__":
    context = None
    if config['tls']['cert']:
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.load_cert_chain(config['tls']['cert'], config['tls']['key'])
    app.run(host='0.0.0.0', port=config['web']['port'], ssl_context=context, threaded=True, debug=config['web']['debug'])
