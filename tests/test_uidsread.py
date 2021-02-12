from unittest import TestCase
import uidsread
import os


class Test(TestCase):

    def test_map_users_to_json_array(self):
        expected = [{"uuid": "{fjk}"}, {"uuid": "{abc}"}]
        result = uidsread.map_users_to_json_array("{fjk}", "{abc}")
        self.assertEqual(expected, result)

    def test_create_two_json_with_reviewers(self):
        maps = {"{139d650b-be36-4d62-8d69-49fec09a6057}": "Piotrek Ucha"}
        uidsread.create_two_json_with_reviewers(maps)
        self.assertTrue(os.path.isfile('usersMap.json'))
        self.assertTrue(os.path.isfile('reviewers.json'))

    def test_get_json_array_from_file(self):
        expected = [{"uuid": "{139d650b-be36-4d62-8d69-49fec09a6057}"}]
        file = 'reviewers.json'
        array = uidsread.get_json_array_from_file(file)
        self.assertEqual(expected, array)
