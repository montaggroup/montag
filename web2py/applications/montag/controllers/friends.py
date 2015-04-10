# coding: utf8
if False:
    from web2py.applications.montag.models.ide_fake import *

from pydb import pyrosetup


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
    friends_by_id = {}
    for friend in friends:
        friend['jobs'] = []
        friend_id = int(friend['id'])
        friends_by_id[friend_id]=friend
    try:
        com_service = pydb.pyrosetup.comservice()
        jobs = com_service.get_job_list()
        add_job_infos_to_friends_dict(friends_by_id, com_service, jobs)

    except Pyro4.errors.CommunicationError:
        pass

    return {'friends': friends, 'update_infos': update_infos,
            'is_locking_active': is_locking_active, 'is_locked': is_locked }


def _friend_edit_form(friend, comm_data):
    values = {
        'hostname': '',
        'port': '1234',
        'secret': '*' * 6,
        'confirm_secret': '-' * 6,
        'type': 'tcp_aes',
        'can_connect_to': friend['can_connect_to'] == 1
    }

    if comm_data:
        for key, value in comm_data.iteritems():
            if key != 'secret':
                values[key] = db_str_to_form(value)

    form = SQLFORM.factory(
        Field('name', requires=IS_NOT_EMPTY(), default=db_str_to_form(friend['name']),
              comment=TOOLTIP('Enter something to tell your friends apart.')),
        Field('secret', 'password', requires=IS_STRONG(min=8, special=0, upper=0), default='*'*6,
              comment=TOOLTIP('Please enter a reasonably long password (10+ characters) and share it '
                              'with your friend. It will be used to identify each other and allow your '
                              'friend to sync.')),
        Field('confirm_secret', 'password', requires=IS_EQUAL_TO(request.vars.secret,
              error_message='secrets do not match'), default='-'*6),
        Field('can_connect_to', type='boolean', default=values['can_connect_to'],
              comment=TOOLTIP('If you enable this, Montag will try to connect to this friend '
                              'if you press the button "Update All".')),
        Field('hostname', requires=IS_NOT_EMPTY(), default=values['hostname'],
              comment=TOOLTIP('Please enter the IP-address or internet host name of your friend')),
        Field('port', requires=IS_INT_IN_RANGE(1024, 65535, error_message='invalid port'), default=values['port'],
              comment=TOOLTIP('Please enter the (TCP) port number your friend has made his/her Montag '
                              'instance available under.')),
        Field('type', default=values['type'], comment=TOOLTIP('Connection type. Currently only "tcp_aes" is supported.'))
    )
    return form


def _friend_add_form():
    form = SQLFORM.factory(Field('name', requires=IS_NOT_EMPTY()), submit_button='Save')

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
            value = read_form_field(form, f)
            if f != 'secret' or (f == 'secret' and value.count('*') != len(value)):
                comm_data[f] = value

        cds = pyrosetup.comm_data_store()
        cds.set_comm_data(friend_id, comm_data)
        
        new_name = read_form_field(form, 'name')
        if new_name != friend['name']:
            friend['name'] = new_name
            pdb.set_friend_name(friend['id'], friend['name'])
            
        new_can_connect_to = '1' if read_form_field(form, 'can_connect_to') else '0'
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
    form = SQLFORM.factory()

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
        friend_id = pdb.add_friend(read_form_field(form, 'name'))
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
    form = SQLFORM.factory(Field('unlock_password', 'password', requires=IS_NOT_EMPTY(), default=''),
                           submit_button='Unlock')
    return form


@auth.requires_login()
def unlock_comm_data():
    form = _unlock_comm_data_form()
    response.title = 'Unlock Comm Data'
    if form.process(keepvalues=True).accepted:
        password = read_form_field(form, 'unlock_password')
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
