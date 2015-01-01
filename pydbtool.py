#!/usr/bin/env python2.7

import Pyro4
import argparse
import os
import sys
import json
import ijson
import tempfile
import subprocess
import shutil
import pydb.title
import pydb.com.client
import pydb.serverlauncher as server
import logging
import pydb.pyrosetup
import getpass
import pydb.com.master_strategy

logging.basicConfig(level=logging.DEBUG)
sys.excepthook = Pyro4.util.excepthook

json_indent = 4
json_separators = (',', ': ')


def do_print_stats(args, db):
    merge_stats = db().get_merge_statistics()
    print "\nmerge.db contains:"
    print "=================="
    for key in merge_stats:
        print "{1} {0}.".format(key, merge_stats[key])

    local_stats = db().get_local_statistics()
    print "\nlocal.db contains:"
    print "=================="
    for key in local_stats:
        print "{1} {0}.".format(key, local_stats[key])


def do_add_friend(args, db):
    friend_name = args.friend_name
    db().add_friend(friend_name)
    print "Friend {} added".format(friend_name)


def do_remove_friend(args, db):
    friend_name = args.friend_name
    friend = db().get_friend_by_name(friend_name)
    if not friend:
        print >> sys.stderr, "No friend by that name, check your spelling or create a new friend using add_friend"
        return False
    friend_id = friend['id']

    db().remove_friend(friend_id)

    print "Friend {} removed".format(friend_name)


def do_list_friends(args, db):
    friends = db().get_friends()
    for friend in friends:
        print "%-3d %-20s" % (friend['id'], friend['name'])


def print_tome_details(tome_fields):
    title = pydb.title.coalesce_title(tome_fields['title'], tome_fields['subtitle'])
    print title
    print "   " + "  ".join(
        ["%s: %s" % (k, v) for (k, v) in tome_fields.iteritems() if k != 'title' and k != 'subtitle' and v])


def do_db_search(args, db):
    tomes = dict()  # id -> fields

    for keyword in args.keywords:
        result_tomes = db().find_tomes_by_title_or_author(keyword)
        for tome_fields in result_tomes:
            tomes[tome_fields['id']] = tome_fields

    for tome_id in tomes.keys():
        print_tome_details(tomes[tome_id])


def do_search(args, db):
    index_server = pydb.pyrosetup.indexserver()

    tome_ids = index_server.search_tomes(args.query)
    for tome_id in tome_ids:
        tome = db().get_tome(tome_id)
        print_tome_details(tome)


def do_update_search_index(args, db):
    index_server = pydb.pyrosetup.indexserver()
    index_server.update_index()


def do_service_fetch_updates(args, db):
    friend_name = args.friend_name
    friend = db().get_friend_by_name(friend_name)
    if not friend:
        print >> sys.stderr, "No friend by that name, check your spelling or create a new friend using add_friend"
        return False
    friend_id = friend['id']

    com_service = pydb.pyrosetup.comservice()
    job_id = com_service.fetch_updates(friend_id)
    print "Update started, job is is {}".format(job_id)


def do_service_list_jobs(args, db):
    com_service = pydb.pyrosetup.comservice()
    number = com_service.get_number_of_running_jobs()
    print "{} jobs running".format(number)

    job_infos = com_service.get_job_list()
    print "ID  Name                      Friend            Running  Current Phase    Progress"
    for job_info in job_infos:
        job_id = job_info['id']
        friend = db().get_friend(job_info['friend_id'])
        items_to_do, items_done = com_service.get_job_progress(job_id)

        progress = "Unknown"
        if items_to_do >= 0:
            progress = "{}/{}".format(items_done, items_to_do)

        print "{:<3} {:<25} {:<17} {:<7} {:<16} {}".format(job_id, job_info['name'], friend['name'],
                                                           job_info['is_running'], job_info['current_phase'], progress)


def do_service_cancel_job(args, db):
    com_service = pydb.pyrosetup.comservice()
    com_service.cancel_job(int(args.id))


