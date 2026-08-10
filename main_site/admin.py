import csv
import json
import re
from urllib.parse import urlencode

from django.contrib import admin
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import path

from main_site.forms import HeatBuilderForm, ResultEntryForm
from main_site.heat_workbook import build_printable_heat_workbook
from main_site.heats import build_heat_assignments
from main_site.helpers import send_email
from main_site.models import Result, Registrant, current_year


class RegistrantAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "age",
        "seed_time",
        "email",
        "gender",
        "sponsor",
        "hometown",
    )
    list_filter = ("year",)
    search_fields = ("first_name", "last_name", "email")


class ResultAdmin(admin.ModelAdmin):
    list_display = ("registrant", "year", "time", "heat", "dnf")
    list_filter = ("year", "heat", "dnf")
    search_fields = (
        "registrant__first_name",
        "registrant__last_name",
        "registrant__email",
    )


class MyAdminSite(admin.AdminSite):
    site_header = "Guinea Pig Mile Admin"
    site_title = "Guinea Pig Mile Admin Portal"
    index_title = "Welcome to Guinea Pig Mile Administration"
    index_template = "admin/custom_index.html"

    def get_urls(self):
        urls = super().get_urls()

        urls = [
            path('heats/', self.admin_view(self.heats_view), name='build_heats'),
            path(
                'results/register/',
                self.admin_view(self.result_entry_view),
                name='register_results',
            ),
            path('email/', self.admin_view(self.email_view), name='email_registrants'),
            path('export/', self.admin_view(self.export_view), name='export_registrants'),
            path(
                'copy-registrant-emails',
                self.admin_view(self.copy_registrant_emails_view),
                name='copy_registrant_emails',
            ),
        ] + urls

        return urls

    def result_entry_view(self, request):
        year = current_year()
        query = request.GET.get('q', '').strip()
        current_heat = self._result_entry_heat_value(
            request.GET.get('current_heat', '')
        )
        heat_filter = self._result_entry_heat_value(
            request.GET.get('heat_filter', '')
        )
        posted_form = None
        posted_registrant_id = None

        if request.method == 'POST':
            query = request.POST.get('q', '').strip()
            current_heat = self._result_entry_heat_value(
                request.POST.get('current_heat', '')
            )
            heat_filter = self._result_entry_heat_value(
                request.POST.get('heat_filter', '')
            )
            posted_registrant_id = request.POST.get('registrant_id')
            action = request.POST.get('action', 'save_result')

            if action == 'assign_heat':
                if not current_heat:
                    messages.error(request, "Select a current heat first.")
                else:
                    try:
                        registrant = Registrant.objects.get(
                            pk=posted_registrant_id,
                            year=year,
                        )
                    except Registrant.DoesNotExist:
                        messages.error(request, "Select a current-year registrant.")
                    else:
                        result, _created = Result.objects.get_or_create(
                            registrant=registrant,
                            year=year,
                            defaults={
                                'time': '',
                                'heat': current_heat,
                                'dnf': False,
                            },
                        )
                        if result.heat != current_heat:
                            result.heat = current_heat
                            result.save(update_fields=['heat'])
                        messages.success(
                            request,
                            (
                                f"Added {registrant.first_name} "
                                f"{registrant.last_name} to {current_heat}."
                            ),
                        )
                        return redirect(
                            self._result_entry_url(
                                request.path,
                                query,
                                current_heat,
                                heat_filter,
                            )
                        )
            else:
                posted_form = ResultEntryForm(
                    request.POST,
                    auto_id=f"id_result_{posted_registrant_id or 'posted'}_%s",
                )

                if posted_form.is_valid():
                    try:
                        registrant = Registrant.objects.get(
                            pk=posted_form.cleaned_data['registrant_id'],
                            year=year,
                        )
                    except Registrant.DoesNotExist:
                        posted_form.add_error(None, "Select a current-year registrant.")
                    else:
                        Result.objects.update_or_create(
                            registrant=registrant,
                            year=year,
                            defaults={
                                'time': posted_form.cleaned_data['time'],
                                'heat': posted_form.cleaned_data['heat'],
                                'dnf': False,
                            },
                        )
                        messages.success(
                            request,
                            f"Result saved for {registrant.first_name} {registrant.last_name}.",
                        )
                        next_query = (
                            query or f"{registrant.first_name} {registrant.last_name}"
                        )
                        return redirect(
                            self._result_entry_url(
                                request.path,
                                next_query,
                                current_heat,
                                heat_filter,
                            )
                        )

        registrants = list(self._result_entry_registrants(year, query, heat_filter))
        existing_results = {
            result.registrant_id: result
            for result in Result.objects.filter(year=year, registrant__in=registrants)
        }
        rows = []

        for registrant in registrants:
            result = existing_results.get(registrant.pk)

            if (
                posted_form is not None
                and posted_registrant_id
                and str(registrant.pk) == str(posted_registrant_id)
            ):
                form = posted_form
            else:
                form = ResultEntryForm(
                    initial={
                        'registrant_id': registrant.pk,
                        'time': result.time if result else '',
                        'heat': result.heat if result else '',
                    },
                    auto_id=f"id_result_{registrant.pk}_%s",
                )

            rows.append(
                {
                    'registrant': registrant,
                    'result': result,
                    'form': form,
                    'is_in_current_heat': bool(
                        current_heat and result and result.heat == current_heat
                    ),
                    'status': self._result_entry_status(result),
                }
            )

        context = {
            **self.each_context(request),
            'current_year': year,
            'query': query,
            'current_heat': current_heat,
            'heat_filter': heat_filter,
            'heat_choices': Result.HEAT_CHOICES,
            'registrant_count': Registrant.objects.filter(year=year).count(),
            'results_heading': self._result_entry_heading(query, heat_filter),
            'rows': rows,
        }

        return render(request, "admin/register_results.html", context)

    def _result_entry_url(self, path, query, current_heat, heat_filter):
        params = {}
        if query:
            params['q'] = query
        if current_heat:
            params['current_heat'] = current_heat
        if heat_filter:
            params['heat_filter'] = heat_filter

        if not params:
            return path

        return f"{path}?{urlencode(params)}"

    def _result_entry_heading(self, query, heat_filter):
        if query and heat_filter:
            return f'Matches for "{query}" in {heat_filter}'
        if query:
            return f'Matches for "{query}"'
        if heat_filter:
            return f"{heat_filter} registrants"
        return ""

    def _result_entry_heat_value(self, value):
        value = value.strip()
        valid_heat_values = {choice[0] for choice in Result.HEAT_CHOICES}
        if value in valid_heat_values:
            return value
        return ""

    def _result_entry_status(self, result):
        if not result:
            return "Not saved"
        if not result.time:
            return "Heat assigned"
        return "Saved"

    def _result_entry_registrants(self, year, query, heat_filter):
        registrants = Registrant.objects.filter(year=year).order_by(
            'last_name',
            'first_name',
        )

        if heat_filter:
            assigned_registrant_ids = Result.objects.filter(
                year=year,
                heat=heat_filter,
            ).values('registrant_id')
            registrants = registrants.filter(pk__in=assigned_registrant_ids)

        name_filters = self._result_entry_name_filters(query)
        if not name_filters and not heat_filter:
            return registrants.none()

        combined_filter = Q()
        for name_filter in name_filters:
            combined_filter |= name_filter

        if not name_filters:
            return registrants.distinct()

        return registrants.filter(combined_filter).distinct()

    def _result_entry_name_filters(self, query):
        entries = [
            entry.strip()
            for entry in re.split(r"[\n,;]+", query.strip())
            if entry.strip()
        ]
        filters = []

        for entry in entries:
            name_filter = Q()
            for term in entry.split():
                name_filter &= (
                    Q(first_name__icontains=term) | Q(last_name__icontains=term)
                )
            filters.append(name_filter)

        return filters

    def heats_view(self, request):
        year = current_year()
        registrants = Registrant.objects.filter(year=year)

        if request.method == 'POST':
            form_data = request.POST.copy()
            if 'largest_heat_size' not in form_data and 'regular_heat_size' in form_data:
                form_data['largest_heat_size'] = form_data['regular_heat_size']

            form = HeatBuilderForm(form_data)
            if form.is_valid():
                try:
                    assignments = build_heat_assignments(
                        registrants,
                        form.cleaned_data['largest_heat_size'],
                        form.cleaned_data['men_championship_size'],
                        form.cleaned_data['women_championship_size'],
                        form.cleaned_data['coed_heat_count'],
                    )
                except ValueError as error:
                    form.add_error(None, str(error))
                else:
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
