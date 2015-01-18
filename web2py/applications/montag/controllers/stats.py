# coding: utf8

@auth.requires_login()
def show_stats():
    merge_stats = pdb.get_merge_statistics()
    local_stats = pdb.get_local_statistics()
    tome_stats = pdb.get_tome_statistics()
    response.title = "Database Statistics - Montag"

    return {'merge_stats': merge_stats, 'local_stats': local_stats, 'tome_stats': tome_stats}


@auth.requires_login()
def show_database_check():
    check_result = pdb.check_databases_for_consistency_problems()
    response.title = "Database Check Result - Montag"
    
    return {'check_result': check_result}


@auth.requires_login()
def show_database_content_check():
    filter_string = None
    if request.args:
        filter_string = request.args[0]
    
    check_result = pdb.check_merge_db_for_content_problems(filter_string)
    response.title = "Database Content Check Result - Montag"
    
    return {'check_result': check_result}
