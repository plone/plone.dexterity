from setuptools import setup, find_packages
import os

version = '1.0a1'

setup(name='plone.dexterity',
      version=version,
      description="Flexible CMF content",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='',
      author='Martin Aspeli',
      author_email='optilude@gmail.com',
      url='http://code.google.com/p/dexterity',
      license='LGPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['plone'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'plone.synchronize',
          'plone.mocktestcase>=1.0b3',
          
          'plone.z3cform',
          'plone.folder',
          'plone.supermodel>=1.0b2',
          'plone.alterego',
          'plone.behavior>=1.0b5',
          'plone.autoform>=1.0b2',

          'zope.interface',
          'zope.component',
          'zope.schema',
          'zope.location',
          'zope.dottedname',
          'zope.annotation',
          'zope.publisher',
          'zope.deferredimport',
          'zope.security',
          'zope.app.container',   # XXX: Should move to zope.container in the future
          'zope.app.content',
          'ZODB3',
          
          # 'Acquisition',
          # 'AccessControl',
          # 'Products.CMFCore',
          # 'Products.CMFDefault',
          # 'Products.CMFDynamicViewFTI',
          # 'Products.Five',
          # 'Products.statusmessages',

          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