def do_import(args, db):
    friend_name = args.friend_name
    friend = db().get_friend_by_name(friend_name)
    if not friend:
        print >> sys.stderr, "No friend by that name, check your spelling or create a new friend using add_friend"
        return False
    friend_id = friend['id']

    with open(args.file_name) as import_file:
        author_docs = ijson.items(import_file, 'authors.item')
        for author_doc in author_docs:
            print "Author: ", author_doc
            # \todo do bulk insert
            db().load_author_documents_from_friend(friend_id, [author_doc])

    with open(args.file_name) as import_file:
        tome_docs = ijson.items(import_file, 'tomes.item')
        for tome_doc in tome_docs:
            print "Tome: ", tome_doc
            # \todo do bulk insert
            db().load_tome_documents_from_friend(friend_id, [tome_doc])


def do_set_comm_data_tcp_plain(args, db):
    comm_data_store = pydb.pyrosetup.comm_data_store()
    friend_name = args.friend_name
    friend = db().get_friend_by_name(friend_name)
    if not friend:
        print >> sys.stderr, "No friend by that name, check your spelling or create a new friend using add_friend"
        return False
    friend_id = friend['id']

    comm_data = {'type': 'tcp_plain', 'hostname': args.hostname, 'port': args.port}
    comm_data_store.set_comm_data(friend_id, comm_data)


def do_set_comm_data_tcp_aes(args, db):
    comm_data_store = pydb.pyrosetup.comm_data_store()
    friend_name = args.friend_name
    friend = db().get_friend_by_name(friend_name)
    if not friend:
        print >> sys.stderr, "No friend by that name, check your spelling or create a new friend using add_friend"
        return False
    friend_id = friend['id']

    comm_data = {'type': 'tcp_aes', 'hostname': args.hostname, 'port': args.port, 'secret': args.secret}
    comm_data_store.set_comm_data(friend_id, comm_data)


def do_import_self(args, db):
    with open(args.file_name) as import_file:
        author_docs = ijson.items(import_file, 'authors.item')
        for author_doc in author_docs:
            print "Author: ", author_doc
            db().load_own_author_document(author_doc)

    with open(args.file_name) as import_file:
        tome_docs = ijson.items(import_file, 'tomes.item')
        for tome_doc in tome_docs:
            print "Tome: ", tome_doc
            db().load_own_tome_document(tome_doc)


def let_user_edit_document(doc, always_discard=False, detect_unchanged=True):
    (fd, filename) = tempfile.mkstemp()

    with os.fdopen(fd, "w") as doc_file:
        text_content = json.dumps(doc, indent=json_indent, separators=json_separators)
        doc_file.write(text_content)

    while True:
        rc = subprocess.call(["editor", filename])

        try:
            with open(filename) as doc_file:
                file_content = doc_file.read()
                if always_discard or (file_content.strip() == text_content.strip() and detect_unchanged):
                    print "Document unchanged, aborting edit"
                    return None

                edited_doc = json.loads(file_content)
                raw_input("Parsed successfully. Hit Enter to save, ctrl-c to abort... ")
                print "Saved."
                return edited_doc
        except ValueError, e:
            print "Json error: ", e
            raw_input("Hit Enter to edit, ctrl-c to abort... ")


def do_edit_author(args, db):
    if args.load_local:
        doc = db().get_local_author_document_by_guid(args.guid, args.ignore_fidelity_filter)
    else:
        doc = db().get_author_document_by_guid(args.guid, args.ignore_fidelity_filter)
    edited_doc = let_user_edit_document(doc, detect_unchanged=not args.load_local)
    if not edited_doc is None:
        db().load_own_author_document(edited_doc)


