from rest_framework.permissions import BasePermission

from userman.models import UserLevel


class ApplyLoanPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.user_level != UserLevel.BANNED


class ManageLoanPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.user_level == UserLevel.ADMIN
