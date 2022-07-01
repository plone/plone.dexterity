from .case import MockTestCase
from plone.dexterity import utils
from plone.dexterity.fti import DexterityFTI
from unittest.mock import Mock


class TestUtils(MockTestCase):
    def test_getAdditionalSchemata(self):
        from plone.autoform.interfaces import IFormFieldProvider
        from plone.behavior.interfaces import IBehavior
        from plone.dexterity.interfaces import IDexterityFTI
        from zope.interface import Interface
        from zope.interface import providedBy

        class IBehaviorInterface(Interface):
            pass

        class IBehaviorSchema(Interface):
            pass

        behavior_mock = Mock()
        fti_mock = DexterityFTI("testtype")

        portal_type = "prefix_0_type_0_schema"
        behavior_name = "behavior_0"

        fti_mock.behaviors = (behavior_name,)
        behavior_mock.interface = IBehaviorInterface

        provider_mock = Mock(return_value=IBehaviorSchema)

        self.mock_utility(behavior_mock, IBehavior, behavior_name)
        self.mock_utility(fti_mock, IDexterityFTI, portal_type)

        self.mock_adapter(
            provider_mock, IFormFieldProvider, (providedBy(IBehaviorInterface),)
        )

        generator = utils.getAdditionalSchemata(None, portal_type)
        schematas = tuple(generator)

        self.assertEqual(len(schematas), 1)
        schemata = schematas[0]
        self.assertTrue(schemata is IBehaviorSchema)

    def testAddContentToContainer_preserves_existing_id(self):
        from plone.dexterity.content import Container
        from plone.dexterity.content import Item

        container = Container()
        container._ordering = "unordered"
        # Allow anyone to access the contents information on the container.
        # This allows to check for existing content with the same id.
        container.manage_permission(
            "Access contents information", ["Anonymous"], acquire=1
        )

        from plone.app.content.namechooser import NormalizingNameChooser
        from plone.folder.interfaces import IOrdering
        from plone.folder.unordered import UnorderedOrdering
        from plone.i18n.normalizer import URLNormalizer
        from plone.i18n.normalizer.interfaces import IURLNormalizer
        from zope.component import provideAdapter
        from zope.component import provideUtility
        from zope.container.interfaces import INameChooser
        from zope.interface import Interface

        provideAdapter(NormalizingNameChooser, [Interface], INameChooser)
        provideUtility(URLNormalizer(), IURLNormalizer)
        provideAdapter(UnorderedOrdering, [Interface], IOrdering)

        # if the item has an id already, use it
        from plone.dexterity.utils import addContentToContainer

        item = Item()
        item.id = "foo"
        item = addContentToContainer(container, item, checkConstraints=False)
        self.assertEqual(item.id, "foo")

        # unless it's a duplicate
        item = Item()
        item.id = "foo"
        item = addContentToContainer(container, item, checkConstraints=False)
        self.assertEqual(item.id, "foo-1")

    def test_all_merged_tagged_values_dict(self):
        from zope.interface import Interface

        class IIFace1(Interface):
            pass

        class IIFace2(Interface):
            pass

        self.assertEqual(
            utils.all_merged_tagged_values_dict((IIFace1, IIFace2), "foo"), {}
        )

        IIFace1.setTaggedValue("foo", {"a": 10})
        IIFace1.setTaggedValue("bar", {"a": 11})
        self.assertEqual(
            utils.all_merged_tagged_values_dict((IIFace1, IIFace2), "foo"), {"a": 10}
        )
        IIFace2.setTaggedValue("foo", {"a": 12})
        self.assertEqual(
            utils.all_merged_tagged_values_dict((IIFace1, IIFace2), "foo"), {"a": 12}
        )
        IIFace2.setTaggedValue("foo", {"a": 13, "b": 14})
        self.assertEqual(
            utils.all_merged_tagged_values_dict((IIFace1, IIFace2), "foo"),
            {"a": 13, "b": 14},
        )