def do_edit_tome(args, db):
    if args.load_local:
        doc = db().get_local_tome_document_by_guid(args.guid, args.ignore_fidelity_filter)
    else:
        doc = db().get_tome_document_with_local_overlay_by_guid(args.guid, args.ignore_fidelity_filter)

    edited_doc = let_user_edit_document(doc, detect_unchanged=not args.load_local)
    if not edited_doc is None:
        db().load_own_tome_document(edited_doc)


def do_merge_db_tome_update(args, db):
    db().request_complete_tome_update(args.guid)


def do_show_tome_debug_info(args, db):
    doc = db().get_debug_info_for_tome_by_guid(args.guid)

    print json.dumps(doc, indent=json_indent, separators=json_separators)


def do_get_latest_tome_related_change(args, db):
    doc = db().get_latest_tome_related_change(args.guid)

    print json.dumps(doc, indent=json_indent, separators=json_separators)


def do_export(args, db, outfile=sys.stdout):
    outfile.write("{\n")

    outfile.write("\"authors\": [\n")
    all_author_guids = db().get_all_author_guids()

    first = True
    for author_guid in all_author_guids:
        if first:
            first = False
        else:
            outfile.write(",\n")
        author = db().get_author_document_by_guid(author_guid)
        author_json = json.dumps(author, indent=json_indent, separators=json_separators)
        outfile.write(author_json)
    outfile.write("],\n")

    outfile.write("\"tomes\": [\n")
    all_tome_guids = db().get_all_tome_guids()

    first = True
    for tome_guid in all_tome_guids:
        if first:
            first = False
        else:
            outfile.write(",\n")
        tome = db().get_tome_document_by_guid(tome_guid)
        tome_json = json.dumps(tome, indent=json_indent, separators=json_separators)
        outfile.write(tome_json)
    outfile.write("]\n")
    outfile.write("}\n")


def do_create_file_list(args, db, outfile=sys.stdout):
    tome_file_ids = db().get_file_hashes_to_request(max_results=args.max_files)
    outfile.write('\n'.join(tome_file_ids) + "\n")


def do_answer_file_list(args, db):
    filename = args.file_name
    target_dir = args.target_directory

    if not os.path.exists(target_dir):
        os.mkdir(target_dir)

    found = 0
    with open(filename) as file_list_file:
        file_server = pydb.pyrosetup.fileserver()
        for line in file_list_file:  # careful - line still contains a newline character
            local_path = file_server.get_local_file_path(line.strip())
            if local_path:
                shutil.copy(local_path, target_dir)
                found += 1
    if not found:
        os.rmdir(target_dir)

    print "%d files found" % found


def do_import_file_store(args, db):
    def insert_files(file_list):
        print "Inserting {} files".format(len(file_list))
        result = pydb.pyrosetup.fileserver().add_files_from_local_disk(file_list)
        succ = 0
        failed = 0
        for fn, file_result in result.iteritems():
            if file_result:
                succ += 1
            else:
                failed += 1
                print "Error while importing {}".format(fn)
        return succ, failed

    INSERT_BATCH_SIZE = 50

    source_dir = os.path.abspath(args.source_directory)
    success_imports = 0
    errors = 0

    files_to_add = []

    strip_files = not args.no_strip

    for root, subfolders, files in os.walk(source_dir):
        files.sort()
        subfolders.sort()
        print 'adding %d files from %s' % (len(files), root)
        for filename in files:
            file_hash, extension = os.path.splitext(filename)

            full_path = os.path.join(root, filename)

            files_to_add.append({'source_path': full_path,
                                 'extension': extension,
                                 'only_allowed_hash': file_hash,
                                 'move_file': args.delete,
                                 'strip_file': strip_files})

            if len(files_to_add) >= INSERT_BATCH_SIZE:
                succeeded, failed = insert_files(files_to_add)
                files_to_add = []
                success_imports += succeeded
                errors += failed

    if files_to_add:
        succeeded, failed = insert_files(files_to_add)
        success_imports += succeeded
        errors += failed

    print "Successfully imported {} files.".format(success_imports)

    if errors:
        print "There have been {} errors while importing.".format(errors)
        return False
    return True


