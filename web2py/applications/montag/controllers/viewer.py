# coding: utf8

def viewfile():
    tome_id = request.args[0]
    file_hash = request.args[1]

    tome_file = pdb.get_tome_file(tome_id, file_hash)
    extension=tome_file['file_extension']
    
    tome = pdb.get_tome(tome_id)
    tome_doc = pdb.get_tome_document_with_local_overlay_by_guid(tome['guid'], include_local_file_info = True, include_author_detail=True)


    return {'tome': tome_doc, 'tome_id': tome_id, 'extension': extension, 'file_hash': file_hash}
