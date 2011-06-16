from zope.component.interfaces import ObjectEvent
from zope.interface import implements

from plone.dexterity import interfaces


class EditBegunEvent(ObjectEvent):
    """An edit operation was begun
    """
    implements(interfaces.IEditBegunEvent)


class AddBegunEvent(ObjectEvent):
    """An add operation was begun. The event context is the folder,
    since the object does not exist yet.
    """
    implements(interfaces.IAddBegunEvent)


class EditCancelledEvent(ObjectEvent):
    """An edit operation was cancelled
    """
    implements(interfaces.IEditCancelledEvent)


class AddCancelledEvent(ObjectEvent):
    """An add operation was cancelled. The event context is the folder,
    since the object does not exist yet.
    """
    implements(interfaces.IAddCancelledEvent)


class EditFinishedEvent(ObjectEvent):
    """Edit was finished and contents are saved. This event is fired
    even when no changes happen (and no modified event is fired.)
    """
    implements(interfaces.IEditFinishedEvent)