def do_fetch_updates(args, db):
    main_db = db()
    friend_name = args.friend_name
    friend = main_db.get_friend_by_name(friend_name)
    if not friend:
        print >> sys.stderr, "No friend by that name, check your spelling or create a new friend using add_friend"
        return False
    friend_id = friend['id']

    comm_data_store = pydb.pyrosetup.comm_data_store()
    friend_comm_data = comm_data_store.get_comm_data(friend_id)

    com_service = pydb.pyrosetup.comservice()

    cc = pydb.com.client.ComClient(main_db, friend_id, friend_comm_data, com_service)

    file_server = pydb.pyrosetup.fileserver()

    strategy = pydb.com.master_strategy.construct_master_client_strategy(main_db, com_service, file_server)
    cc.connect_and_execute(strategy)


def do_check_databases(args, db):
    db().check_databases()


def do_fix_databases(args, db):
    db().fix_databases()


def do_rebuild_merge_db(args, db):
    print "Do not forget to rebuild the search index after this command completed."
    print "You can achieve this by deleting whoosh* in the db folder an restarting the index server."
    db().rebuild_merge_db()


def do_remove_local_tome_links_to_missing_files(args, db):
    removed = db().remove_local_tome_links_to_missing_files()
    print "Removed {} ghost files links".format(removed)


def do_create_satellite(args, db):
    insert_bulk_size = 1000

    target_dir = args.target_dir
    if not os.path.exists(target_dir):
        os.mkdir(target_dir)

    with server.Server(target_dir, port=4511, sync_mode=False, debug=False) as satellite:
        if satellite.ping() != "pong":
            print >> sys.stderr, "Unable to talk to satellite server, is it running?`"
            sys.exit(-1)

        friend_id = satellite.add_friend("source")

        all_author_guids = db().get_all_author_guids()
        authors_to_insert = []
        for author_guid in all_author_guids:
            author = db().get_author_document_by_guid(author_guid)
            authors_to_insert.append(author)

            if len(authors_to_insert) >= insert_bulk_size:
                print "Inserting %d authors into satellite" % (len(authors_to_insert))
                satellite.load_author_documents_from_friend(friend_id, authors_to_insert)
                authors_to_insert = []
        print "Inserting %d authors into satellite" % (len(authors_to_insert))
        satellite.load_author_documents_from_friend(friend_id, authors_to_insert)

        all_tome_guids = db().get_all_tome_guids()

        tomes_to_insert = []
        for tome_guid in all_tome_guids:
            tome = db().get_tome_document_by_guid(tome_guid)

            tomes_to_insert.append(tome)
            if len(tomes_to_insert) >= insert_bulk_size:
                print "Inserting %d tomes into satellite" % (len(tomes_to_insert))
                satellite.load_tome_documents_from_friend(friend_id, tomes_to_insert)
                tomes_to_insert = []

        print "Inserting {} tomes into satellite".format(len(tomes_to_insert))
        satellite.load_tome_documents_from_friend(friend_id, tomes_to_insert)

    print "Created satellite db in {}".format(args.target_dir)


def do_encrypt_comm_data(args, db):
    cds = pydb.pyrosetup.comm_data_store()

    is_locking_active = cds.is_locking_active()
    if is_locking_active:
        print >> sys.stderr, "Comm data is already encrypted."
        sys.exit(-3)

    password1 = getpass.getpass("Enter password to encrypt comm data with: ")
    password2 = getpass.getpass("Please repeat the password to encrypt comm data with: ")

    if password1 != password2:
        print >> sys.stderr, "Passwords did not match"
        sys.exit(-2)

    cds.activate_locking(password1)


