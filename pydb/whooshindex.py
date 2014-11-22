import os
import logging
import title

from whoosh.index import create_in, open_dir
from whoosh.fields import *
from whoosh.qparser import QueryParser
from whoosh import analysis

logger = logging.getLogger('whoosh_index')

MaxNumberOfSearchResults = 500


class WhooshIndex:
    def __init__(self, db_dir):
        if not os.path.exists(db_dir):
            os.mkdir(db_dir)
        self.index_dir = os.path.join(db_dir, "whoosh")
        # logger.info("Whoosh index located in %s" % self.index_dir)

        if os.path.exists(self.index_dir):
            self.index = open_dir(self.index_dir)
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

            os.mkdir(self.index_dir)
            self.index = create_in(self.index_dir, schema)

    def add_enriched_tomes(self, enriched_tomes):
        if not enriched_tomes:
            return

        writer = self.index.writer()
        for tome in enriched_tomes:
            full_title_text = title.coalesce_title(tome['title'], tome['subtitle'])

            # @todo add pseudonyms
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
        logger.info("Committing writer")
        writer.commit()
        logger.info("Commit done")

    def remove_tomes(self, tome_guids):
        if not tome_guids:
            return

        writer = self.index.writer()
        for guid in tome_guids:
            writer.delete_by_term('guid', guid)
            pass

        writer.commit()

    def search_tomes(self, query_text):
        logger.info("Searching for '%s'" % query_text)
        parser = QueryParser("any_field", self.index.schema)
        my_query = parser.parse(query_text)
        with self.index.searcher() as searcher:
            results = list(searcher.search(my_query, limit=MaxNumberOfSearchResults))
            merge_db_ids = [r['merge_db_id'] for r in results]
            logger.info("Found %d results" % len(merge_db_ids))
            return merge_db_ids
