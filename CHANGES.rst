Changelog
=========


.. You should *NOT* be adding new change log entries to this file.
   You should create a file in the news directory instead.
   For helpful instructions, please see:
   https://github.com/plone/plone.releaser/blob/master/ADD-A-NEWS-ITEM.rst

.. towncrier release notes start

2.9.3 (2019-12-23)
------------------

Bug fixes:


- Fix thread safe recursion detection. This fixes an issue in plone.restapi: https://github.com/plone/plone.dexterity/issues/120. [jensens] (#120)


2.9.2 (2019-10-12)
------------------

Bug fixes:


- The debug messages issued when a non existent behavior is recorded in an FTI have been improved [ale-rt] (#109)
- Avoid looking up behaviors with an empty name [ale-rt] (#110)
- Performance enhancement in schema cache by factor ~1.5.
  [jensens] (#113)
- Performance enhancement in schema cache and assignable.
  [jensens] (#115)
- Performance enhancement:
  Refine pre-filtering of attributes on content ``__getattr__``.
  Filter out all permissions (ending with ``_Permission``) and some portal-tools.
  Also often called aquired functions are skipped.
  [jensens] (#116)
- Performance enhancement: avoid a providedBy in ``_default_from_schema``.
  [jensens] (#117)


2.9.1 (2019-05-21)
------------------

Bug fixes:


- Fix WebDAV compatibility issues with ZServer on Python 3 [datakurre] (#102)
- Avoid passing in unicode data into the WebDAV message parser.
  [Rotonen] (#103)


2.9.0 (2019-05-01)
------------------

New features:


- Avoid expensive lookups for other common attributes.
  [gforcada] (#98)
- Add container property to ``AddForm`` to simplify target container selection in subclasses. [jensens] (#101)


Bug fixes:


- Turn a warning meant as deprecation warning into a a real DeprecationWarning,
  follows Deprecation Guide best practice.
  [jensens] (#95)
- Fixed DeprecationWarning for ObjectEvent.  [maurits] (#96)


2.8.0 (2019-02-08)
------------------

New features:


- Implement getSize method to sum the size of all field values that have a
  getSize method. [davisagli] (#89)


Bug fixes:


- Other Python 3 compatibility fixes [ale-rt] (#90)
- Add PathReprProvider as a baseclass of Container to restore the original
  __repr__ behavior instead of the new __repr__ from persistent.Persistent.
  PathReprProvider needs to be before CMFOrderedBTreeFolderBase (which inherits
  OrderedBTreeFolderBase > BTreeFolder2Base > Persistent). [pbauer] (#93)
- Fixed test for minor check_id change. We need the 'Access contents
  information' permission. (#2582)
- Remove deprecation warning, see
  https://github.com/plone/Products.CMFPlone/issues/2667 (#2667)


2.6.1 (2018-09-23)
------------------

New features:

- ZServer is now optional
  [pbauer]

Bug fixes:

- Other Python 3 compatibility fixes
  [ale-rt, pbauer, jensens]


2.6.0 (2018-04-03)
------------------

New features:

- Move translations to plone.app.locales
  [erral]

Bug fixes:

- Other Python 3 compatibility fixes
  [pbauer]


2.5.5 (2018-02-05)
------------------

Bug fixes:

- Prepare for Python 2 / 3 compatibility
  [pbauer]


2.5.4 (2017-11-24)
------------------

Bug fixes:

- Fix tests on Zope 4. [davisagli]


2.5.3 (2017-10-17)
------------------

Bug fixes:

- Give more context to the 'schema cannot be resolved' warning.  [gotcha]


2.5.2 (2017-06-03)
------------------

Bug fixes:

- Fix problem with new zope.interface not accepting None as value.
  [jensens]


2.5.1 (2017-02-27)
------------------

Bug fixes:

- Make sure that all fields are initialized to their default value
  when items are added via the add form. This is important in the case
  of fields with a defaultFactory that can change with time
  (such as defaulting to the current date).
  [davisagli]


2.5.0 (2017-02-12)
------------------

Breaking changes:

- When calling the DC metadata accessor for ``Description``, remove newlines from the output.
  This makes the removal of newlines from the description behavior setter in plone.app.dexterity obsolete.
  [thet]

Bug fixes:

- Relax tests for ZMI tabs for compatibility with Zope 4. [davisagli]


2.4.5 (2016-11-19)
------------------

New features:

- Removed test dependency on plone.mocktestcase [davisagli]


2.4.4 (2016-09-23)
------------------

Bug fixes:

- Fix error when copying DX containers with AT children which caused the
  children to not have the UID updated properly.  [jone]


2.4.3 (2016-08-12)
------------------

Bug fixes:

- Use zope.interface decorator.
  [gforcada]


2.4.2 (2016-05-12)
------------------

Fixes:

- Added security declarations from Products.PloneHotfix20160419.  [maurits]


2.4.1 (2016-02-27)
------------------

Incompatibilities:

- addCreator should not add if a creator is already set for content. This prevents every
  editor on content from adding to the list of creators for an object.
  [vangheem]


2.4.0 (2016-02-17)
------------------

New:

- Added Russian translation.  [serge73]

- Updated to and depended on pytz 2015.7 and DateTime 4.0.1.  [jensens]

Fixes:

- Skipped the tests
  ``test_portalTypeToSchemaName_looks_up_portal_for_prefix`` and
  ``test_getAdditionalSchemata`` with isolation problems in Zope 4.
  [pbauer]

- Made utils/datify work with newer DateTime and pytz.  Adjust tests
  to reflect changes.  [jensens]

- Fixed: duplicate aq_base without using Acquistion API resulted in an
  AttributeError that was masqued in the calling hasattr and resulted
  in wrong conclusion.  [jensens]

- Made modification test more stable.  [do3cc]


2.3.7 (2016-01-08)
------------------

Fixes:

- Sync schema when schema_policy name is changed (issue #44)
  [sgeulette]

- Corrected tests on date comparison (avoid 1h shift)
  [sgeulette]


2.3.6 (2015-10-28)
------------------

Fixes:

- No longer rely on deprecated ``bobobase_modification_time`` from
  ``Persistence.Persistent``.
  [thet]


2.3.5 (2015-09-20)
------------------

- Use registry lookup for types_use_view_action_in_listings
  [esteele]

- Don't check type constraints in AddForm.update() if request provides
  IDeferSecurityChecks.
  [alecm]


2.3.4 (2015-08-14)
------------------

- Avoid our own DeprecationWarning about portalTypeToSchemaName.
  [maurits]

- Set title on WebDAV upload
  [tomgross]

2.3.3 (2015-07-29)
------------------

- This version is still Plone 4.3.x compatible. Newer versions
  are only Plone 5 compatible.

- Check add_permission before checking constrains. Refs #37
  [jaroel]

- Remove obsolete css-class and text from statusmessages.
  [pbauer]

- Complete invalidate_cache.
  [adamcheasley]


2.3.2 (2015-07-18)
------------------

- Check allowed types for add form.
  [vangheem]


2.3.1 (2015-05-31)
------------------

- Fix issue where webdav PUT created items with empty id
  [datakurre]

- fix #27: createContent ignores empty fields
  [jensens]


2.3.0 (2015-03-13)
------------------

- Use attribute for DefaultAddForm and DefaultEditForm success message so it can
  be easily customized.
  [cedricmessiant]

- Big major overhaul to use everywhere the same way to fetch the main schema,
  behavior schemata and its markers. This was very scrmabled: sometimes
  behaviors weren't taken into account, or only FTI based behaviors but not
  those returned by the IBehaviorAssignable adapter. Also the caching was
  cleaned up. The tests are now better readable (at least I hope so).  In order
  to avoid circular imports some methods where moved fro ``utils.py`` to
  ``schema.py``.  Deprecations are in place.
  [jensens]

- Fix (security): Attribute access to schema fields can be protected. This
  worked for direct schemas, but was not implemented for permissions coming
  from behaviors.
  [jensens]

2.2.4 (2014-10-20)
------------------

- Fix the default attribute accessor to bind field to context when finding
  the field default.
  [datakurre]

- fix: when Dexterity container or its children contains any AT content with
  AT references in them, any move or rename operation for the parent
  Dexterity object will cause AT ReferenceEngine to remove those references.
  see #20.
  [datakurre]

- Let utils.createContent also handle setting of attributes on behaviors, which
  derive from other behaviors.
  [thet]

- overhaul (no logic changed):
  pep8, sorted imports plone.api style, readability, utf8header,
  remove bbb code (plone 3)
  [jensens]

2.2.3 (2014-04-15)
------------------

- Re-release 2.2.2 which was a brown bag release.
  [timo]

2.2.2 (2014-04-13)
------------------

- Add a 'success' class to the status message shown after successfully
  adding or editing an item.  The previous 'info' class is also
  retained for backwards-compatibility.
  [davisagli]

- If an object being added to a container already has an id, preserve it.
  [davisagli]

2.2.1 (2014-02-14)
------------------

- Also check behavior-fields for IPrimaryField since plone.app.contenttypes
  uses fields provided by behaviors as primary fields
  [pbauer]


2.2.0 (2014-01-31)
------------------

- utils.createContent honors behaviors.
  [toutpt]

- Date index method works even if source field is a dexterity field
  wich provides a  datetime python value.
  Now you can manually add a field with the name of a common Plone metadata field
  (as effective_date, publication_date, etc.)
  [tdesvenain]

- Replace deprecated test assert statements.
  [timo]

- Put a marker interface on the default edit view so viewlets
  can be registered for it.
  [davisagli]

- Ensure FTI's isConstructionAllowed method returns a boolean.
  [danjacka]

- Hide the Dublin Core tab and show the Properties tab for
  items when viewed in the ZMI.
  [davisagli]

- Avoid storing dublin core metadata on new instances unless it
  differs from the default values.
  [davisagli]

- Implement CMF's dublin core interfaces inline rather than
  depending on CMFDefault.
  [davisagli]

- Support GenericSetup structure import/export of Dexterity content.
  Content is serialized the same way as for WebDAV,
  using plone.rfc822. Not all field types are supported yet,
  but this at least gets the basics in place.

  GS import used to work by accident in a basic way for Dexterity
  containers. If you were using this, you'll need to recreate your
  exported files with the rfc822 serialization.
  [davisagli]

- Creator accessor should return encoded strings
  If your catalog was broken, try to clear & reindex Creator::

    cat.clearIndex('Creator')
    cat.manage_reindexIndex(['Creator'])

  [kiorky]

- Use the same message string for the default fieldset as Archetypes does.
  [davisagli]

2.1.3 (2013-05-26)
------------------

- Fail gracefully when a schema lookup fails due to schema that doesn't
  exist or no longer exists for some reason or another.
  [eleddy]


2.1.2 (2013-03-05)
------------------

- Merged Rafael Oliveira's (@rafaelbco) @content-core views from
  collective.cmfeditionsdexteritycompat.
  [rpatterson]

2.1.1 (2013-01-17)
------------------

* No longer add title and description fields to new FTIs by default.
  [davisagli, cedricmessiant]

* When pasting into a dexterity container check the FTI for the the pasted
  object to see if it is allowed in the new container.
  [wichert]

* Fixed schema caching. Previously, a non-persistent counter would be
  used as part of the cache key, and changes made to this counter in
  one process would obviously not propagate to other processes.

  Instead, the cache key now includes the schema and subtypes which
  are both retrieved from a FTI-specific volatile cache that uses the
  modification time as its cache key.
  [malthe]


2.1 (2013-01-01)
----------------

* Added Finnish translations.
  [pingviini]

* Overrride allowedContentTypes and invokeFactory from PortalFolder
  to mimic the behavior of Archetypes based folders. This allows the
  registration of IConstrainTypes adapters to actually have the
  expected effect.
  [gaudenzius]

* The default attribute accessor now also looks through subtypes
  (behaviors) to find a field default.
  [malthe]

* Added support in the FTI to look up behaviors by utility name when
  getting additional schemata (i.e. fields provided by behaviors).

  This functionality makes it possible to create a behavior where the
  interface is dynamically generated.
  [malthe]

* Return early for attributes that begin with two underscores.
  https://github.com/plone/plone.dexterity/pull/11
  [malthe]

* Make it possible to define a SchemaPolicy for the FTI
  [Frédéric Péters]
  [gbastien]

2.0 (2012-08-30)
----------------

* Add a UID method to Dexterity items for compatibility with the Archetypes
  API.
  [davisagli]

* Remove hard dependency on zope.app.content.
  [davisagli]

* Use standard Python properties instead of rwproperty.
  [davisagli]

* Removed support for Plone 3 / CMF 2.1 / Zope 2.10.
  [davisagli]

* Update package dependencies and imports as appropriate for Zope 2.12 & 2.13.
  [davisagli]

1.1.2 - 2012-02-20
------------------

* Fix UnicodeDecodeError when getting an FTI title or description with
  non-ASCII characters.
  [davisagli]

1.1.1 - 2012-02-20
------------------

* When deleting items from a container using manage_delObjects,
  check for the "DeleteObjects" permission on each item being
  deleted. This fixes
  http://code.google.com/p/dexterity/issues/detail?id=252
  [davisagli]

1.1 - 2011-11-26
----------------

* Added Italian translation.
  [zedr]

* Ensure that a factory utility really isn't needed before removing it.
  [lentinj]

* Work around issue where user got a 404 upon adding content if a content
  rule had moved the new item to a different folder. This closes
  http://code.google.com/p/dexterity/issues/detail?id=240
  [davisagli]

* Added events: IEditBegunEvent, IEditCancelledEvent, IEditFinished,
  IAddBegunEvent, IAddCancelledEvent
  [jbaumann]

* Make sure Dexterity content items get UIDs when they are created if
  ``plone.uuid`` is present. This closes
  http://code.google.com/p/dexterity/issues/detail?id=235
  [davisagli]

* Make sure the Title() and Description() accessors of containers return an
  encoded bytestring as expected for CMF-style accessors.
  [buchi]

* Added zh_TW translation.
  [marr, davisagli]

1.0.1 - 2011-09-24
------------------

* Support importing the ``add_view_expr`` property of the FTI via GenericSetup.
  This closes http://code.google.com/p/dexterity/issues/detail?id=192
  [davisagli]

* Make it possible to use DefaultAddForm without a form wrapper.
  [davisagli]

* Make sure the Subject accessor returns an encoded bytestring as expected for
  CMF-style accessors. This fixes
  http://code.google.com/p/dexterity/issues/detail?id=197
  [davisagli]

* Added pt_BR translation.
  [rafaelbco, davisagli]


1.0 - 2011-05-20
----------------

* Make sure the Title and Description accessors handle a value of None.
  [davisagli]

* Make sure the Title() accessor for Dexterity content returns an encoded
  bytestring as expected for CMF-style accessors.
  [davisagli]

1.0rc1 - 2011-04-30
-------------------

* Look up additional schemata by adapting to IBehaviorAssignable in cases
  where a Dexterity instance is available. (The list of behaviors in the
  FTI is still consulted for add forms.)
  [maurits]

* Explicitly load CMFCore ZCML.
  [davisagli]

* Add ids to group fieldsets.
  [elro]

* Do a deep copy instead of shallow when assigning field defaults. Content
  generated via script wound up with linked list (and other
  AbstractCollection) fields.
  [cah190, esteele]

* Make setDescription coerce to unicode in the same way as setTitle.
  [elro]

* Change the FTI default to enable dynamic view.
  [elro]

* Setup folder permissions in the same way as Archetypes so copy / paste /
  rename work consistently with the rest of Plone.
  [elro]

* Make sure the typesUseViewActionInListings property is respected when
  redirecting after edit.
  [elro, davisagli]

* Fix #145: UnicodeDecodeError After renaming item from @@folder_contents
  [toutpt]

1.0b7 - 2011-02-11
------------------

* Add adapter for plone.rfc822.interfaces.IPrimaryFieldInfo.
  [elro]

* Fixed deadlock in synchronized methods of schema cache by using
  threading.RLock instead of threading.Lock.
  [jbaumann]

* Add Spanish translation.
  [dukebody]

* Add French translation.
  [toutpt]


1.0b6 - 2010-08-30
------------------

* Send ObjectCreatedEvent event from createContent utility method.
  [wichert]

* Update content base classes to use allow keyword arguments to set
  initial values for instance variables.
  [wichert]

* Avoid empty <div class="field"> tag for title and description in
  item.pt.
  [gaudenzius]


1.0b5 - 2010-08-05
------------------

* Fix folder ordering bug.
  See: http://code.google.com/p/dexterity/issues/detail?id=113
  [optilude]

* Switch to the .Title() and .Description() methods of fti when used in
  a translatable context, to ensure that these strings are translated.
  [mj]

* Add Norwegian translation.
  [mj]


1.0b4 - 2010-07-22
------------------

* Improve robustness: catch and log import errors when trying to resolve
  behaviours.
  [wichert]

* Add German translation from Christian Stengel.
  [wichert]


1.0b3 - 2010-07-19
------------------

* Clarify license to GPL version 2 only.
  [wichert]

* Configure Babel plugins for i18n extraction and add a Dutch translation.
  [wichert]


1.0b2 - 2010-05-24
------------------

* Fix invalid license declaration in package metadata.
  [wichert]

* Do not assume "view" is the right immediate view - in some cases
  it might not exist. Instead use the absolute URL directly.
  [wichert]


1.0b1 - 2010-04-20
------------------

* Update the label for the default fieldset to something more humane.
  [wichert]

* Make the default add form extend BrowserPage to avoid warnings about
  security declarations for nonexistent methods.  This closes
  http://code.google.com/p/dexterity/issues/detail?id=69
  [davisagli]

* For now, no longer ensure that Dexterity content provides ILocation (in
  particular, that it has a __parent__ pointer), since that causes problems
  when exporting in Zope 2.10.
  [davisagli]

* Don't assume the cancel and actions buttons are always present in the
  default forms.
  [optilude]

1.0a3 - 2010-01-08
------------------

* require zope.filerepresentation>=3.6.0 for IRawReadFile
  [csenger]

1.0a2 - 2009-10-12
------------------

* Added support for zope.size.interfaces.ISized. An adapter to this interface
  may be used to specify the file size that is reported in WebDAV operations
  or used for Plone's folder listings. This requires that the sizeForSorting()
  method is implemented to return a tuple ('bytes', numBytes), where numBytes
  is the size in bytes.
  [optilude]

* Added support for WebDAV. This is primarily implemented by adapting content
  objects to the IRawReadFile and IRawWriteFile interfaces from the
  zope.filerepresentation package. The default is to use plone.rfc822 to
  construct an RFC(2)822 style message containing all fields. One or more
  fields may be marked with the IPrimaryField interface from that package,
  in which case they will be sent in the body of the message.

  In addition, the creation of new files (PUT requests to a null resource) is
  delegated to an IFileFactory adapter, whilst the creation of new directories
  (MKCOL requests) is delegated to an IDirectoryFactory adapter. See
  zope.filerepresentation for details, and filerepresentation.py for the
  default implementation.
  [optilude]

* Move AddViewActionCompat to the second base class of DexterityFTI, so that
  the FTI interfaces win over IAction. This fixes a problem with GenericSetup
  export: http://code.google.com/p/dexterity/issues/detail?id=79
  [optilude]

* Add getMapping() to AddViewActionCompat.
  Fixes http://code.google.com/p/dexterity/issues/detail?id=78
  [optilude]

1.0a1 - 2009-07-25
------------------

* Initial release
