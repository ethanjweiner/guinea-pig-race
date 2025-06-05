from django.contrib import admin
from main_site.models import Result, Registrant

class RegistrantAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "seed_time", "email", "gender", "sponsor", "hometown")
    list_filter = ("year",)

class ResultAdmin(admin.ModelAdmin):
    list_display = ("registrant__first_name", "registrant__last_name", "time")

admin.site.register(Result, ResultAdmin)
admin.site.register(Registrant, RegistrantAdmin)