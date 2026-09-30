from rest_framework.permissions import SAFE_METHODS, BasePermission


def is_business_admin(user):
    return bool(user and user.is_authenticated and user.is_business_admin)


class IsBusinessAdmin(BasePermission):
    def has_permission(self, request, view):
        return is_business_admin(request.user)


class IsBusinessAdminOrReadOnly(BasePermission):
    """Anyone can read (e.g. browse services), only the business admin can write."""

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or is_business_admin(request.user)
