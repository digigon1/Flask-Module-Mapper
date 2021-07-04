from inspect import getmembers, ismodule

from flask import request

# Mapping functions for types
_type_map = {
    'i': int,
    'f': float,
    'c': complex,
    's': str,
    'b': lambda s: s.lower() in ['true', 't', 'yes', 'y', '1']
}

# List all functions in obj as flask endpoints recursively
def _list_endpoints(obj, max_depth=5, pos_args_key='_args'):
    # Limit recursion to max_depth
    if max_depth == 0:
        return []

    result = []
    for m in getmembers(obj):
        # Ignore non-public members
        if m[0].startswith('_'):
            continue

        # Create mapping for functions
        if callable(m[1]):
            # Create function for flask endpoint,
            # which parses positional arguments from pos_args_key
            # and parses and passes keyword arguments
            def create_function_endpoint(name, func):
                def f():
                    try:
                        # Create keywork args map
                        kwargs = dict(request.args)

                        # Parse positional arguments
                        pos_args = kwargs.get(pos_args_key)
                        if pos_args:
                            # Delete positional arguments from keyword map
                            del kwargs[pos_args_key]

                            # Split arguments
                            pos_args = pos_args.split(';')

                            # Parse each positional argument and add to fixed list
                            fixed_pos_args = []
                            for val in pos_args:
                                # Format of arguments: <type>:<value>
                                val_split = val.split(':', 1)
                                val_fixed = val_split[-1]
                                if len(val_split) > 1:
                                    val_fixed = _type_map.get(val_split[0], str)(val_fixed)

                                # Add fixed positional argument to list
                                fixed_pos_args.append(val_fixed)
                        else:
                            # If no positional arguments, set array to empty
                            fixed_pos_args = []

                        # Fix keyword arguments
                        for key in kwargs:
                            val = kwargs[key].split(';')
                            if len(val) > 1:
                                kwargs[key] = _type_map.get(val[0], str)(val[1])
                        
                        # Run function and display result
                        result = func(*fixed_pos_args, **kwargs)
                        return str(result)
                    except Exception as e:
                        # Fail safely and display exception
                        return str(e), 500

                # Rename function to avoid overwrite of existing functions with same name
                f.__name__ = name
                return f

            # Build endpoint url
            endpoint = f'/{obj.__name__}/{m[0]}'

            # Append url, function pair
            result.append((endpoint, create_function_endpoint('_' + obj.__name__ + '_' + m[0], m[1])))

        # Create module mapping via recursion
        elif ismodule(m[1]):
            # Recurse into other modules
            for endpoint, function in _list_endpoints(m[1], max_depth - 1):
                # Override function name to include module name
                function.__name__ = '_' + obj.__name__ + '_' + function.__name__

                # Append fixed url, function pair
                result.append((f'/{obj.__name__}{endpoint}', function))

        # Create mapping for all other members
        else:
            # Create function for flask endpoint,
            # which displays variable value
            def create_variable_endpoint(name, value):
                def f():
                    return str(value)

                # Rename function to avoid overwrite of existing functions with same name
                f.__name__ = name
                return f

            # Build endpoint url
            endpoint = f'/{obj.__name__}/{m[0]}'

            # Append url, function pair
            result.append((endpoint, create_variable_endpoint('_' + obj.__name__ + '_' + m[0], m[1])))

    return result



class ModuleMapper():
    """Maps given objects to flask endpoints"""
    def __init__(self, app):
        super(ModuleMapper, self).__init__()
        self.app = app

    # Register new handlers for custom types
    def register_type_handler(self, new_type, func):
        _type_map[new_type] = func

    # Map module functions to flask endpoints
    def map(self, obj):
        for endpoint, function in _list_endpoints(obj):
            self.app.route(endpoint)(function)
