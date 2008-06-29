from AccessControl.SecurityInfo import SecurityInfo
from AccessControl.SecurityInfo import ACCESS_PRIVATE
from AccessControl.SecurityInfo import ACCESS_PUBLIC
from AccessControl.SecurityInfo import ACCESS_NONE

from AccessControl.PermissionRole import PermissionRole

# 1. Class uses ClassSecurityInfo
# 2. ClassSecurityInfo stores declarations in self.names[name] = permission
# 3. InitializeClass is called
# 4.1. Calls security_info.apply(class)
# 4.1.1. Sets __ac_permissions__ based on self.names -- (('permission 1': ('name1', 'name2',),)
#                                                        ('permission 2': ('name3',),))
# 4.2. Calls AccessControl.Permission.registerPermissions -- lets permissions spring to life
# 4.3. Creates a PermissionRole() for each __ac_permission__ and sets role

class InstanceSecurityInfo(SecurityInfo):
    """Allow setting of security on an instance, rather than a class
    """
    
    # XXX: This doesn't seem to work as we'd expect - fields are accessible
    # regardless of settings made using this class.
    
    __roles__ = ACCESS_PRIVATE

    apply__roles__ = ACCESS_PRIVATE
    def apply(self, instance):
        """Apply security information to the given instance.
        """
        
        # This code is liberally borrowed from AccessControl.SecurityInfo :)

        instance_dict = instance.__dict__
        instance_permissions = set()

        # Check the class for an existing __ac_permissions__ and
        # incorporate that if present to support older classes or
        # classes that haven't fully switched to using SecurityInfo.
        if instance_dict.has_key('__ac_permissions__'):
            for item in instance_dict['__ac_permissions__']:
                permission_name = item[0]
                self._setaccess(item[1], permission_name)
                if len(item) > 2:
                    self.setPermissionDefault(permission_name, item[2])

        # Set __roles__ for attributes declared public or private.
        # Collect protected attribute names in ac_permissions.
        
        class_permissions = getattr(instance.__class__, '__ac_permissions__', ())
        
        ac_permissions = dict([(permission, list(names),) for permission, names in class_permissions])
        for name, access in self.names.items():
            instance_permissions.add(name)
            if access in (ACCESS_PRIVATE, ACCESS_PUBLIC, ACCESS_NONE):
                setattr(instance, '%s__roles__' % name, access)
            else:
                if not ac_permissions.has_key(access):
                    ac_permissions[access] = []
                ac_permissions[access].append(name)

        # Now transform our nested dict structure into the nested tuple
        # structure expected of __ac_permissions__ attributes and set
        # it on the class object.
        getRoles = self.roles.get
        __ac_permissions__ = []
        permissions = ac_permissions.items()
        permissions.sort()
        for permission_name, names in permissions:
            roles = getRoles(permission_name, ())
            if len(roles):
                entry = (permission_name, tuple(names), tuple(roles.keys()))
            else:
                entry = (permission_name, tuple(names))
            __ac_permissions__.append(entry)
        for permission_name, roles in self.roles.items():
            if permission_name not in ac_permissions:
                entry = (permission_name, (), tuple(roles.keys()))
                __ac_permissions__.append(entry)
        
        setattr(instance, '__ac_permissions__', tuple(__ac_permissions__))
        
        for acp in __ac_permissions__:
            pname, mnames = acp[:2]
            if len(acp) > 2:
                roles = acp[2]
                pr = PermissionRole(pname, roles)
            else:
                pr=PermissionRole(pname)
            for mname in mnames:
                # Skip things we didn't set at the instance level at all
                if mname not in instance_permissions:
                    continue
                setattr(instance, mname+'__roles__', pr)