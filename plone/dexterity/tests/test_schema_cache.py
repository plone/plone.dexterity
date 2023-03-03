from .case import MockTestCase
from plone.dexterity.fti import DexterityFTI
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.schema import SCHEMA_CACHE
from unittest.mock import Mock
from unittest.mock import patch
from zope.globalrequest import setRequest
from zope.interface import Interface
from zope.publisher.browser import TestRequest


class TestSchemaCache(MockTestCase):
    def setUp(self):
        setRequest(TestRequest())
        SCHEMA_CACHE.clear()

    def test_repeated_get_lookup(self):
        class ISchema(Interface):
            pass

        fti_mock = DexterityFTI("testtype")
        fti_mock.lookupSchema = Mock(return_value=ISchema)
        self.mock_utility(fti_mock, IDexterityFTI, name="testtype")

        schema1 = SCHEMA_CACHE.get("testtype")
        schema2 = SCHEMA_CACHE.get("testtype")

        self.assertTrue(schema1 is schema2 is ISchema)

    def test_repeated_behavior_registration_lookup(self):
        fti = DexterityFTI("testtype")
        self.mock_utility(fti, IDexterityFTI, name="testtype")

        # Mock a test behavior
        class ITestBehavior(Interface):
            pass

        fti.behaviors = [ITestBehavior.__identifier__]
        from plone.behavior.registration import BehaviorRegistration

        registration = BehaviorRegistration(
            title="Test Behavior",
            description="Provides test behavior",
            interface=Interface,
            marker=ITestBehavior,
            factory=None,
        )
        from plone.behavior.interfaces import IBehavior

        self.mock_utility(registration, IBehavior, ITestBehavior.__identifier__)

        r1 = SCHEMA_CACHE.behavior_registrations("testtype")
        r2 = SCHEMA_CACHE.behavior_registrations("testtype")

        self.assertTrue(r1[0] is r2[0] is registration)

    def test_unexistent_behaviors_lookup(self):
        fti = DexterityFTI("testtype")
        self.mock_utility(fti, IDexterityFTI, name="testtype")
        # Set an unregistered behavior
        fti.behaviors = ["foo.bar"]

        with patch("warnings.warn") as mock_warnings:
            SCHEMA_CACHE.behavior_registrations("testtype")
            # Verify the warning has been issued
            mock_warnings.assert_called_once_with(
                (
                    "No behavior registration found for behavior named "
                    '"foo.bar" for factory "testtype" - trying deprecated '
                    'fallback lookup (will be removed in 3.0)..."'
                ),
                DeprecationWarning,
            )

    def test_repeated_subtypes_lookup(self):
        fti = DexterityFTI("testtype")
        self.mock_utility(fti, IDexterityFTI, name="testtype")

        # Mock a test behavior
        class ITestSchema(Interface):
            pass

        class ITestMarker(Interface):
            pass

        fti.behaviors = [ITestSchema.__identifier__]
        from plone.behavior.registration import BehaviorRegistration

        registration = BehaviorRegistration(
            title="Test Behavior",
            description="Provides test behavior",
            interface=ITestSchema,
            marker=ITestMarker,
            factory=None,
        )
        from plone.behavior.interfaces import IBehavior

        self.mock_utility(registration, IBehavior, ITestSchema.__identifier__)

        s1 = SCHEMA_CACHE.subtypes("testtype")
        s2 = SCHEMA_CACHE.subtypes("testtype")

        self.assertTrue(s1[0] is s2[0] is ITestMarker)

    def test_repeated_lookup_with_changed_schema(self):
        class ISchema1(Interface):
            pass

        class ISchema2(Interface):
            pass

        fti = DexterityFTI("testtype")
        fti.lookupSchema = Mock(side_effect=[ISchema1, ISchema2])
        self.mock_utility(fti, IDexterityFTI, name="testtype")

        schema1 = SCHEMA_CACHE.get("testtype")
        schema2 = SCHEMA_CACHE.get("testtype")

        self.assertTrue(schema1 is schema2 and schema2 is ISchema1)

    def test_repeated_lookup_with_changed_schema_and_invalidation(self):
        class ISchema1(Interface):
            pass

        class ISchema2(Interface):
            pass

        fti = DexterityFTI("testtype")
        fti.lookupSchema = Mock(side_effect=[ISchema1, ISchema2])
        self.mock_utility(fti, IDexterityFTI, name="testtype")

        schema1 = SCHEMA_CACHE.get("testtype")
        SCHEMA_CACHE.invalidate("testtype")
        schema2 = SCHEMA_CACHE.get("testtype")

        self.assertTrue(schema1 is ISchema1)
        self.assertTrue(schema2 is ISchema2)

    def test_none_not_cached(self):
        class ISchema1(Interface):
            pass

        fti = DexterityFTI("testtype")
        fti.lookupSchema = Mock(side_effect=[None, ISchema1, ISchema1])
        self.mock_utility(fti, IDexterityFTI, name="testtype")

        SCHEMA_CACHE.invalidate("testtype")
        schema1 = SCHEMA_CACHE.get("testtype")

        SCHEMA_CACHE.invalidate("testtype")
        schema2 = SCHEMA_CACHE.get("testtype")

        SCHEMA_CACHE.invalidate("testtype")
        schema3 = SCHEMA_CACHE.get("testtype")

        self.assertTrue(schema1 is None)
        self.assertTrue(schema2 is schema3 is ISchema1)

    def test_attribute_and_value_error_not_cached(self):
        class ISchema1(Interface):
            pass

        fti = DexterityFTI("testtype")
        fti.lookupSchema = Mock(side_effect=[AttributeError, ValueError, ISchema1])
        self.mock_utility(fti, IDexterityFTI, name="testtype")

        schema1 = SCHEMA_CACHE.get("testtype")

        SCHEMA_CACHE.invalidate("testtype")
        schema2 = SCHEMA_CACHE.get("testtype")

        SCHEMA_CACHE.invalidate("testtype")
        schema3 = SCHEMA_CACHE.get("testtype")

        self.assertTrue(schema1 is None)
        self.assertTrue(schema2 is None)
        self.assertTrue(schema3 is ISchema1)

    def test_unknown_type_not_cached(self):
        class ISchema1(Interface):
            pass

        fti = DexterityFTI("testtype")
        fti.lookupSchema = Mock(return_value=ISchema1)
        self.mock_utility(fti, IDexterityFTI, name="testtype")

        schema1 = SCHEMA_CACHE.get("othertype")
        schema2 = SCHEMA_CACHE.get("testtype")
        schema3 = SCHEMA_CACHE.get("testtype")

        self.assertTrue(schema1 is None)
        self.assertTrue(schema2 is schema3 is ISchema1)

    def test_clear_all_caches(self):
        class ISchema1(Interface):
            pass

        fti1 = DexterityFTI("testtype")
        fti1.lookupSchema = Mock(return_value=ISchema1)
        self.mock_utility(fti1, IDexterityFTI, name="testtype1")

        fti2 = DexterityFTI("testtype")
        fti2.lookupSchema = Mock(return_value=ISchema1)
        self.mock_utility(fti2, IDexterityFTI, name="testtype2")

        # reset schemacache counter
        SCHEMA_CACHE.invalidations = 0

        # fill cache should call lookupschema one time
        schema1 = SCHEMA_CACHE.get("testtype1")
        schema2 = SCHEMA_CACHE.get("testtype2")
        self.assertTrue(schema1 is schema2 is ISchema1)

        # clear
        SCHEMA_CACHE.clear()

        self.assertEqual(SCHEMA_CACHE.invalidations, 2)

        # check invalidations

        # fill cache again should call lookupschema one time
        schema1 = SCHEMA_CACHE.get("testtype1")
        schema2 = SCHEMA_CACHE.get("testtype2")
        self.assertTrue(schema1 is schema2 is ISchema1)
