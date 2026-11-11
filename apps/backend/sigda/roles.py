from functools import wraps

from django.core.exceptions import PermissionDenied


from .role_schema import ROLES


def role_for(user):
    if not user.is_authenticated:
        return None
    names = set(user.groups.values_list("name", flat=True))
    roles = [role for role in ROLES if f"SIGDA_{role}" in names]
    return roles[0] if len(roles) == 1 else None


def require_ops(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if role_for(request.user) != "OPS":
            raise PermissionDenied("Cette action appartient au profil OPS.")
        return view(request, *args, **kwargs)
    return wrapped


def workspace_role(request):
    role = role_for(request.user)
    return {"workspace_role": role, "role_info": ROLES.get(role), "is_ops": role == "OPS", "workflow_roles": ROLES}
