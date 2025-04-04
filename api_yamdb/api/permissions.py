from rest_framework import permissions


class ReadOnlyPermission(permissions.BasePermission):
    """Анонимные или обычные залогиненные пользователи могут только читать."""

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class AdminPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return (request.user.is_authenticated and request.user.is_admin())


class IsAuthorOrAdminOrModerator(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return (
            obj.author == request.user
            or request.user.is_moderator()
            or request.user.is_admin()
        )
