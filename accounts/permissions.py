from rest_framework.permissions import BasePermission


class IsModerator(BasePermission):
    """Доступ только для модераторов и администраторов."""
    message = 'Доступно только модераторам'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_moderator)