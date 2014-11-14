# -*- coding: utf-8 -*-
import doctest
import unittest
import zope.component.testing


def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite(
            '../behavior_api.rst',
            setUp=zope.component.testing.setUp,
            tearDown=zope.component.testing.tearDown),
        )

    )
