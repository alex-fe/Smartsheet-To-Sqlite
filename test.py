import unittest

from smartsheet_app import process_yml


class TestProcessYML(unittest.TestCase):

    def setUp(self):
        self.path = './config.yml'

    def test_errors(self):
        """Test that RuntimeErrors are raised if the path given is incorrect.
        """
        # if path is false
        with self.assertRaises(RuntimeError):
            process_yml('')
        # if path does not lead to config.yml
        with self.assertRaises(RuntimeError):
            process_yml(self.path[:-2])


if __name__ == '__main__':
    unittest.main()
