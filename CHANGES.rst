Changelog
=========

2.2.0 (unreleased)
------------------

- Date index method works even if source field is a dexterity field
  wich provides a  datetime python value.
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
