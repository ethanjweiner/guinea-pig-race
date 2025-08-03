from django.contrib import admin
from main_site.models import Result, Registrant
import json
from datetime import datetime
from django.urls import path
from django.shortcuts import render
from django.http import HttpResponse
from main_site.helpers import send_email
import csv

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
            path('email/', self.admin_view(self.email_view), name='email_registrants'),
            path('export/', self.admin_view(self.export_view), name='export_registrants'),
            path('copy-registrant-emails', self.admin_view(self.copy_registrant_emails_view), name='copy_registrant_emails'),
        ] + urls

        return urls
    
    def export_view(self, request):
        RACE_DAY_FIELDS = ['Heat Number', 'Sticker Number', 'Unofficial Time', 'Official Time', 'Place', 'Heat Place', 'Division Place']

        current_year = datetime.now().year
        registrants = Registrant.objects.all().filter(year=current_year)
        registrants = sorted(registrants, key=lambda x: x.seed_time_seconds, reverse=True)
        
        if request.method == 'POST':
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="registrants_{current_year}.csv"'
            
            writer = csv.writer(response)
            # Write header

            writer.writerow([
                'First Name', 'Last Name', 'Email', 'Date of Birth', 
                'Gender', 'Seed Time', 'Sponsor', 'Hometown',
                *RACE_DAY_FIELDS
            ])
            
            # Write data
            for registrant in registrants:
                writer.writerow([
                    registrant.first_name,
                    registrant.last_name,
                    registrant.email,
                    registrant.date_of_birth,
                    registrant.gender,
                    registrant.seed_time,
                    registrant.sponsor or '',
                    registrant.hometown or '',
                ])
            
            return response
        
        context = {
            'registrant_count': len(registrants),
            'current_year': current_year,
        }
        
        return render(request, "admin/export_registrants.html", context)

    def copy_registrant_emails_view(self, request):
        current_year = datetime.now().year
        registrants = Registrant.objects.all().filter(year=current_year)
        emails = [r.email for r in registrants]
        return HttpResponse(json.dumps(emails), content_type='application/json', status=200)

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

