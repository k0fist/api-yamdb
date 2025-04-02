from rest_framework import permissions


class AdminPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return (request.user.is_authenticated and request.user.is_admin())


class IsAuthorOrAdminOrModerator(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_authenticated
            and (
                obj.author == request.user
                or request.user.is_moderator_or_admin()
            )
        )
