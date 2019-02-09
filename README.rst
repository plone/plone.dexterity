Dexterity
=========

    "Same, same, but different"

Dexterity is a system for building content types, both through-the-web and as filesystem code.
It is aimed at Plone, although this package should work with plain Zope + CMF systems.

Key use cases
-------------

Dexterity wants to make some things really easy. These are:

- Create a "real" content type entirely through-the-web without having to know programming.

- As a business user, create a schema using visual or through-the-web tools, and augment it with adapters, event handlers, and other Python code written on the filesystem by a Python programmer.

- Create content types in filesystem code quickly and easily, without losing the ability to customise any aspect of the type and its operation later if required.

- Support general "behaviours" that can be enabled on a custom type in a declarative fashion.
  Behaviours can be things like title-to-id naming, support for locking or versioning, or sets of standard metadata with associated UI elements.

- Easily package up and distribute content types defined through-the-web, on the filesystem, or using a combination of the two.

Philosophy
----------

Dexterity is designed with a specific philosophy in mind.
This can be summarised as follows:

Reuse over reinvention
   As far as possible, Dexterity should reuse components and technologies that already exist.
   More importantly, however, Dexterity should reuse *concepts* that exist elsewhere.
   It should be easy to learn Dexterity by analogy, and to work with Dexterity types using familiar APIs and techniques.

Small over big
   Mega-frameworks be damned.
   Dexterity consists of a number of specialised packages, each of which is independently tested and reusable.
   Furthermore, packages should have as few dependencies as possible, and should declare their dependencies explicitly.
   This helps keep the design clean and the code manageable.

Natural interaction over excessive generality
   The Dexterity design was driven by several use cases (see docs/Design.txt) that express the way in which we want people to work with Dexterity.
   The end goal is to make it easy to get started, but also easy to progress from an initial prototype to a complex set of types and associated behaviours through step-wise learning and natural interaction patterns.
   Dexterity aims to consider its users - be they business analysts, light integrators, or Python developers, and be they new or experienced - and cater to them explicitly with obvious, well-documented, natural interaction patterns.

Real code over generated code
   Generated code is difficult to understand and difficult to debug when it  doesn't work as expected.
   There is rarely, if ever, any reason to scribble methods or 'exec' strings of Python code.

ZCA over old Zope 2
   As many components as possible should work with plain ZCA (Zope Component Architecture, ``zope.*`` packages with origins in Zope 3).
   Although Dexterity does not pretend to work with non-CMF systems,
   Even where there are dependencies on Zope 2, CMF or Plone, they should - as far as is practical - follow ZCA techniques and best practices.
   Many operations (e.g. managing objects in a folder, creating new objects or manipulating objects through a defined schema) are better designed in
   ZCA than they were in Zope 2.

Zope concepts over new paradigms
   We want Dexterity to be "Zope-ish" (and really, "ZCA-ish").
   Zope is a mature, well-designed (well, mostly) and battle tested platform.
   We do not want to invent brand new paradigms and techniques if we can help it.

Automated testing over wishful thinking
   "Everything" should be covered by automated tests.
   Dexterity necessarily has a lot of moving parts.
   Untested moving parts tend to come lose and fall on people's heads.
   Nobody likes that.

What's it all about?
--------------------

With the waffle out of the way, let's look in a bit more detail about what
makes up a "content type" in the Dexterity system.

The model
   The Dexterity "model" describes a type's schemata and metadata associated with those schemata.
   A schema is just a series of fields that can be used to render add/edit forms and introspect an object of the given type.
   The metadata storage is extensible via the component architecture.
   Typical forms of metadata include UI hints such as specifying the type of widget to use when rendering a particular field, and per-field security settings.

   The model is described in also XML.
   Though at runtime it is an instance of an object providing the IModel interface from ``plone.supermodel``.
   Schemata in the model are interfaces with ``zope.schema`` fields.

   The model can exist purely as data in the ZODB if a type is created through-the-web.
   Alternatively, it can be loaded from a file.
   The XML representation is intended to be human-readable and self-documenting.
   It is also designed with tools like `AGX  <http://agx.me>`_ in mind, that can generate models from a visual representation.

The schema
   All content types have at least one (unnamed) schema.
   A schema is simply an Interface with zope.schema fields.
   The schema can be specified in Python code (in which case it is simply referenced by name), or it can be loaded from an XML model.

   The unnamed schema is also known as the IContentType schema.
   In that, the schema interface will provide the zope IContentType interface.
   This means that if you call ``queryContentType()`` on a Dexterity content object, you should get back its unnamed schema, and that schema should be provided by the object that was queried.
   Thus, the object will directly support the attributes promised by the schema.
   This makes Dexterity content objects "Pythonic" and easy to work with.

The class
   Of course, all content objects are instances of a particular class.
   It is easy to provide your own class, and Dexterity has convenient base classes for you to use.
   However, many types will not need a class at all.
   Instead, they will use the standard Dexterity "Item" and "Container" classes.

   Dexterity's content factory will initialise an object of one of these classes with the fields in the type's content schema.
   The factory will ensure that objects provide the relevant interfaces, including the schema interface itself.

   The preferred way to add behaviour and logic to Dexterity content objects is via adapters.
   In this case, you will probably want a filesystem version of the schema interface (this can still be loaded from XML if you
   wish, but it will have an interface with a real module path) that you  can register components against.

