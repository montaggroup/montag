# coding: utf8

def show_stats():
    merge_stats = db.get_merge_statistics()
    local_stats = db.get_local_statistics()
    tome_stats = db.get_tome_statistics()
    response.title = "Database Statistics - Montag"

    return {'merge_stats': merge_stats, 'local_stats': local_stats, 'tome_stats': tome_stats}


def show_database_check():
    check_result = db.check_databases_for_consistency_problems()
    response.title = "Database Check Result - Montag"
    
    return {'check_result': check_result}

def show_database_content_check():
    check_result = db.check_merge_db_for_content_problems()
    response.title = "Database Content Check Result - Montag"
    
    return {'check_result': check_result}
