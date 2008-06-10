import os.path

from zope.interface import implements

from plone.dexterity.interfaces import IDynamicFTI
from plone.dexterity.fti.base import DexterityFTI, _fix_properties

from plone.supermodel import load_string, load_file

class DynamicFTI(DexterityFTI):
    """A Dexterity FTI that is managed entirely through-the-web
    """
    
    implements(IDynamicFTI)
    
    _properties = DexterityFTI._properties + (
        { 'id': 'model_source', 
          'type': 'text',
          'mode': 'w',
          'label': 'Model source',
          'description': "XML source for the type's model. Note that this takes " +
                         "precendence over any model file."
        },
        { 'id': 'model_file', 
          'type': 'string',
          'mode': 'w',
          'label': 'Model file',
          'description': "Path to file containing the schema model. This can be " +
                         "relative to a package, e.g. 'my.package:myschema.xml'."
        },
    )
    
    def __init__(self, *args, **kwargs):
        super(DynamicFTI, self).__init__(*args, **kwargs)
        
        self.model_source = self.model_source = """\
<model>
    <schema>
        <field name="title" type="zope.schema.TextLine">
            <title>Title</title>
            <required>True</required>
        </field>
        <field name="description" type="zope.schema.Text">
            <title>Description</title>
            <required>False</required>
        </field>
    </schema>
</model>
"""
        self.model_file = ""
    
    def lookup_model(self):
        # TODO: Cache model, invalidate when FTI modified
        model = None
        
        if self.model_source:
            model = load_string(self.model_source, policy=u"dexterity")
        elif self.model_file:
            colons = self.model_file.count(':')
            model_file = self.model_file
            
            # We have a package and not an absolute Windows path
            if colons == 1 and self.model_file[1:3] != ':\\':
                package, filename = self.model_file.split(':')
                try:
                    mod = __import__(package)
                except ImportError:
                    raise ValueError(u"Invalid package %s specified for model file in %s" % package, self.getId())
                model_file = os.path.split(mod.__file__)[0]
            else:
                if not os.path.isabs(model_file):
                    raise ValueError(u"Model file name %s is not an absolute path and does not contain a package name in %s" % model_file, self.getId())
            
            model = load_file(model_file, policy=u"dexterity")
            
        return model

_fix_properties(DynamicFTI)