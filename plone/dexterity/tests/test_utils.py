# -*- coding: utf-8 -*-
from pkg_resources import get_distribution
from plone.dexterity import utils
from plone.dexterity.fti import DexterityFTI
from plone.mocktestcase import MockTestCase

import unittest


has_zope4 = get_distribution('Zope2').version.startswith('4')


class TestUtils(MockTestCase):

    @unittest.skipIf(has_zope4, 'Broken with zope4, see https://community.plone.org/t/problems-with-mocktestcase-in-plone-dexterity/1484')  # noqa
    def test_getAdditionalSchemata(self):
        from plone.dexterity.interfaces import IDexterityFTI
        from plone.behavior.interfaces import IBehavior
        from plone.autoform.interfaces import IFormFieldProvider
        from zope.interface import Interface
        from zope.interface import providedBy

        class IBehaviorInterface(Interface):
            pass

        class IBehaviorSchema(Interface):
            pass

        behavior_mock = self.mocker.mock()
        fti_mock = self.mocker.proxy(DexterityFTI(u'testtype'))
        provider_mock = self.mocker.mock()

        portal_type = 'prefix_0_type_0_schema'
        behavior_name = 'behavior_0'

        self.expect(
            fti_mock.behaviors
        ).result(
            (behavior_name, )
        )

        self.expect(
            behavior_mock.interface
        ).result(
            IBehaviorInterface
        ).count(2)

        provider_mock(IBehaviorInterface)
        self.mocker.result(IBehaviorSchema)

        self.mock_utility(behavior_mock, IBehavior, behavior_name)
        self.mock_utility(fti_mock, IDexterityFTI, portal_type)

        self.mock_adapter(
            provider_mock,
            IFormFieldProvider,
            (providedBy(IBehaviorInterface), )
        )

        self.replay()

        generator = utils.getAdditionalSchemata(None, portal_type)
        schematas = tuple(generator)

        self.assertEqual(len(schematas), 1)
        schemata = schematas[0]
        self.assertTrue(schemata is IBehaviorSchema)

    def testAddContentToContainer_preserves_existing_id(self):
        from plone.dexterity.content import Item
        from plone.dexterity.content import Container
        container = Container()
        container._ordering = u'unordered'

        from zope.component import provideAdapter, provideUtility
        from zope.container.interfaces import INameChooser
        from zope.interface import Interface
        from plone.app.content.namechooser import NormalizingNameChooser
        from plone.folder.interfaces import IOrdering
        from plone.folder.unordered import UnorderedOrdering
        from plone.i18n.normalizer.interfaces import IURLNormalizer
        from plone.i18n.normalizer import URLNormalizer
        provideAdapter(NormalizingNameChooser, [Interface], INameChooser)
        provideUtility(URLNormalizer(), IURLNormalizer)
        provideAdapter(UnorderedOrdering, [Interface], IOrdering)

        # if the item has an id already, use it
        from plone.dexterity.utils import addContentToContainer
        item = Item()
        item.id = 'foo'
        item = addContentToContainer(container, item, checkConstraints=False)
        self.assertEqual(item.id, 'foo')

        # unless it's a duplicate
        item = Item()
        item.id = 'foo'
        item = addContentToContainer(container, item, checkConstraints=False)
        self.assertEqual(item.id, 'foo-1')

    def test_all_merged_tagged_values_dict(self):
        from zope.interface import Interface

        class IIFace1(Interface):
            pass

        class IIFace2(Interface):
            pass

        self.assertEqual(
            utils.all_merged_tagged_values_dict((IIFace1, IIFace2), 'foo'),
            {}
        )

        IIFace1.setTaggedValue('foo', {'a': 10})
        IIFace1.setTaggedValue('bar', {'a': 11})
        self.assertEqual(
            utils.all_merged_tagged_values_dict((IIFace1, IIFace2), 'foo'),
            {'a': 10}
        )
        IIFace2.setTaggedValue('foo', {'a': 12})
        self.assertEqual(
            utils.all_merged_tagged_values_dict((IIFace1, IIFace2), 'foo'),
            {'a': 12}
        )
        IIFace2.setTaggedValue('foo', {'a': 13, 'b': 14})
        self.assertEqual(
            utils.all_merged_tagged_values_dict((IIFace1, IIFace2), 'foo'),
            {'a': 13, 'b': 14}
        )


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
