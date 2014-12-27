# coding: utf8
import Pyro4
import os
import sys
import copy

web2py_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)))
pydb_dir = web2py_dir
for i in range(0, 4):
    pydb_dir, _ = os.path.split(pydb_dir)

if not pydb_dir in sys.path:
    sys.path.append(pydb_dir)

import pydb
import pydb.network_params
from pydb.network_params import is_relevant, relevant_items
import pydb.title
import pydb.config
import pydb.pyrosetup

sys.excepthook = Pyro4.util.excepthook
pdb = pydb.pyrosetup.pydbserver()

cfg_tags_minimum_display_fidelity = 20.0

def db_str_to_form(a_string):
    if not a_string:
        return ""
    return unicode(a_string).encode('utf-8')

def has_cover(tome_id):
    tome_file = pdb.get_best_relevant_cover_available(tome_id)
    return tome_file is not None

def trim_joblist(joblist, target_size):
    result = []
    j = list(joblist)
    j.reverse()
    for job in j:
        if len(result) < target_size or job['is_running']:
            result.append(job)
    result.reverse()
    return result


def add_job_infos_to_friends_dict(friends_by_id, com_service, jobs):
    for j in jobs:
        job_info=copy.deepcopy(j)
        job_info['progress'] =  progress_text(com_service, job_info['id'], job_info['current_phase'])
        friend_id = int(job_info['friend_id'])
        if friend_id in friends_by_id:
            joblist = friends_by_id[friend_id]['jobs']
            joblist.append(job_info)
            if len(joblist) > 2:
                joblist = trim_joblist(joblist, 2)
                friends_by_id[friend_id]['jobs']=joblist


def progress_text(com_service, job_id, current_phase):
    arg1, arg2 = com_service.get_job_progress(job_id)

    if current_phase == 'providing':
        docs_provided, files_provided = arg1, arg2
        return "{} docs, {} files".format(docs_provided, files_provided)
    
    items_to_do, items_done = arg1, arg2
    if items_to_do <= 0:
        return ""
    
    return "{}/{}".format(items_done, items_to_do)
        

def format_job_status(job_info):
    job_status = "completed" if not job_info['is_running'] else ""
    if job_info['current_phase'] != 'completed':
        job_status += " " + nice_name(job_info['current_phase'])
    job_status += " "+job_info['progress']
    return job_status


response.breadcrumb_bar = request.function.replace('_', ' ').title()

_friend_name_cache = {0: 'You'}


def friend_name(friend_id):
    if friend_id not in _friend_name_cache:
        friend = pdb.get_friend(friend_id)
        _friend_name_cache[friend_id] = friend['name']

    return _friend_name_cache[friend_id]


def get_used_languages():
    return pdb.get_used_languages()

