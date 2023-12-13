from rest_framework import permissions


class IsApprover(permissions.BasePermission):

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return request.user and request.user in obj.approvers.all()
