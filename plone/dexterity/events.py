# -*- coding: utf-8 -*-
from plone.dexterity import interfaces
from zope.interface import implementer
from zope.interface.interfaces import ObjectEvent


@implementer(interfaces.IEditBegunEvent)
class EditBegunEvent(ObjectEvent):
    """An edit operation was begun"""


@implementer(interfaces.IAddBegunEvent)
class AddBegunEvent(ObjectEvent):
    """An add operation was begun. The event context is the folder,
    since the object does not exist yet.
    """


@implementer(interfaces.IEditCancelledEvent)
class EditCancelledEvent(ObjectEvent):
    """An edit operation was cancelled"""


@implementer(interfaces.IAddCancelledEvent)
class AddCancelledEvent(ObjectEvent):
    """An add operation was cancelled. The event context is the folder,
    since the object does not exist yet.
    """


@implementer(interfaces.IEditFinishedEvent)
class EditFinishedEvent(ObjectEvent):
    """Edit was finished and contents are saved. This event is fired
    even when no changes happen (and no modified event is fired.)
    """
