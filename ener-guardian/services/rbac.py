from functools import wraps
from flask import abort, request
from flask_login import current_user

def requires_role(*roles):
    """Decorator to restrict access to users with specified roles.
    Usage:
        @requires_role('admin')
        def view():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            user_role = getattr(current_user, 'papel', None)
            if user_role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator
