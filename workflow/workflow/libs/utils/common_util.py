

def chain_getattr(obj, *args, default=None, raise_error=False):
    """
    Chain get object attribute with no exception.
    e.g:
        request.user.group.name
        If the user object has no group, there will be raised an error(User object has no attribute 'group')
        Instead you can use chain_getattr(request, 'user', 'group', 'name', raise_error=False) to avoid the error.
    """
    for arg in args:
        has_attr = hasattr(obj, arg)
        if not has_attr:
            if raise_error:
                raise AttributeError(f'{obj} object has no attribute {arg}')
            return default
        obj = getattr(obj, arg)
    return obj

