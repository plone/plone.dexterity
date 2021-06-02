# -*- coding: utf-8 -*-
from setuptools import setup
from setuptools import find_packages


version = '2.2.10'

short_description = """\
Framework for content types as filesystem code and TTW (Zope/CMF/Plone)\
"""
long_description = open("README.rst").read() + "\n"
long_description += open("CHANGES.rst").read()

setup(
    name='plone.dexterity',
    version=version,
    description=short_description,
    long_description=long_description,
    # Get more strings from
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Framework :: Plone",
        "Framework :: Plone :: 4.3",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords='plone dexterity contenttype framework',
    author='Martin Aspeli',
    author_email='optilude@gmail.com',
    url='https://pypi.python.org/pypi/plone.dexterity',
    license='GPL version 2',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['plone'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # 'Acquisition',
        # 'AccessControl',
        'Products.CMFCore',
        'Products.CMFDynamicViewFTI',
        'Products.statusmessages',
        'ZODB3',
        'Zope2',
        'plone.alterego',
        'plone.autoform>=1.0b2',
        'plone.behavior>=1.0b5',
        'plone.folder',
        'plone.memoize',
        'plone.rfc822',
        'plone.supermodel>=1.0b2',
        'plone.synchronize',
        'plone.uuid',
        'plone.z3cform>=0.6.0',
        'setuptools',
        'zope.annotation',
        'zope.browser',
        'zope.component',
        'zope.container',
        'zope.dottedname',
        'zope.filerepresentation>=3.6.0',
        'zope.interface',
        'zope.lifecycleevent',
        'zope.location',
        'zope.publisher',
        'zope.schema',
        'zope.security',
        'zope.size',
    ],
    extras_require={
        'test': [
            'plone.mocktestcase>=1.0b3',
            'plone.testing',
        ]
    },
    entry_points="""
    # -*- Entry points: -*-
    """,
    )
