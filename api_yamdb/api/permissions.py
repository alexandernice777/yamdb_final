from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrReadOnly(BasePermission):
    """ADMIN может редактировать все;
    остальные могут только смотреть."""

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return request.user.is_admin
        return request.method in SAFE_METHODS


class IsAuthorModeratorAdminOrReadOnly(BasePermission):
    """Автор может редактировать только то, что сам создал;
    MODERATOR/ADMIN могут редактировать все;
    остальные могут только смотреть."""

    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.method in SAFE_METHODS
                or request.user == obj.author
                or request.user.is_moderator
                or request.user.is_admin)


class IsAdminStaffOnly(BasePermission):
    """Только ADMIN/SUPERUSER имеют доступ к информации."""

    def has_permission(self, request, view):
        return request.user.is_admin
