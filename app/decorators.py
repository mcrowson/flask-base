from functools import wraps

from flask import abort
from flask.ext.login import current_user


def group_required(permission):
    """Restrict a view to users with the given permission."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.member_of_group(group_name):
                abort(403)
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def admin_required(f):
    return group_required('administrator')(f)
