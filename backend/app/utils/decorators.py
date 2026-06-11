from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt

def roles_required(*roles):
    """
    Decorator that checks the JWT 'role' claim against allowed roles.
    Usage:
        @jwt_required()
        @roles_required("admin")
        def my_route(): ...
    
    Always use AFTER @jwt_required() — jwt_required verifies
    the token exists, roles_required checks what's inside it.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get("role")
            if user_role not in roles:
                return jsonify({
                    "error": "Forbidden",
                    "message": f"Requires one of these roles: {', '.join(roles)}"
                }), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(fn):
    """Shortcut decorator — admin role only."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get("role") != "admin":
            return jsonify({
                "error": "Forbidden",
                "message": "Admin access required"
            }), 403
        return fn(*args, **kwargs)
    return wrapper


def guard_or_admin_required(fn):
    """Shortcut decorator — guard or admin."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get("role") not in ("admin", "guard"):
            return jsonify({
                "error": "Forbidden",
                "message": "Guard or admin access required"
            }), 403
        return fn(*args, **kwargs)
    return wrapper