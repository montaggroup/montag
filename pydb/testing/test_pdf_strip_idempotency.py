import unittest
import hashlib
import pydb.ebook_metadata_tools.pdf as pdf
import cStringIO

class TestPdfStripIdempotency(unittest.TestCase):

    def test_multi_strip(self):
        with open('test_data/pg1661.pdf', 'rb') as f:
            test_data = f.read()

        print "Original hash         : {}, size {}".format(hashlib.sha256(test_data).hexdigest(), len(test_data))

        # hash once for reference
        test_data, reference_hash = strip_and_hash(test_data)
        print "Hash after stripping  : {}, size {}".format(reference_hash, len(test_data))

        for i in range(10):
            stripped_data, file_hash = strip_and_hash(test_data)
            print "hash after iteration {}: {}, size {}".format(i, file_hash, len(stripped_data))

            self.assertEqual(file_hash, reference_hash, "Hash compare at iteration {} should match".format(i))

            test_data = stripped_data

            #with open('test_data/out_{}.pdf'.format(i), 'wb') as f:
            #    f.write(result_data)


def strip_and_hash(test_data):
    in_stream = cStringIO.StringIO(test_data)
    out_stream = cStringIO.StringIO()
    pdf.clear_metadata(in_stream, out_stream)
    result_data = out_stream.getvalue()
    file_hash = hashlib.sha256(result_data).hexdigest()
    return result_data, file_hash



if __name__ == '__main__':
    unittest.main()
