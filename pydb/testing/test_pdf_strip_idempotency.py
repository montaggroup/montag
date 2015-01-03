import unittest
import hashlib
import pydb.ebook_metadata_tools.pdf as pdf
import cStringIO

class TestPdfStripIdempotency(unittest.TestCase):
    def test_multi_strip(self):
        with open('test_data/no_check_in.pdf', 'rb') as f:
            test_data = f.read()

        print "original hash {}".format(hashlib.sha256(test_data).hexdigest())
        for i in range(10):
            in_stream = cStringIO.StringIO(test_data)
            out_stream = cStringIO.StringIO()
            pdf.clear_metadata(in_stream, out_stream)
            result_data = out_stream.getvalue()
            print "hash after iteration {}: {}, size {}".format(i, hashlib.sha256(result_data).hexdigest(), len(result_data))
            test_data = result_data

            with open('test_data/out_{}.pdf'.format(i), 'wb') as f:
                f.write(result_data)






if __name__ == '__main__':
    unittest.main()
