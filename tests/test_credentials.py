from unittest import TestCase
import credentials


class Test(TestCase):
    def test_get_credentials_for_bitbucket(self):
        credential = credentials.get_credentials_for_bitbucket("bitbucket-credentials")
        self.assertEqual("fdfsdfsdfsfa", credential.appkey)
        self.assertEqual("userBitbucket", credential.username)
