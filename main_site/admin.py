import csv
import json

from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import path

from main_site.forms import HeatBuilderForm
from main_site.heat_workbook import build_printable_heat_workbook
from main_site.heats import build_heat_assignments
from main_site.helpers import send_email
from main_site.models import Result, Registrant, current_year

class RegistrantAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "age", "seed_time", "email", "gender", "sponsor", "hometown")
    list_filter = ("year",)

class ResultAdmin(admin.ModelAdmin):
    list_display = ("registrant__first_name", "registrant__last_name", "time")

class MyAdminSite(admin.AdminSite):
    site_header = "Guinea Pig Mile Admin"
    site_title = "Guinea Pig Mile Admin Portal"
    index_title = "Welcome to Guinea Pig Mile Administration"
    index_template = "admin/custom_index.html"

    def get_urls(self):
        urls = super().get_urls()
        
        urls = [
            path('heats/', self.admin_view(self.heats_view), name='build_heats'),
            path('email/', self.admin_view(self.email_view), name='email_registrants'),
            path('export/', self.admin_view(self.export_view), name='export_registrants'),
            path('copy-registrant-emails', self.admin_view(self.copy_registrant_emails_view), name='copy_registrant_emails'),
        ] + urls

        return urls

    def heats_view(self, request):
        year = current_year()
        registrants = Registrant.objects.filter(year=year)

        if request.method == 'POST':
            form_data = request.POST.copy()
            if 'largest_heat_size' not in form_data and 'regular_heat_size' in form_data:
                form_data['largest_heat_size'] = form_data['regular_heat_size']

            form = HeatBuilderForm(form_data)
            if form.is_valid():
                assignments = build_heat_assignments(
                    registrants,
                    form.cleaned_data['largest_heat_size'],
                    form.cleaned_data['men_championship_size'],
                    form.cleaned_data['women_championship_size'],
                )
                if request.POST.get('format') == 'xlsx':
                    return self._heat_xlsx_response(assignments, year)
                return self._heat_csv_response(assignments, year)
        else:
            form = HeatBuilderForm()

        context = {
            **self.each_context(request),
            'form': form,
            'registrant_count': registrants.count(),
            'current_year': year,
        }

        return render(request, "admin/build_heats.html", context)

    def _heat_csv_response(self, assignments, year):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="heats_{year}.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Heat Number',
            'Heat Name',
            'Heat Type',
            'Position In Heat',
            'First Name',
            'Last Name',
            'Email',
            'Date of Birth',
            'Gender',
            'Seed Time',
            'Sponsor',
            'Hometown',
        ])

        for assignment in assignments:
            registrant = assignment.registrant
            writer.writerow([
                assignment.heat_number,
                assignment.heat_name,
                assignment.heat_type,
                assignment.position,
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

    def _heat_xlsx_response(self, assignments, year):
        response = HttpResponse(
            build_printable_heat_workbook(assignments, year),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="heats_{year}.xlsx"'
        return response
    
    def export_view(self, request):
        RACE_DAY_FIELDS = ['Heat Number', 'Sticker Number', 'Unofficial Time', 'Official Time', 'Place', 'Heat Place', 'Division Place']

        year = current_year()
        registrants = Registrant.objects.all().filter(year=year)
        registrants = sorted(registrants, key=lambda x: x.seed_time_seconds, reverse=True)
        
        if request.method == 'POST':
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="registrants_{year}.csv"'
            
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
            'current_year': year,
        }
        
        return render(request, "admin/export_registrants.html", context)

    def copy_registrant_emails_view(self, request):
        year = current_year()
        registrants = Registrant.objects.all().filter(year=year)
        emails = [r.email for r in registrants]
        return HttpResponse(json.dumps(emails), content_type='application/json', status=200)

    def email_view(self, request):
        year = current_year()
        registrants = Registrant.objects.all().filter(year=year)
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
            'current_year': year,
        }
        
        return render(request, "admin/email_registrants.html", context)

# Create the custom admin site
custom_admin_site = MyAdminSite(name='guinea_pig_admin')

# Register models with the custom admin site
custom_admin_site.register(Result, ResultAdmin)
custom_admin_site.register(Registrant, RegistrantAdmin)
