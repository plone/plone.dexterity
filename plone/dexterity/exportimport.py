# -*- coding: utf-8 -*-
from csv import reader
from csv import writer
from Products.GenericSetup.content import _globtest
from Products.GenericSetup.content import FauxDAVRequest
from Products.GenericSetup.content import FauxDAVResponse
from Products.GenericSetup.content import FolderishExporterImporter
from Products.GenericSetup.interfaces import IContentFactoryName
from Products.GenericSetup.interfaces import IFilesystemExporter
from Products.GenericSetup.interfaces import IFilesystemImporter
from Products.GenericSetup.utils import _getDottedName
from six import BytesIO
from six import StringIO
from zope.component import queryAdapter
from zope.interface import implementer

import six


@implementer(IFilesystemExporter, IFilesystemImporter)
class DexterityContentExporterImporter(FolderishExporterImporter):
    """Tree-walking exporter / importer for Dexterity types.

    This is based on the generic one in GenericSetup,
    but it uses Dexterity's rfc822 serialization support
    to serialize the content.

    Folderish instances are mapped to directories within the 'structure'
    portion of the profile, where the folder's relative path within the site
    corresponds to the path of its directory under 'structure'.

    The subobjects of a folderish instance are enumerated in the '.objects'
    file in the corresponding directory.  This file is a CSV file, with one
    row per subobject, with the following structure::

     "<subobject id>","<subobject portal_type>"

    Subobjects themselves are represented as individual files or
    subdirectories within the parent's directory.
    """

    def __init__(self, context):
        self.context = context

    def export(self, export_context, subdir, root=False):
        """See IFilesystemExporter."""
        context = self.context

        if not root:
            subdir = "%s/%s" % (subdir, context.getId())

        exportable = self.listExportableItems()

        stream = StringIO()
        csv_writer = writer(stream)

        for object_id, object, adapter in exportable:

            factory_namer = IContentFactoryName(object, None)
            if factory_namer is None:
                factory_name = _getDottedName(object.__class__)
            else:
                factory_name = factory_namer()

            csv_writer.writerow((object_id, factory_name))

        export_context.writeDataFile(
            ".objects",
            text=stream.getvalue(),
            content_type="text/comma-separated-values",
            subdir=subdir,
        )

        props = context.manage_FTPget()
        if hasattr(props, "read"):
            props = props.read()
        export_context.writeDataFile(
            ".data",
            text=props,
            content_type="text/plain",
            subdir=subdir,
        )

        for object_id, object, adapter in exportable:
            if adapter is not None:
                adapter.export(export_context, subdir)

    def import_(self, import_context, subdir, root=False):
        """See IFilesystemImporter."""
        context = self.context
        if not root:
            subdir = "%s/%s" % (subdir, context.getId())

        data = import_context.readDataFile(".data", subdir)
        if data is not None:
            request = FauxDAVRequest(BODY=data, BODYFILE=BytesIO(data))
            response = FauxDAVResponse()
            context.PUT(request, response)

        preserve = import_context.readDataFile(".preserve", subdir)
        must_preserve = self._mustPreserve()

        prior = context.objectIds()

        if not preserve:
            preserve = []
        else:
            # Make sure ``preserve`` is a native string
            if six.PY3 and not isinstance(preserve, str):
                preserve = preserve.decode("utf-8")
            preserve = _globtest(preserve, prior)

        preserve.extend([x[0] for x in must_preserve])

        for id in prior:
            if id not in preserve:
                context._delObject(id)

        objects = import_context.readDataFile(".objects", subdir)
        if objects is None:
            return

        dialect = "excel"
        if six.PY3 and not isinstance(objects, str):
            objects = objects.decode("utf-8")
        stream = StringIO(objects)

        rowiter = reader(stream, dialect)
        rows = filter(None, tuple(rowiter))

        existing = context.objectIds()

        for object_id, type_name in rows:

            if object_id not in existing:
                object = self._makeInstance(
                    object_id, type_name, subdir, import_context
                )
                if object is None:
                    logger = import_context.getLogger("SFWA")
                    logger.warning(
                        "Couldn't make instance: %s/%s" % (subdir, object_id)
                    )
                    continue

            wrapped = context._getOb(object_id)

            adapted = queryAdapter(wrapped, IFilesystemImporter)
            if adapted is not None:
                adapted.import_(import_context, subdir)
