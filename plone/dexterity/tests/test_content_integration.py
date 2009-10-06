import unittest

# TODO: End to end tests that ensure components are properly wired up
#  - for now, we have some tests in example.dexterity, but we should have
#    more specific tests here.

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
