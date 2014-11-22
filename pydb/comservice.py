from multiprocessing import Process, Array, Value
import com.client
import com.master_strategy
import com.strategies
import Pyro4
import sys
import time
import logging


logger = logging.getLogger('comservice')


class Job():
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
        return "'{}': {}".format(self.name, self.friend_id)

    def __repr__(self):
        return str(self)


class ComService():
    def __init__(self):
        # job id -> (process, progress_array)
        self.jobs = {}
        self.last_job_id = 0

        # \todo replace this with the file monitor
        self.locked_files = set()
        self.completed_files = set()

    def clean_jobs(self):
        for job_id, job in self.jobs.items():
            if not job.is_running():
                print "Removing completed job {}: {}".format(job_id, str(job))
                del self.jobs[job_id]

    def stop(self):
        print "Requesting stop"
        for job in self.jobs.itervalues():
            job.terminate()

        for job in self.jobs.itervalues():
            job.join_process()

    def _check_for_already_running(self, job):
        for e_job in self.jobs.itervalues():
            if e_job.name == job.name and e_job.friend_id == job.friend_id and e_job.is_running():
                raise ValueError("A job of this type is already running, can't start a second one")

    def fetch_updates(self, friend_id):
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
        if not job_id in self.jobs:
            return False
        job = self.jobs[job_id]
        return job.is_running()

    def get_job_progress(self, job_id):
        if not job_id in self.jobs:
            return None, None
        job = self.jobs[job_id]
        arr = job.progress_array
        return arr[0], arr[1]

    def cancel_job(self, job_id):
        if not job_id in self.jobs:
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
        if file_hash in self.completed_files:
            # print "lock_file_for_fetching: {} {}".format(file_hash,"completed")
            return "completed"

        if file_hash in self.locked_files:
            # print "lock_file_for_fetching: {} {}".format(file_hash,"busy")
            return "busy"

        self.locked_files.add(file_hash)
        # print "lock_file_for_fetching: {} {}".format(file_hash,"locked")
        return "locked"

    def release_file_after_fetching(self, file_hash, success):
        if not file_hash in self.locked_files:
            raise KeyError("Hash {} not locked".format(file_hash))

        if success:
            # print "release_file_after_fetching: {} {}".format(file_hash,"after success")
            self.completed_files.add(file_hash)
        else:
            # print "release_file_after_fetching: {} {}".format(file_hash,"after fail")
            pass

        self.locked_files.remove(file_hash)

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
        if not job_id in self.jobs:
            return
        job = self.jobs[job_id]
        job.is_running_if_no_process = False

    def update_job_progress(self, job_id, current_phase_id, current_items_to_do, current_items_done):
        """ for externally created jobs: signals progress """
        if not job_id in self.jobs:
            return
        job = self.jobs[job_id]
        job.current_phase.value = current_phase_id
        job.progress_array[0] = current_items_to_do
        job.progress_array[1] = current_items_done
        
        


def exec_fetch_updates(friend_id, current_phase_store, progress_array):
    # noinspection PyUnresolvedReferences
    sys.excepthook = Pyro4.util.excepthook
    import pyrosetup

    db = pyrosetup.pydbserver()
    comm_data_store = pyrosetup.comm_data_store()
    comservice = pyrosetup.comservice()

    if db.ping() != "pong":
        raise ValueError("Unable to talk to server, is it running?")

    friend_id = int(friend_id)
    friend = db.get_friend(friend_id)
    if not friend:
        raise ValueError("No friend by that id found")

    friend_comm_data = comm_data_store.get_comm_data(friend_id)
    cc = com.client.ComClient(db, friend_id, friend_comm_data, comservice)

    strategy = com.master_strategy.construct_master_client_strategy(db, comservice)

    def update_progress(current_phase, progress_arg_1, progress_arg_2):
        current_phase_store.value = current_phase
        progress_array[0] = progress_arg_1
        progress_array[1] = progress_arg_2

    update_progress(com.strategies.strategy_phase_id('connecting'), 0, 0)
    strategy.set_progress_callback(update_progress)

    cc.connect_and_execute(strategy)
