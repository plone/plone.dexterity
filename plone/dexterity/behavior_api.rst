==================================
API for interacting with behaviors
==================================

Behaviors are having an API.

It is not about writing new behaviors. Its is about using existing behaviors.

Target group are developers outside of Plones core, i.e. addon developers and integrators.

The API has two major goals:
- easy access: behaviors, both its data, getters, setters and functionality
- easy introspection: understand whats up with the content item

Design goals are:
- single entry point into the world of behaviors
- verbose
- hide ZCA and other magic
- practical for every days tasks
- simple enough, but do not hide behaviors completly

Given we have a simple content item::

    >>> from plone.dexterity.content import Item
    >>> context = Item()

Then API is an attribute on the content base class. It is an instance of the
``BehaviorAPI`` class::

    >>> print repr(context.behaviors)  # doctest: +ELLIPSIS
    <BehaviorAPI for Item (portal_type=None) at ...
      Behaviors used:
        There is no behavior set.
    >

