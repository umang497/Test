from django.contrib import admin
from reversion_compare.admin import CompareVersionAdmin

from userman.models import User


@admin.register(User)
class UsersAdmin(CompareVersionAdmin):
    pass
