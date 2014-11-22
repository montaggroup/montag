import logging

logger = logging.getLogger("com.session")

FILE_TRANSFER_CHUNK_SIZE = 1024 * 1024
KEEP_ALIVE_SEND_INTERVAL_SECONDS = 120

def send_chunked_file(session, file_extension, file_hash, file_stream):
    start_pos = 0
    chunk = file_stream.read(FILE_TRANSFER_CHUNK_SIZE)
    while chunk:
        next_chunk = file_stream.read(FILE_TRANSFER_CHUNK_SIZE)

        stop_pos = start_pos + len(chunk)
        more_chunks_follow = bool(next_chunk)
        logger.info("Sending bytes {}-{} total for hash {}, mcf: {}".format
                    (start_pos, stop_pos - 1, file_hash, more_chunks_follow))
        session.deliver_file(file_hash, file_extension, chunk,
                             more_parts_follow=more_chunks_follow)
        start_pos = stop_pos

        chunk = next_chunk