from setuptools import setup, find_packages
import os

version = '1.1.2'

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
      license='GPL version 2',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['plone'],
      include_package_data=True,
      message_extractors = {"plone": [
            ("**.py",    "chameleon_python", None),
            ("**.pt"  ,  "chameleon_xml", None),
            ]},
      zip_safe=False,
      install_requires=[
          'setuptools',
          'rwproperty',
          'plone.synchronize',
          'plone.memoize',

          'Products.CMFCore',
          'Products.CMFPlone',
          
          'plone.z3cform>=0.6.0',
          'plone.folder',
          'plone.supermodel>=1.0b2',
          'plone.alterego',
          'plone.behavior>=1.0b5',
          'plone.autoform>=1.0b2',
          'plone.rfc822',
          
          'zope.app.pagetemplate',
          'zope.app.component',

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
          'zope.filerepresentation>=3.6.0',
          'zope.size',
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
      extras_require={
        'test': ['plone.mocktestcase>=1.0b3',]
      },
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
