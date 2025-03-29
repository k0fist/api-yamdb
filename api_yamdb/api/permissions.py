from rest_framework import permissions


class AdminPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (
                request.user.role == 'admin'
                or request.user.is_staff
            )
        )


class IsAuthorOrAdminOrModerator(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return (obj.author == request.user
                or (request.user.role == 'admin' or request.user.is_staff)
                or request.user.role == 'moderator')

