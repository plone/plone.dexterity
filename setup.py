from setuptools import setup, find_packages
import os

version = '1.0a1'

setup(name='plone.dexterity',
      version=version,
      description="CMF compatible integration of TTW-editable types",
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
      url='http://plone.org',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['plone'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'plone.z3cform',
          'plone.mocktestcase',
          'plone.folder',
          'plone.supermodel',
          'plone.alterego',
          'plone.behavior',

          'five.grok',
          
          'zope.interface',
          'zope.component',
          'zope.schema',
          'zope.dottedname',
          'zope.annotation',
          'zope.publisher',
          'zope.app.container',
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
