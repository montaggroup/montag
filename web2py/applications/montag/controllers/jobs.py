# coding: utf8
if False:
    from web2py.applications.montag.models.ide_fake import *


@auth.requires_login()
def index(): return dict(message="hello from jobs.py")

def _friend_name(friend_id):
    friend = pdb.get_friend(friend_id)
    return friend['name']


@auth.requires_login()
def list_jobs():
    response.title = "List Jobs - Montag"

    com_service = pydb.pyrosetup.comservice()
    job_infos = com_service.get_job_list()
    for job_info in job_infos:
        job_info['friend_name'] = _friend_name(job_info['friend_id'])
        job_info['progress'] = progress_text(com_service, job_info['id'],  job_info['current_phase'])
    return dict(job_infos=job_infos)


@auth.requires_login()
def clear_completed():
    com_service = pydb.pyrosetup.comservice()
    com_service.clean_jobs()
    redirect('list_jobs')


@auth.requires_login()
def cancel_job():
    job_id = request.args[0]
    com_service = pydb.pyrosetup.comservice()
    com_service.cancel_job(int(job_id))
    redirect('../list_jobs')
