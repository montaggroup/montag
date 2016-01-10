# coding=utf-8
from multiprocessing import Process, Array, Value
import com.client
import com.master_strategy
import com.strategies
import Pyro4
import sys
import time
import logging
import filedownloadmonitor
import pyrosetup

logger = logging.getLogger('comservice')

DELAY_BETWEEN_UPDATE_LAUNCHES = 0.2


class Job(object):
    def __init__(self, name, friend_id):
        self.name = name
        self.friend_id = friend_id
        self.start_time = time.time()

        self.process = None
        self.is_running_if_no_process = True

        self.current_phase = Value('i')
        self.current_phase.value = 0
        self.progress_array = Array('i', range(2))
        self.progress_array[0] = -1  # number items to request OR number documents provided, depending on context
        self.progress_array[1] = -1  # number requested OR number files provided, depending on context

    def is_running(self):
        if self.process is not None:
            return self.process.is_alive()

        return self.is_running_if_no_process

    def join_process(self):
        if self.process is not None:
            self.process.join()

    def terminate(self):
        if self.process is None:
            return
        if self.process.is_alive():
            self.process.terminate()

    def __str__(self):
        return u'"{}": {}'.format(self.name, self.friend_id)

    def __repr__(self):
        return str(self)


class ComService(object):
    def __init__(self, file_download_monitor):
        # job id -> (process, progress_array)
        self.jobs = {}
        self.last_job_id = 0

        self.file_download_monitor = file_download_monitor

    def clean_jobs(self):
        for job_id, job in self.jobs.items():
            if not job.is_running():
                logger.info("Removing completed job {}: {}".format(job_id, str(job)))
                del self.jobs[job_id]

    def stop(self):
        logger.info("Requesting stop")
        for job in self.jobs.itervalues():
            job.terminate()

        for job in self.jobs.itervalues():
            job.join_process()

    def _check_for_already_running(self, job):
        for e_job in self.jobs.itervalues():
            if e_job.name == job.name and e_job.friend_id == job.friend_id and e_job.is_running():
                raise ValueError("A job of this type is already running, can't start a second one")

    def fetch_updates_from_friends(self, friend_ids):
        for index, friend_id in enumerate(friend_ids):
            try:
                self.fetch_updates_from_friend(friend_id)
                if index != len(friend_ids)-1:
                    # it seems that twisted sometimes has a problem when triggering all connections at once
                    time.sleep(DELAY_BETWEEN_UPDATE_LAUNCHES)
            except ValueError:
                pass

    def fetch_updates_from_friend(self, friend_id):
        friend_id = int(friend_id)
        job = Job("fetch_updates", friend_id)
        self._check_for_already_running(job)

        p = Process(target=exec_fetch_updates, args=(friend_id, job.current_phase, job.progress_array))
        p.start()
        job.process = p

        self.last_job_id += 1
        self.jobs[self.last_job_id] = job

        return self.last_job_id

    def is_job_running(self, job_id):
        if job_id not in self.jobs:
            return False
        job = self.jobs[job_id]
        return job.is_running()

    def get_job_progress(self, job_id):
        if job_id not in self.jobs:
            return None, None
        job = self.jobs[job_id]
        arr = job.progress_array
        return arr[0], arr[1]

    def cancel_job(self, job_id):
        if job_id not in self.jobs:
            return

        job = self.jobs[job_id]
        job.terminate()

    def get_job_list(self):
        result = []
        for job_id, job in self.jobs.iteritems():
            result.append({'id': job_id,
                           'name': job.name,
                           'friend_id': job.friend_id,
                           'is_running': job.is_running(),
                           'start_time': job.start_time,
                           'current_phase': com.strategies.strategy_phase_name(job.current_phase.value)})
        return result
        
    def get_number_of_running_jobs(self):
        return len([job for job in self.jobs.itervalues() if job.is_running()])

    def lock_file_for_fetching(self, file_hash):
        """ @returns "locked" for lock successful, "busy" for lock busy, and "completed" for download already completed
        """

        code_translation = {
            None: 'completed',
            True: 'locked',
            False: 'busy'
        }

        lock_result = self.file_download_monitor.try_lock(file_hash)
        return code_translation[lock_result]

    def release_file_after_fetching(self, file_hash, success):
        if success:
            self.file_download_monitor.set_completed_and_unlock(file_hash)
        else:
            self.file_download_monitor.unlock(file_hash)

    # functions for external job creation
    def register_job(self, name, friend_id):
        """ for externally created jobs: tries to create a job, throws ValueError if not possible """
        friend_id = int(friend_id)
        job = Job(name, friend_id)
        self._check_for_already_running(job)

        self.last_job_id += 1
        self.jobs[self.last_job_id] = job
        job.current_phase.value = com.strategies.strategy_phase_id('incoming_connection')
        return self.last_job_id

    def unregister_job(self, job_id):
        """ for externally created jobs: signals that the job is completed """
        logging.info("Unregister job called, job is {}".format(job_id))
        if job_id not in self.jobs:
            return
        job = self.jobs[job_id]
        job.is_running_if_no_process = False

    def update_job_progress(self, job_id, current_phase_id, current_items_to_do, current_items_done):
        """ for externally created jobs: signals progress """
        if job_id not in self.jobs:
            return
        job = self.jobs[job_id]
        job.current_phase.value = current_phase_id
        job.progress_array[0] = current_items_to_do
        job.progress_array[1] = current_items_done


def build():
    file_download_monitor = filedownloadmonitor.FileDownloadMonitor()
    return ComService(file_download_monitor)


def exec_fetch_updates(friend_id, current_phase_store, progress_array):
    # noinspection PyUnresolvedReferences
    sys.excepthook = Pyro4.util.excepthook

    db = pyrosetup.pydbserver()
    comm_data_store = pyrosetup.comm_data_store()
    com_service = pyrosetup.comservice()

    if db.ping() != "pong":
        raise ValueError("Unable to talk to server, is it running?")

    friend_id = int(friend_id)
    friend = db.get_friend(friend_id)
    if not friend:
        raise ValueError("No friend by that id found")

    friend_comm_data = comm_data_store.get_comm_data(friend_id)
    cc = com.client.ComClient(db, friend_id, friend_comm_data, com_service)

    file_server = pyrosetup.fileserver()

    strategy = com.master_strategy.construct_master_client_strategy(db, com_service, file_server)

    def update_progress(current_phase, progress_arg_1, progress_arg_2):
        current_phase_store.value = current_phase
        progress_array[0] = progress_arg_1
        progress_array[1] = progress_arg_2

    update_progress(com.strategies.strategy_phase_id('connecting'), 0, 0)
    strategy.set_progress_callback(update_progress)

    cc.connect_and_execute(strategy)