The factory
   Dexterity content is constructed using a standard zope IFactory named utility.
   By convention the factory utility has the same name as the portal_type of the content type.

   When a Dexterity FTI (Factory Type Information, see below) is created, an appropriate factory will be registered as a local utility unless one    with that name already exists.

   The default factory is capable of initialising a generic ``Item`` or  ``Container`` object to exhibit a content type schema and have the security and other aspects specified in the type's model.
   You can use this if you wish, or provide your own factory.

Views
   Dexterity will by default create an:
   - add view (registered as a local utility, since it needs to take the portal_type of the content type into account when determining what fields to render) and an
   - edit view (registered as a generic, global view, which inspects the context's portal_type at runtime) for each type.
   - A default main view exists, which simply outputs the fields set on the context.

   To register new views, you will normally need a filesystem schema interface.
   You can then register views for this interface as you normally would.

   If you need to override the default add view, create a view for IAdding with a name corresponding to the portal_type of the content type.
   This will prevent Dexterity from registering a local view with the same name when the FTI is created.

The Factory Type Information (FTI)
   The FTI holds various information about the content type.
   Many operations performed by the Dexterity framework begin by looking up the type's FTI to find out some information about the type.

   The FTI is an object stored in portal_types in the ZMI.
   Most settings can be changed through the web.
   See the IDexterityFTI interface for more information.

   When a Dexterity FTI is created, an event handler will create a few local components, including the factory utility and add view for the new type. The FTI itself is also registered as a named utility, to make it easy to look up using syntax like::

       getUtility(IDexterityFTI, name=portal_type)

   The FTI is also fully importable and exportable using GenericSetup.
   Thus, the easiest way to create and distribute a content type is to create a new FTI, set some properties (including a valid XML model,
   which can be entered TTW if there is no file or schema interface to use), and export it as a GenericSetup extension profile.

Behaviors
   Behaviors are a way write make re-usable bits of functionality that can be toggled on or off on a per-type basis.
   Examples may include common metadata, or common functionality such as locking, tagging or ratings.

   Behaviors are implemented using the plone.behavior package.
   See its documentation for more details about how to write your own behaviors.

   In Dexterity, behaviors can "inject" fields into the standard add and edit forms, and may provide marker interfaces for newly created objects.
   See the example.dexterity package for an example of a behavior that provides form fields.

   In use, a behavior is essentially just an adapter that only appears to be registered if the behavior is enabled in the FTI of the object being adapted.
   Thus, if you have a behavior described by my.package.IMyBehavior, you'll typically interact with this behavior by doing::

       my_behavior = IMyBehavior(context, None)
       if my_behavior is not None:
           ...

   The enabled behaviors for a given type are kept in the FTI, as a list of dotted interface names.

The Dexterity Ecosystem
-----------------------

The Dexterity system comprises a number of packages, most of which are
independently re-usable. In addition, Dexterity uses many components from
Zope and CMF.

The most important packages are:

`plone.dexterity <https://pypi.python.org/pypi/plone.alterego>`_ (CMF)
   **this package** Defines the FTI and content classes.
   It provides basic views (with forms based on z3c.form), handles security and so on.
   It also provides components to orchestrate the various functionality provided by the packages above in order to bring the Dexterity system together.

`plone.behavior <https://pypi.python.org/pypi/plone.behavior>`_ (ZCA)
   Supports "conditional" adapters. A product author can write and register  a generic behaviour that works via a simple adapter.
   The adapter will appear to be registered for types that have the named behaviour available.

   Dexterity wires this up in such a way that the list of enabled behaviours is stored as a property in the FTI.
   This makes it easy to add/remove behaviours through the web, or using GenericSetup at install time.

`plone.folder <https://pypi.python.org/pypi/plone.folder>`_ (CMF)
   This is an implementation of an ordered, BTree-backed folder, with ZCA
   dictionary-style semantics for managing content items inside the folder.
   The standard Dexterity 'Container' type uses plone.folder as its base.

`plone.autoform <https://pypi.python.org/pypi/plone.autoform>`_ (CMF, z3cform)
   Contains helper functions to construct forms based on tagged values stored on schema interfaces.

`plone.supermodel <https://pypi.python.org/pypi/plone.supermodel>`_ (ZCA)
   Supports parsing and serialisation of interfaces from/to XML.
   The XML format is based directly on the interfaces that describe zope.schema type fields.
   Thus it is easily extensible to new field types.
   This has the added benefit that the interface documentation in the zope.schema package applies to the XML format as well.

   Supermodel is extensible via adapters and XML namespaces.
   plone.dexterity uses this to allow security and UI hints to be embedded as metadata in the XML model.

`plone.alterego <https://pypi.python.org/pypi/plone.alterego>`_ (Python)
   Support for dynamic modules that create objects on the fly.
   Dexterity uses this to generate "real" interfaces for types that exist only through-the-web.
   This allows these types to have a proper IContentType schema.
   It also allows local adapters to be registered for this interface (e.g. a custom view with a template defined through the web).

   Note that if a type uses a filesystem interface (whether written manually or loaded from an XML model), this module is not used.

`plone.app.dexterity <https://pypi.python.org/pypi/plone.app.dexterity>`_ (Plone)
   This package contains all Plone-specific aspects of Dexterity, including Ploneish UI components, behaviours and defaults.


Developer Manual
----------------

The `Dexterity Developer Manual <http://docs.plone.org/external/plone.app.dexterity/docs/index.html>`_ is a complete documentation with practical examples and part of the `Offical Plone Documentation <http://docs.plone.org/>`_.


Source Code
===========

Contributors please read the document `Process for Plone core's development <https://docs.plone.org/develop/coredev/docs/index.html>`_

Sources are at the `Plone code repository hosted at Github <https://github.com/plone/plone.dexterity>`_.
