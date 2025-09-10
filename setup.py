from pathlib import Path
from setuptools import find_packages
from setuptools import setup


version = "3.0.8.dev0"


long_description = (
    f"{Path('README.rst').read_text()}\n{Path('CHANGES.rst').read_text()}"
)


short_description = """\
Framework for content types as filesystem code and TTW (Zope/CMF/Plone)\
"""

setup(
    name="plone.dexterity",
    version=version,
    description=short_description,
    long_description=long_description,
    long_description_content_type="text/x-rst",
    # Get more strings from
    # https://pypi.org/classifiers/
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
    packages=find_packages("src"),
    namespace_packages=["plone"],
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.8",
    install_requires=[
        "Products.CMFCore",
        "Products.statusmessages",
        "Zope",
        "plone.alterego",
        "plone.app.uuid",
        "plone.autoform>=1.0",
        "plone.base",
        "plone.behavior>=1.0",
        "plone.folder",
        "plone.memoize",
        "plone.rfc822",
        "plone.supermodel>=1.0",
        "plone.uuid",
        "z3c.form",
        "setuptools",
    ],
    extras_require={
        "test": [
            "plone.testing",
            "plone.app.content",
            "plone.i18n",
        ]
    },
)