def do_unlock_comm_data(args, db):
    cds = pydb.pyrosetup.comm_data_store()

    is_locking_active = cds.is_locking_active()
    if not is_locking_active:
        print >> sys.stderr, "Comm data is not encrypted, use encrypt_comm_data to encrypt it."
        sys.exit(-3)

    is_locked = cds.is_locked()
    if not is_locked:
        print >> sys.stderr, "Comm data already unlocked."
        sys.exit(-2)

    password = getpass.getpass("Enter password to unlock comm data: ")
    try:
        cds.unlock(password)
    except Exception as e:
        print >> sys.stderr, "Unable to unlock comm data, error was {}".format(e.message)
        sys.exit(-1)


def do_show_comm_data_status(args, db):
    cds = pydb.pyrosetup.comm_data_store()

    is_locking_active = cds.is_locking_active()
    if not is_locking_active:
        print "Not encrypted"
        sys.exit(1)

    print "Encrypted"
    is_locked = cds.is_locked()
    if is_locked:
        print "Locked"
        sys.exit(2)
    else:
        print "Unlocked"
        sys.exit(0)


def do_show_disk_usage(args, db):
    total, used, free = pydb.pyrosetup.fileserver().file_store_disk_usage()

    gb = 1000 * 1000 * 1000.0
    print "Total: {} GB".format(round(total / gb, 1))
    print " Used: {} GB".format(round(used / gb, 1))
    print " Free: {} GB".format(round(free / gb, 1))


parser = argparse.ArgumentParser(description='Imports/Exports documents to/from the database.')

subparsers = parser.add_subparsers(help='sub-command help')

parser_import = subparsers.add_parser('import', help='import a friend\' database')
parser_import.add_argument('friend_name', help='name of friend')
parser_import.add_argument('file_name', help='file to import')
parser_import.set_defaults(func=do_import)

parser_import_self = subparsers.add_parser('import_self', help='import into own database')
parser_import_self.add_argument('file_name', help='file to import')
parser_import_self.set_defaults(func=do_import_self)

parser_edit_author = subparsers.add_parser('edit_author', help='edit an author document')
parser_edit_author.add_argument('guid', help='author guid to edit')
parser_edit_author.add_argument('--ignore-fidelity-filter', action='store_true',
                                help='Also included sub items filtered out due to low fidelity')
parser_edit_author.add_argument('--load-local', action='store_true', help='Use local db entry as base for editing')

parser_edit_author.set_defaults(func=do_edit_author)

parser_edit_tome = subparsers.add_parser('edit_tome', help='edit an tome document')
parser_edit_tome.add_argument('guid', help='tome guid to edit')
parser_edit_tome.add_argument('--ignore-fidelity-filter', action='store_true',
                              help='Also included sub items filtered out due to low fidelity')
parser_edit_tome.add_argument('--load-local', action='store_true', help='Use local db entry as base for editing')

parser_edit_tome.set_defaults(func=do_edit_tome)

parser_show_tome_debug_info = subparsers.add_parser('show_tome_debug_info', help='shows debugging info about a tome')
parser_show_tome_debug_info.add_argument('guid', help='tome guid to show')
parser_show_tome_debug_info.set_defaults(func=do_show_tome_debug_info)

parser_merge_db_tome_update = subparsers.add_parser('merge_db_tome_update',
                                                    help='Triggers an update of the merge db info for a given tome. Should not be necessary to call at all.')
parser_merge_db_tome_update.add_argument('guid', help='tome guid to recalc')

parser_merge_db_tome_update.set_defaults(func=do_merge_db_tome_update)

parser_get_latest_tome_related_change = subparsers.add_parser('get_latest_tome_related_change',
                                                              help='shows latest change related to a certain tome')
parser_get_latest_tome_related_change.add_argument('guid', help='tome guid to show')
parser_get_latest_tome_related_change.set_defaults(func=do_get_latest_tome_related_change)

parser_export = subparsers.add_parser('export', help='export the current database for a friend')
parser_export.set_defaults(func=do_export)

parser_list_friends = subparsers.add_parser('list_friends', help='list friends help')
parser_list_friends.set_defaults(func=do_list_friends)

