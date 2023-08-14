

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


def sort_nodes_by_parent(nodes):
    parent_map = {node['id']: node for node in nodes}

    def get_children(node_id):
        return [node for node in nodes if node['parent_id'] == node_id]

    def dfs(node_id):
        result.append(parent_map[node_id])
        children = get_children(node_id)
        for child in children:
            dfs(child['id'])

    result = []
    root_nodes = [node for node in nodes if node['parent_id'] is None]
    for root in root_nodes:
        dfs(root['id'])

    return result
