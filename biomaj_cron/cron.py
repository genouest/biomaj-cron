from crontab import CronTab
import requests


def add_cron_task(cron_time, cron_cmd, cron_name):
    cron = CronTab(user=True)
    job = cron.new(command=cron_cmd, comment=cron_name)
    job.setall(cron_time)
    cron.write()


def list_cron_tasks():
    cron_jobs = CronTab(user=True)
    return cron_jobs


def remove_cron_task(cron_name):
    cron = CronTab(user=True)
    cron.remove_all(comment=cron_name)
    cron.write()


class CronClient(object):
    '''
    Client class to manage BioMAJ cron service, either locally or calling remote service
    '''

    def __init__(self, endpoint=None, biomaj_cli='biomaj-cli.py'):
        '''
        Constructor

        :param endpoint: Remote address to cron service or proxy. If None, calls methods locally
        :type endpoint: str
        :param biomaj_cli: Path to biomaj-cli.py if not in PATH
        :type biomaj_clic: str
        '''
        self.endpoint = endpoint
        self.biomaj_cli = biomaj_cli

    def cron_tasks(self):
        '''
        Get a list of defined cron tasks

        :return: list of str (cron syntax like format * * * * * echo hello), None if operation failed

        '''
        cron_list = []
        if self.endpoint:
            r = requests.get(self.endpoint + '/api/cron/jobs')
            if not r.status_code == 200:
                return None
            answer = r.json()
            if answer['status']:
                cron_list = answer['cron']
            else:
                return None

        else:
            cron_list = list_cron_tasks()
        return cron_list

    def cron_task_add(self, cron_time, banks, cron_name, cron_oldname=None):
        '''
        Add a new cron task

        :param cron_time: cron format time request (example: 0 * * 1 *)
        :type cron_time: str
        :param banks: banks to update (example alu,genbank)
        :type banks: str
        :param cron_name: unique name for the cron operation, used to match a cron task
        :type cron_name: str
        :param cron_oldname: unique name for an existing cron operation in case of cron task update, defaults to cron_name parameter
        :type cron_oldname: str
        :return: bool Success of operation
        '''
        if not cron_oldname:
            cron_oldname = cron_name

        is_ok = False
        if self.endpoint:
            r = requests.post(self.endpoint + '/api/cron/jobs/' + cron_oldname, json={
                'slices': cron_time,
                'banks': banks,
                'comment': cron_name
            })
            if not r.status_code == 200:
                return False
            answer = r.json()
            if answer['status']:
                is_ok = True
        else:
            cron_cmd = self.biomaj_cli + " --update --bank " + banks + " >> /var/log/cron.log 2>&1"
            add_cron_task(cron_time, cron_cmd, cron_name)
            is_ok = True
        return is_ok

    def cron_task_remove(self, cron_name):
        '''
        Removes a cron task

        :param cron_name: unique name for the cron operation, used to match a cron task
        :type cron_name: str
        :return: bool Success of operation
        '''
        is_ok = False

        if self.endpoint:
            r = requests.delete(self.endpoint + '/api/cron/jobs/' + cron_name)
            if not r.status_code == 200:
                return False
            answer = r.json()
            if answer['status']:
                is_ok = True
        else:
            remove_cron_task(cron_name)
            is_ok = True
        return is_ok
