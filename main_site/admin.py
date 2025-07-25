from django.contrib import admin
from main_site.models import Result, Registrant
from datetime import datetime
from django.urls import path
from django.shortcuts import render
from main_site.helpers import send_email

class RegistrantAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "seed_time", "email", "gender", "sponsor", "hometown")
    list_filter = ("year",)

class ResultAdmin(admin.ModelAdmin):
    list_display = ("registrant__first_name", "registrant__last_name", "time")

class MyAdminSite(admin.AdminSite):
    site_header = "Guinea Pig Mile Admin"
    site_title = "Guinea Pig Mile Admin Portal"
    index_title = "Welcome to Guinea Pig Mile Administration"

    def get_urls(self):
        urls = super().get_urls()
        
        urls = [
            path('email/', self.admin_view(self.email_view), name='email_registrants')
        ] + urls

        print("GETTING URLS")
        print(urls)
        
        return urls

    def email_view(self, request):
        current_year = datetime.now().year
        registrants = Registrant.objects.all().filter(year=current_year)
        message = None
        
        if request.method == 'POST':
            subject = request.POST.get('subject')
            message_text = request.POST.get('message')
            
            if subject and message_text:
                try:
                    # Get all registrants for the current year
                    recipient_emails = [r.email for r in registrants]

                    # Send email to all registrants
                    send_email(subject, message_text, recipient_emails, 'plain')
                    
                    message = f"Email sent successfully to {len(recipient_emails)} registrants!"
                except Exception as e:
                    message = f"Error sending email: {str(e)}"
            else:
                message = "Please fill in both subject and message fields."
        
        context = {
            'registrant_count': registrants.count(),
            'message': message,
            'current_year': current_year,
        }
        
        return render(request, "admin/email_registrants.html", context)

# Create the custom admin site
custom_admin_site = MyAdminSite(name='guinea_pig_admin')

# Register models with the custom admin site
custom_admin_site.register(Result, ResultAdmin)
custom_admin_site.register(Registrant, RegistrantAdmin)