parser_add_friend = subparsers.add_parser('add_friend', help='add_friend help')
parser_add_friend.add_argument('friend_name', help='name of friend')
parser_add_friend.set_defaults(func=do_add_friend)

parser_remove_friend = subparsers.add_parser('remove_friend',
                                             help='removes a friend from the db(). Does not remove his opinions from mergedb - use rebuild_merge_db afterwards to achieve this. Does also not delete the foreign db file.')
parser_remove_friend.add_argument('friend_name', help='name of friend')
parser_remove_friend.set_defaults(func=do_remove_friend)

parser_db_search = subparsers.add_parser('db_search', help='Looks for tomes in the database.')
parser_db_search.add_argument('--non-fiction', '-n', dest='tome_type', help='Looks for non-fictions tomes only',
                              action='store_const', const='nonfiction')
parser_db_search.add_argument('--fiction', '-f', dest='tome_type', help='Looks for fiction tomes only',
                              action='store_const', const='fiction')
parser_db_search.add_argument('--fidelity', help='Minimum fidelity value for matches, ranging from -100 to 100',
                              type=int,
                              default='20')

parser_db_search.add_argument('keywords', nargs='+')
parser_db_search.set_defaults(func=do_db_search)

parser_search = subparsers.add_parser('search', help='Looks for tomes in search index.')
parser_search.add_argument('query', help='The whoosh query string')
parser_search.set_defaults(func=do_search)

parser_update_search_index = subparsers.add_parser('update_search_index', help='Requests a search index update.')
parser_update_search_index.set_defaults(func=do_search)

parser_print_stats = subparsers.add_parser('print_stats', help='prints statistics')
parser_print_stats.set_defaults(func=do_print_stats)

parser_create_file_list = subparsers.add_parser('create_file_list', help='creates a list of files needed')
parser_create_file_list.add_argument('--max_files', help='Maximum number of files to add to list', type=int,
                                     default='100000')
parser_create_file_list.set_defaults(func=do_create_file_list)

parser_answer_file_list = subparsers.add_parser('answer_file_list',
                                                help='creates a folder containing all files we can offer for a file list')
parser_answer_file_list.add_argument('file_name', help='name of list file')
parser_answer_file_list.add_argument('target_directory', help='directory to put found files into')
parser_answer_file_list.set_defaults(func=do_answer_file_list)

parser_import_file_store = subparsers.add_parser('import_file_store',
                                                 help='imports a folder of files from a (exported) store')
parser_import_file_store.add_argument('source_directory', help='directory to check for files')
parser_import_file_store.add_argument('--delete', '-d', action='store_true', help='delete imported files')
parser_import_file_store.add_argument('--no-strip', '-n', action='store_true',
                                      help='skip stripping of files (faster, requires a trusted clean file store)')
parser_import_file_store.set_defaults(func=do_import_file_store)

parser_set_comm_data_tcp_plain = subparsers.add_parser('set_comm_data_tcp_plain',
                                                       help='set the communication data for a friend to plain tcp with address and port')
parser_set_comm_data_tcp_plain.add_argument('friend_name', help='name of friend')
parser_set_comm_data_tcp_plain.add_argument('hostname', help='host name or ip address of friend')
parser_set_comm_data_tcp_plain.add_argument('port', help='port number of friend')
parser_set_comm_data_tcp_plain.set_defaults(func=do_set_comm_data_tcp_plain)

parser_set_comm_data_tcp_aes = subparsers.add_parser('set_comm_data_tcp_aes',
                                                     help='set the communication data for a friend to aes encrypted tcp with address and port')
parser_set_comm_data_tcp_aes.add_argument('friend_name', help='name of friend')
parser_set_comm_data_tcp_aes.add_argument('hostname', help='host name or ip address of friend')
parser_set_comm_data_tcp_aes.add_argument('port', help='port number of friend')
parser_set_comm_data_tcp_aes.add_argument('secret',
                                          help='shared secret passphrase for this friend (friend needs the same for us)')
