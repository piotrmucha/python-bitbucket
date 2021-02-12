from unittest import TestCase
import resolver
import os


class Test(TestCase):
    def test_get_files_with_extension(self):
        files = resolver.get_files_with_extension(os.getcwd(), ["exts"])
        self.assertEqual(1, len(files))

    def test_find_files_with_str(self):
        files = [os.getcwd() + '/text.exts']
        files = resolver.find_files_with_str(files, "strings")
        self.assertEqual(1, len(files))
