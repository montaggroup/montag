import os
import logging
from pydb import title

from whoosh.index import create_in, open_dir
from whoosh.fields import *
from whoosh.qparser import QueryParser
from whoosh import analysis

logger = logging.getLogger('whoosh_index')

MAX_NUMBER_OF_SEARCH_RESULTS = 500


def build(db_dir):
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    index_dir = os.path.join(db_dir, "whoosh")

    if os.path.exists(index_dir):
        index = open_dir(index_dir)
    else:
        all_words_ana = analysis.StandardAnalyzer(stoplist=None, minsize=0)

        schema = Schema(
            any_field=TEXT(analyzer=all_words_ana),
            title=TEXT(analyzer=all_words_ana),
            subtitle=TEXT(analyzer=all_words_ana),
            author=TEXT(analyzer=all_words_ana),
            edition=TEXT(analyzer=all_words_ana),
            principal_language=TEXT(analyzer=all_words_ana),
            publication_year=NUMERIC(),
            tag=KEYWORD(commas=True, scorable=True, lowercase=True),
            guid=ID(stored=True, unique=True),
            merge_db_id=NUMERIC(stored=True),
            type=NUMERIC()
        )

        os.mkdir(index_dir)
        index = create_in(index_dir, schema)

    return WhooshIndex(index)


def simplify_query(query):
    query = query.strip()
    if query.startswith('* '):
        return query[2:]
    return query


class WhooshIndex(object):
    def __init__(self, whoosh_index):
        self.index = whoosh_index

    def add_enriched_tomes(self, enriched_tomes):
        if not enriched_tomes:
            return

        writer = self.index.writer()
        for tome in enriched_tomes:
            full_title_text = title.coalesce_title(tome['title'], tome['subtitle'])

            author_text = u' '.join([author['name'] for author in tome['authors']])

            tag_text = u','.join(tag['tag_value'] for tag in tome['tags'])

            all_in_one = ' '.join([full_title_text, author_text, tag_text])

            publication_year = None
            try:
                publication_year = int(tome['publication_year'])
            except (ValueError, TypeError):
                pass

            writer.update_document(any_field=all_in_one,
                                   title=tome['title'],
                                   subtitle=tome['subtitle'],
                                   edition=tome['edition'],
                                   author=author_text,
                                   tag=tag_text,
                                   publication_year=publication_year,
                                   principal_language=tome['principal_language'],
                                   guid=tome['guid'],
                                   merge_db_id=tome['id'],
                                   type=tome['type'])
        logger.debug("Committing writer")
        writer.commit(MERGE_CUSTOM)
        logger.debug("Commit done")

    def remove_tomes(self, tome_guids):
        if not tome_guids:
            return

        writer = self.index.writer()
        for guid in tome_guids:
            writer.delete_by_term('guid', guid)
            pass

        writer.commit()

    def search_tomes(self, query_text):
        query_text = simplify_query(query_text)
        logger.info(u'Searching for "%s"', query_text)
        parser = QueryParser('any_field', self.index.schema)
        my_query = parser.parse(query_text)
        with self.index.searcher() as searcher:
            results = list(searcher.search(my_query, limit=MAX_NUMBER_OF_SEARCH_RESULTS))
            merge_db_ids = [r['merge_db_id'] for r in results]
            logger.info(u'Found %s results', len(merge_db_ids))
            return merge_db_ids


# noinspection PyPep8Naming
def MERGE_CUSTOM(writer, segments):
    """This policy merges small segments, where "small" is defined using a
    heuristic based on the fibonacci sequence.
    """

    from whoosh.reading import SegmentReader
    from whoosh.util import fib

    unchanged_segments = []
    segments_to_merge = []

    sorted_segment_list = sorted(segments, key=lambda s: s.doc_count_all())
    total_docs = 0

    log_stats = False

    merge_point_found = False
    for i, seg in enumerate(sorted_segment_list):
        count = seg.doc_count_all()
        if count > 0:
            total_docs += count

        if log_stats:
            logger.debug("%s: %s/%s, fib %s", i, count, total_docs, fib(i+5))

        if merge_point_found:
            unchanged_segments.append(seg)
        else:
            segments_to_merge.append((seg, i))
            if i > 3 and total_docs < fib(i + 5):
                logger.debug("Merge point found at %s - %s", i, total_docs)
                merge_point_found = True

    if merge_point_found and len(segments_to_merge) > 1:
        for seg, i in segments_to_merge:
            logger.info("Merging segment %s having size %s", i, seg.doc_count_all())
            reader = SegmentReader(writer.storage, writer.schema, seg)
            writer.add_reader(reader)
            reader.close()
        return unchanged_segments
    else:
        logger.debug("No merge point found, no merge yet")
        return segments
