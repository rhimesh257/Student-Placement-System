import re
import tempfile
import unittest
from pathlib import Path
from app import create_app

class PlacementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = create_app({'TESTING': True, 'DATABASE': str(Path(self.temp.name) / 'test.db'), 'SECRET_KEY': 'test-key'})
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def token(self):
        self.client.get('/')
        with self.client.session_transaction() as sess:
            return sess['csrf_token']

    def student(self, **changes):
        data = dict(csrf_token=self.token(), name='Test Student', department='CSE', cgpa='8.5',
                    aptitude='80', technical='90', communication='75', placed='yes', package='6')
        data.update(changes)
        return data

    def test_dashboard(self):
        page = self.client.get('/')
        self.assertEqual(page.status_code, 200)
        self.assertIn(b'Rahul', page.data)

    def test_add_student_and_persist(self):
        result = self.client.post('/', data=self.student())
        self.assertEqual(result.status_code, 302)
        self.assertIn(b'Test Student', self.client.get('/').data)
        another = create_app({'TESTING': True, 'DATABASE': self.app.config['DATABASE']})
        self.assertIn(b'Test Student', another.test_client().get('/').data)

    def test_invalid_inputs(self):
        for change in ({'cgpa': 'nan'}, {'cgpa': 'inf'}, {'technical': '101'},
                       {'placed': 'invalid'}, {'department': 'INVALID'},
                       {'placed': 'no', 'package': '6'}, {'package': '-2'},
                       {'name': ''}, {'aptitude': '5.5'}):
            with self.subTest(change=change):
                self.assertEqual(self.client.post('/', data=self.student(**change)).status_code, 400)

    def test_csrf(self):
        data = self.student()
        data.pop('csrf_token')
        self.assertEqual(self.client.post('/', data=data).status_code, 400)

if __name__ == '__main__':
    unittest.main()
