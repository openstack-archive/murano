import muranoapi.dsl.principal_objects.sys_object


def register(class_loader):
    sys_object = muranoapi.dsl.principal_objects.sys_object
    class_loader.import_class(sys_object.SysObject)
