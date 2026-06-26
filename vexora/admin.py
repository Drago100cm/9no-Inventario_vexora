from django.contrib import admin

# Register your models here.

#--------------vista de grupos de usuarios----------------
from vexora.models import CustomUser


admin.site.register(CustomUser)
