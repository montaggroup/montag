import unittest
import hashlib
import pydb.ebook_metadata_tools.pdf as pdf
import cStringIO
from pydb.testing.integration_tests import get_test_data_path


class TestPdfStripIdempotency(unittest.TestCase):

    def test_multi_strip(self):
        with open(get_test_data_path('pg1661.pdf'), 'rb') as f:
            original_data = f.read()

        print "Original hash         : {}, size {}".format(hashlib.sha256(original_data).hexdigest(),
                                                           len(original_data))

        # hash once for reference
        test_data, reference_hash = strip_and_hash(original_data)
        if test_data is None:
            print "Hashing not possible, aborting"
            return

        print "Hash after stripping  : {}, size {}".format(reference_hash, len(test_data))
        dump_file(0, test_data)

        for i in range(10):
            stripped_data, file_hash = strip_and_hash(test_data)
            print "hash after iteration {}: {}, size {}".format(i, file_hash, len(stripped_data))
            dump_file(i, stripped_data)

            self.assertEqual(file_hash, reference_hash, "Hash compare at iteration {} should match".format(i))

            test_data = stripped_data


def dump_file(index, data):
        do_dumps = False
        if do_dumps:
            return
        with open(get_test_data_path('out_{}.pdf'.format(index)), 'wb') as f:
            f.write(data)


def strip_and_hash(test_data):
    in_stream = cStringIO.StringIO(test_data)
    out_stream = cStringIO.StringIO()
    if not pdf.clear_metadata(in_stream, out_stream):
        return None, None
    result_data = out_stream.getvalue()
    file_hash = hashlib.sha256(result_data).hexdigest()
    return result_data, file_hash


if __name__ == '__main__':
    unittest.main()
