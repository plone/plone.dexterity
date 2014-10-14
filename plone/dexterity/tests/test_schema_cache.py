# -*- coding: utf-8 -*-
from plone.dexterity.fti import DexterityFTI
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.schema import SCHEMA_CACHE
from plone.mocktestcase import MockTestCase
from zope.interface import Interface

import unittest


class TestSchemaCache(MockTestCase):

    def setUp(self):
        SCHEMA_CACHE.clear()

    def test_repeated_get_lookup(self):

        class ISchema(Interface):
            pass

        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(ISchema)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        self.replay()

        schema1 = SCHEMA_CACHE.get(u"testtype")
        schema2 = SCHEMA_CACHE.get(u"testtype")

        self.assertTrue(schema1 is schema2 is ISchema)

    def test_repeated_behavior_registration_lookup(self):

        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        # Mock a test behavior
        class ITestBehavior(Interface):
            pass
        self.expect(fti_mock.behaviors).result([ITestBehavior.__identifier__])
        from plone.behavior.registration import BehaviorRegistration
        registration = BehaviorRegistration(
            title=u"Test Behavior",
            description=u"Provides test behavior",
            interface=Interface,
            marker=ITestBehavior,
            factory=None
        )
        from plone.behavior.interfaces import IBehavior
        self.mock_utility(
            registration,
            IBehavior,
            ITestBehavior.__identifier__
        )

        self.replay()

        r1 = SCHEMA_CACHE.behavior_registrations(u'testtype')
        r2 = SCHEMA_CACHE.behavior_registrations(u'testtype')

        self.assertTrue(r1[0] is r2[0] is registration)

    def test_repeated_subtypes_lookup(self):

        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        # Mock a test behavior
        class ITestSchema(Interface):
            pass

        class ITestMarker(Interface):
            pass
        self.expect(fti_mock.behaviors).result([ITestSchema.__identifier__])
        from plone.behavior.registration import BehaviorRegistration
        registration = BehaviorRegistration(
            title=u"Test Behavior",
            description=u"Provides test behavior",
            interface=ITestSchema,
            marker=ITestMarker,
            factory=None
        )
        from plone.behavior.interfaces import IBehavior
        self.mock_utility(
            registration,
            IBehavior,
            ITestSchema.__identifier__
        )

        self.replay()

        s1 = SCHEMA_CACHE.subtypes(u"testtype")
        s2 = SCHEMA_CACHE.subtypes(u"testtype")

        self.assertTrue(s1[0] is s2[0] is ITestMarker)

    def test_repeated_lookup_with_changed_schema(self):

        class ISchema1(Interface):
            pass

        class ISchema2(Interface):
            pass

        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(ISchema1)
        self.expect(fti_mock.lookupSchema()).result(ISchema2).count(0, None)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        self.replay()

        schema1 = SCHEMA_CACHE.get(u"testtype")
        schema2 = SCHEMA_CACHE.get(u"testtype")

        self.assertTrue(schema1 is schema2 and schema2 is ISchema1)

    def test_repeated_lookup_with_changed_schema_and_invalidation(self):

        class ISchema1(Interface):
            pass

        class ISchema2(Interface):
            pass

        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(ISchema1)
        self.expect(fti_mock.lookupSchema()).result(ISchema2).count(0, None)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        self.replay()

        schema1 = SCHEMA_CACHE.get(u"testtype")
        SCHEMA_CACHE.invalidate(u"testtype")
        schema2 = SCHEMA_CACHE.get(u"testtype")

        self.assertTrue(schema1 is ISchema1)
        self.assertTrue(schema2 is ISchema2)

    def test_none_not_cached(self):

        class ISchema1(Interface):
            pass

        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(None)
        self.expect(fti_mock.lookupSchema()).result(ISchema1).count(2)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        self.replay()

        SCHEMA_CACHE.invalidate('testtype')
        schema1 = SCHEMA_CACHE.get(u"testtype")

        SCHEMA_CACHE.invalidate('testtype')
        schema2 = SCHEMA_CACHE.get(u"testtype")

        SCHEMA_CACHE.invalidate('testtype')
        schema3 = SCHEMA_CACHE.get(u"testtype")

        self.assertTrue(schema1 is None)
        self.assertTrue(schema2 is schema3 is ISchema1)

    def test_attribute_and_value_error_not_cached(self):

        class ISchema1(Interface):
            pass

        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).throw(AttributeError)
        self.expect(fti_mock.lookupSchema()).throw(ValueError)
        self.expect(fti_mock.lookupSchema()).result(ISchema1)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        self.replay()

        schema1 = SCHEMA_CACHE.get(u"testtype")

        SCHEMA_CACHE.invalidate('testtype')
        schema2 = SCHEMA_CACHE.get(u"testtype")

        SCHEMA_CACHE.invalidate('testtype')
        schema3 = SCHEMA_CACHE.get(u"testtype")

        self.assertTrue(schema1 is None)
        self.assertTrue(schema2 is None)
        self.assertTrue(schema3 is ISchema1)

    def test_unknown_type_not_cached(self):

        class ISchema1(Interface):
            pass

        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(ISchema1)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        self.replay()

        schema1 = SCHEMA_CACHE.get(u"othertype")
        schema2 = SCHEMA_CACHE.get(u"testtype")
        schema3 = SCHEMA_CACHE.get(u"testtype")

        self.assertTrue(schema1 is None)
        self.assertTrue(schema2 is schema3 is ISchema1)

    def test_clear_all_caches(self):

        class ISchema1(Interface):
            pass
        # FTI mock
        fti_mock1 = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock1.lookupSchema()).result(ISchema1).count(2)
        self.mock_utility(fti_mock1, IDexterityFTI, name=u"testtype1")

        fti_mock2 = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock2.lookupSchema()).result(ISchema1).count(2)
        self.mock_utility(fti_mock2, IDexterityFTI, name=u"testtype2")

        self.replay()

        # reset schemacache counter
        SCHEMA_CACHE.invalidations = 0

        # fill cache should call lookupschema one time
        schema1 = SCHEMA_CACHE.get(u"testtype1")
        schema2 = SCHEMA_CACHE.get(u"testtype2")
        self.assertTrue(schema1 is schema2 is ISchema1)

        # clear
        SCHEMA_CACHE.clear()

        self.assertEqual(SCHEMA_CACHE.invalidations, 2)

        # check invalidations

        # fill cache again should call lookupschema one time
        schema1 = SCHEMA_CACHE.get(u"testtype1")
        schema2 = SCHEMA_CACHE.get(u"testtype2")
        self.assertTrue(schema1 is schema2 is ISchema1)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
