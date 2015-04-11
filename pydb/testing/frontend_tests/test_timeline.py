import unittest
import service_helpers
import web2py_helpers

web2py_helpers.prepare_web2py()


class TestTimeLine(unittest.TestCase):
    def setUp(self):
        self.timeline = web2py_helpers.build_request('default', 'timeline')
        service_helpers.start_services()

    def tearDown(self):
        service_helpers.stop_services()

    def test_empty_timeline_returns_empty_list_and_view_renders(self):
        res = self.timeline.execute()
        self.assertIn('tome_info', res)

        html = self.timeline.render_result()
        self.assertIn('Timeline ', html)

if __name__ == '__main__':
    unittest.main()
