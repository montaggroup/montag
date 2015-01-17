# coding: utf8

from pydb import pyrosetup


@auth.requires_login()
def index():
    return dict(message='hello from friends.py')


@auth.requires_login()
def list_friends():
    response.title = 'Friends - Montag'
    
    comm_data_store = pydb.pyrosetup.comm_data_store()
    is_locking_active = comm_data_store.is_locking_active()
    is_locked = False
    if is_locking_active:
        is_locked = comm_data_store.is_locked()

    friends = pdb.get_friends()
    update_infos = [pdb.get_friend_last_query_dates(friend['id']) for friend in friends]
    friends_by_id={}
    for friend in friends:
        friend['jobs']=[]
        friend_id = int(friend['id'])
        friends_by_id[friend_id]=friend
    try:
        com_service = pydb.pyrosetup.comservice()
        jobs = com_service.get_job_list()
        add_job_infos_to_friends_dict(friends_by_id, com_service, jobs)

    except Pyro4.errors.CommunicationError:
        pass

    return {'friends': friends, 'update_infos': update_infos, 'is_locking_active': is_locking_active, 'is_locked': is_locked }


def _friend_edit_form(friend, comm_data):
    fields = [
        Field('name',requires=IS_NOT_EMPTY(), default=db_str_to_form(friend['name'])),
        Field('can_connect_to', type='boolean', default=friend['can_connect_to']==1)
    ]
    
    if comm_data:
        for key in comm_data.keys():
            if key == 'secret':
                fields.append(Field(key, 'password', requires=IS_STRONG(min=8, special=0, upper=0), default='*'*6))
                fields.append(Field('confirm_secret', 'password', requires=IS_EQUAL_TO(request.vars.secret,
                                   error_message='secrets do not match'), default='-'*6))
            elif key == 'port':
                fields.append(Field('port', requires=IS_INT_IN_RANGE(1024, 65535, error_message='invalid port'), default=db_str_to_form(comm_data[key])))
            else:
                fields.append(Field(key, default=db_str_to_form(comm_data[key])))
    else:
        fields.append(Field('type', default='tcp_aes'))
        fields.append(Field('port', requires=IS_INT_IN_RANGE(1024, 65535, error_message='invalid port'), default='1234'))
        fields.append(Field('hostname', requires=IS_NOT_EMPTY(), default=''))
        fields.append(Field('secret', 'password', requires=IS_STRONG(min=8, special=0, upper=0), default='*'*6))
        fields.append(Field('confirm_secret', 'password', requires=IS_EQUAL_TO(request.vars.secret,
                       error_message='secrets do not match'), default='-'*6))
    form = SQLFORM.factory(*fields)
    return form


def _friend_add_form():
    form = SQLFORM.factory(
        Field('name',requires=IS_NOT_EMPTY()),
    )
    return form

def _load_comm_data(friend_id):
    cds = pyrosetup.comm_data_store()
    comm_data = cds.get_comm_data(friend_id)
    if comm_data is None:
        comm_data = dict()
    if comm_data and not comm_data.has_key('secret'):
        comm_data['secret'] = ''
    return comm_data

def _load_friend(friend_id):
    friend = pdb.get_friend(friend_id)
    return friend


@auth.requires_login()
def edit_friend():
    friend_id = request.args[0]
    friend = _load_friend(friend_id)
    comm_data = _load_comm_data(friend_id)

    form = _friend_edit_form(friend, comm_data)
    response.title = u'Edit friend {} - Montag'.format(friend['name'])

    if form.process(keepvalues=True).accepted:
        comm_data = _load_comm_data(friend_id)

        comm_data_fields = ['hostname', 'type', 'port', 'secret']
        for f in comm_data_fields:
            if type(form.vars[f]) == str:
                if f != 'secret' or (f == 'secret' and form.vars[f].count('*') != len(form.vars[f])):
                    comm_data [f] = str(form.vars[f]).decode('utf-8')
            else:
                comm_data[f] = form.vars[f]
        cds = pyrosetup.comm_data_store()
        cds.set_comm_data(friend_id, comm_data)
        
        new_name = form.vars['name'].decode('utf-8')
        if new_name != friend['name']:
            friend['name'] = new_name
            pdb.set_friend_name(friend['id'], friend['name'])
            
        new_can_connect_to = '1' if form.vars['can_connect_to'] else '0'
        if new_can_connect_to != friend['can_connect_to']:
            friend['can_connect_to'] = new_can_connect_to
            pdb.set_friend_can_connect_to(friend['id'], new_can_connect_to)

        comm_data = _load_comm_data(friend_id)
        response.flash = 'Stored new values'
        redirect('../list_friends')

    elif form.errors:
        response.flash = 'comm data has errors'
    return dict(form=form, comm_data=comm_data, friend_id=friend_id)


def _friend_remove_form():
    form = SQLFORM.factory(
    )
    return form


@auth.requires_login()
def remove_friend():
    friend_id = request.args[0]
    friend = _load_friend(friend_id)
    
    form = _friend_remove_form()
    if friend is not None:
        response.title = u'Remove friend {} - Montag'.format(friend['name'])

    if form.process(keepvalues=True).accepted:
        pdb.remove_friend(int(friend_id))
        redirect('../list_friends')

    elif form.errors:
        response.flash = 'form  has errors'
    return dict(form=form, friend=friend)


@auth.requires_login()
def add_friend():
    form = _friend_add_form()
    response.title = 'Add friend'
    if form.process(keepvalues=True).accepted:
        friend_id = pdb.add_friend(form.vars['name'].decode('utf-8'))
        response.flash = 'Added new friend'
        redirect(URL('edit_friend', args=[friend_id]))

    elif form.errors:
        response.flash = 'form has errors'
    return dict(form=form)


@auth.requires_login()
def fetch_updates():
    friend_id = request.args[0]
    com_service = pydb.pyrosetup.comservice()
    try:
        com_service.fetch_updates(friend_id)
        redirect('../list_friends')
    except ValueError as e:
        session.flash = e.message
        redirect('../list_friends')


@auth.requires_login()
def fetch_updates_all():
    com_service = pydb.pyrosetup.comservice()
    friends = pdb.get_friends()
    for friend in friends:
        try:
            if friend['can_connect_to']:
                com_service.fetch_updates(friend['id'])
        except ValueError:  # already running
            pass
    redirect('list_friends')

def _unlock_comm_data_form():
    form = SQLFORM.factory(
        Field('unlock_password', 'password', requires=IS_NOT_EMPTY(), default=''),
    )
    return form


@auth.requires_login()
def unlock_comm_data():
    form = _unlock_comm_data_form()
    response.title = 'Unlock Comm Data'
    if form.process(keepvalues=True).accepted:
        password = form.vars['unlock_password'].decode('utf-8')
        cds = pyrosetup.comm_data_store()
        try:
            cds.unlock(str(password))
            redirect('list_friends')
        except KeyError as e:
            response.flash = 'Invalid password'

    elif form.errors:
        response.flash = 'form has errors'
    return dict(form=form)


@auth.requires_login()
def clear_completed_jobs():
    com_service = pydb.pyrosetup.comservice()
    com_service.clean_jobs()
    redirect('list_friends')
