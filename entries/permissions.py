from rest_framework import permissions

class IsAccountantOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow accountants to create entries.
    Managers can modify entries (approve/reject).
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True  # Allow safe methods (GET, HEAD, OPTIONS)
        
        # Allow creation (POST) only if user is an accountant
        return request.user.role == 'accountant'

    def has_object_permission(self, request, view, obj):
        # Allow managers to modify (approve/reject) entries
        return request.user.role == 'manager'
    