from unittest import TestCase
import uidsread


class Test(TestCase):
    def test_get_users_for_given_workspace(self):
        pass

    def test_get_uuid_for_current_user(self):
        self.fail()

    def test_map_users_to_json_array(self):
        expected = [{"uuid": "{fjk}"}, {"uuid": "{abc}"}]
        result = uidsread.map_users_to_json_array("{fjk}", "{abc}")
        self.assertEqual(expected, result)

    def test_create_two_json_with_reviewers(self):
        self.fail()

    def test_get_json_array_from_file(self):
        self.fail()
