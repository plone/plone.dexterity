from .case import ItemDummy
from .case import MockTestCase
from plone.dexterity.filerepresentation import DefaultReadFile
from zope.interface.verify import verifyObject
from ZPublisher.Iterators import IStreamIterator


class TestFileRepresentation(MockTestCase):
    def create_dummy(self, **kw):
        return ItemDummy(**kw)

    def test_defaultreadfile_verify_iface(self):

        dummy = DefaultReadFile(ItemDummy())
        self.assertTrue(IStreamIterator.providedBy(dummy))
        self.assertTrue(verifyObject(IStreamIterator, dummy))
        self.assertEqual(b"".join(dummy), b"Portal-Type: foo\n\n")
        self.assertEqual(len(dummy), 18)
