from unittest import TestCase
import gitaction


class Test(TestCase):
    def test_create_pr_json(self):
        expected = {"title": "mytitle",
                    "source": {
                        "branch": {
                            "name": "new_branch"
                        }
                    },
                    "reviewers": [{"uuid": "{139d650b-be36-4d62-8d69-49fec09a6057}"}]
                    }
        self.assertEqual(expected, gitaction.create_pr_json("new_branch",
                                                            [{"uuid": "{139d650b-be36-4d62-8d69-49fec09a6057}"}],
                                                            "mytitle"))
