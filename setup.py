# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup


version = '2.9.4'

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
    # https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Plone",
        "Framework :: Plone :: 5.2",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords='plone dexterity contenttypes',
    author='Martin Aspeli',
    author_email='optilude@gmail.com',
    url='https://pypi.org/project/plone.dexterity',
    license='GPL version 2',
    packages=find_packages(),
    namespace_packages=['plone'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # 'Acquisition',
        # 'AccessControl',
        'DateTime>=4.0.1',
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
        'Products.CMFCore',
        'Products.CMFDynamicViewFTI',
        'Products.statusmessages',
        'setuptools',
        'six',
        'ZODB3',
        'zope.annotation',
        'zope.browser',
        'zope.component',
        'zope.container',
        'zope.dottedname',
        'zope.globalrequest',
        'zope.filerepresentation>=3.6.0',
        'zope.interface',
        'zope.lifecycleevent',
        'zope.location',
        'zope.publisher',
        'zope.schema',
        'zope.security',
        'zope.size',
        'Zope2',
    ],
    extras_require={
        'test': [
            'plone.testing',
            'Products.CMFPlone',
            'mock',
        ]
    },
    entry_points="""
    # -*- Entry points: -*-
    """,
)
