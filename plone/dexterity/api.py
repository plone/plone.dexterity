import zope.deferredimport

zope.deferredimport.defineFrom(
    'plone.supermodel.directives',
    'Schema', 'model'
)

zope.deferredimport.defineFrom(
    'plone.dexterity.content'
    'Item', 'Container'
)