parser_set_comm_data_tcp_aes.set_defaults(func=do_set_comm_data_tcp_aes)

parser_fetch_updates = subparsers.add_parser('fetch_updates',
                                             help='update a friend db by connecting to the friend and downloading')
parser_fetch_updates.add_argument('friend_name', help='name of friend')
parser_fetch_updates.set_defaults(func=do_fetch_updates)

parser_service_fetch_updates = subparsers.add_parser('service_fetch_updates',
                                                     help='use the com service to update a friend db by connecting to the friend and downloading')
parser_service_fetch_updates.add_argument('friend_name', help='name of friend')
parser_service_fetch_updates.set_defaults(func=do_service_fetch_updates)

parser_get_service_list_jobs = subparsers.add_parser('service_list_jobs',
                                                     help="shows the list of currently running jobs via com service ")
parser_get_service_list_jobs.set_defaults(func=do_service_list_jobs)

parser_service_cancel_job = subparsers.add_parser('service_cancel_job',
                                                  help="cancel a com service job identified by id")
parser_service_cancel_job.add_argument('id', help='job id')
parser_service_cancel_job.set_defaults(func=do_service_cancel_job)

parser.check_database = subparsers.add_parser('check_databases', help='instructs the server to check the databases')
parser.check_database.set_defaults(func=do_check_databases)

parser.check_database = subparsers.add_parser('fix_databases',
                                              help='instructs the server to try to fix some database inconsistencies by rebuilding the affected parts of merge db')
parser.check_database.set_defaults(func=do_fix_databases)

parser.rebuild_merge_db = subparsers.add_parser('rebuild_merge_db', help='instructs the server to rebuild the merge db'
                                                                         'using the local source databases')
parser.rebuild_merge_db.set_defaults(func=do_rebuild_merge_db)

parser.encrypt_comm_data = subparsers.add_parser('encrypt_comm_data',
                                                 help='instructs the server to encrypt comm data information. Will ask for a password on the console.')
parser.encrypt_comm_data.set_defaults(func=do_encrypt_comm_data)

parser.unlock_comm_data = subparsers.add_parser('unlock_comm_data',
                                                help='instructs the server to unlock encrypted comm data information for use by the services. Will ask for a password on the console')
parser.unlock_comm_data.set_defaults(func=do_unlock_comm_data)

parser.comm_data_status = subparsers.add_parser('show_comm_data_status',
                                                help='Shows the status of comm data encryption / locking')
parser.comm_data_status.set_defaults(func=do_show_comm_data_status)

parser.disk_usage = subparsers.add_parser('show_disk_usage', help='Shows the disk usage of the file store')
parser.disk_usage.set_defaults(func=do_show_disk_usage)

parser.remove_local_tome_links_to_missing_files = \
    subparsers.add_parser('remove_local_tome_links_to_missing_files',
                          help='removes tome<->file link info from the local source database '
                               'for all files which are not locally stored at the moment. '
                               'useful for removing ghost file links. Do not use if you have a metadata-only node')
parser.remove_local_tome_links_to_missing_files.set_defaults(func=do_remove_local_tome_links_to_missing_files)

parser_create_satellite = subparsers.add_parser('create_satellite',
                                                help='Creates a satellite db for starting a friend\'s db')
parser_create_satellite.add_argument('target_dir', help='target directory for satellite creation')
parser_create_satellite.set_defaults(func=do_create_satellite)

cmd_args = parser.parse_args()
_db = None


def get_db():
    global _db
    if _db is None:
        _db = pydb.pyrosetup.pydbserver()

        if _db.ping() != "pong":
            print >> sys.stderr, "Unable to talk to server, is it running?"
            sys.exit(-1)
    return _db


run_ok = cmd_args.func(cmd_args, get_db)
if run_ok is None:
    run_ok = True

sys.exit(0 if run_ok else -2)




