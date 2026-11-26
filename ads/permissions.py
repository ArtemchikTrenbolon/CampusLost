from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrModerator(BasePermission):
    """Менять и удалять объявление может автор или модератор."""
    message = 'Изменять объявление может только его автор или модератор'

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return user.is_authenticated and (obj.author_id == user.id or user.is_moderator)