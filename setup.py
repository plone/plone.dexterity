from setuptools import find_packages
from setuptools import setup


version = "3.0.0"


def read(filename):
    with open(filename) as myfile:
        try:
            return myfile.read()
        except UnicodeDecodeError:
            # Happens on one Jenkins node on Python 3.6,
            # so maybe it happens for users too.
            pass
    # Opening and reading as text failed, so retry opening as bytes.
    with open(filename, "rb") as myfile:
        contents = myfile.read()
        return contents.decode("utf-8")


short_description = """\
Framework for content types as filesystem code and TTW (Zope/CMF/Plone)\
"""
long_description = read("README.rst")
long_description += "\n"
long_description += read("CHANGES.rst")

setup(
    name="plone.dexterity",
    version=version,
    description=short_description,
    long_description=long_description,
    # Get more strings from https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Plone",
        "Framework :: Plone :: 6.0",
        "Framework :: Plone :: Core",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="plone dexterity contenttypes",
    author="Martin Aspeli",
    author_email="optilude@gmail.com",
    maintainer="The Plone Release Team and Community",
    maintainer_email="releaseteam@plone.org",
    url="https://github.com/plone/plone.dexterity",
    license="GPL version 2",
    packages=find_packages(),
    namespace_packages=["plone"],
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.8",
    install_requires=[
        "DateTime>=4.0.1",
        "plone.alterego",
        "plone.autoform>=1.0",
        "plone.behavior>=1.0",
        "plone.folder",
        "plone.memoize",
        "plone.rfc822",
        "plone.supermodel>=1.0",
        "plone.uuid",
        "plone.z3cform>=0.6.0",
        "Products.CMFCore",
        "Products.CMFDynamicViewFTI",
        "Products.statusmessages",
        "setuptools",
        "zope.annotation",
        "zope.browser",
        "zope.component",
        "zope.container",
        "zope.dottedname",
        "zope.globalrequest",
        "zope.filerepresentation>=3.6.0",
        "zope.interface",
        "zope.lifecycleevent",
        "zope.publisher",
        "zope.schema",
        "zope.security",
        "zope.size",
        "Zope",
    ],
    extras_require={"test": ["plone.testing", "Products.CMFPlone"]},
)
