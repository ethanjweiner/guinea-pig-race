from django.http import HttpResponse
from django.template import loader
from main_site.models import Result, Registrant
from django.shortcuts import redirect
from django.core.exceptions import ValidationError
from main_site.helpers import send_email


def index(request):
    template = loader.get_template("home/index.html")

    return HttpResponse(template.render({}, request))


def home(_):
    return redirect("index")


def register(request):
    template = loader.get_template("register/index.html")

    if request.method == "POST":
        if request.POST["email"] != request.POST["email_confirm"]:
            return HttpResponse(
                template.render(
                    {
                        "success": False,
                        "error": "Emails do not match. Please try again.",
                    },
                    request,
                )
            )

        try:
            registrant = Registrant(
                first_name=request.POST["first_name"],
                last_name=request.POST["last_name"],
                email=request.POST["email"],
                date_of_birth=request.POST["date_of_birth"],
                gender=request.POST["gender"],
                seed_time=request.POST["seed_time"],
                sponsor=request.POST.get("sponsor", ""),
                hometown=request.POST.get("hometown", ""),
            )

            registrant.full_clean()
            registrant.save()
            send_email(
                "Guinea Pig Mile Registration",
                loader.get_template("email/index.html").render({"registrant": registrant}),
                [registrant.email],
            )

            return HttpResponse(template.render({"success": True}, request))

        except Exception as e:
            print("REGISTRATION ERROR: ", e)
            return HttpResponse(
                template.render(
                    {"success": False, "error": "There was an error with your registration. Please try again."},
                    request,
                )
            )

    return HttpResponse(template.render({}, request))


def awards(request):
    template = loader.get_template("awards/index.html")
    return HttpResponse(template.render({}, request))


def results(request):
    template = loader.get_template("results/index.html")
    available_years = list(Result.objects.order_by("year").values_list("year", flat=True).distinct())

    if not available_years:
        return HttpResponse(
            template.render(
                {
                    "year": None,
                    "men_results": [],
                    "women_results": [],
                    "previous_year": None,
                    "next_year": None,
                },
                request,
            )
        )

    requested_year = request.GET.get("year")
    try:
        year = int(requested_year) if requested_year else available_years[-1]
    except ValueError:
        year = available_years[-1]

    if year not in available_years:
        year = available_years[-1]

    year_index = available_years.index(year)
    previous_year = available_years[year_index - 1] if year_index > 0 else None
    next_year = available_years[year_index + 1] if year_index < len(available_years) - 1 else None

    # Get all results and sort in Python
    men_results = list(Result.objects.filter(registrant__gender="male", year=year))
    men_results.sort(key=lambda x: (x.dnf, x.time_seconds))
    
    women_results = list(Result.objects.filter(registrant__gender="female", year=year))
    women_results.sort(key=lambda x: (x.dnf, x.time_seconds))

    return HttpResponse(
        template.render(
            {
                "year": year,
                "men_results": men_results,
                "women_results": women_results,
                "previous_year": previous_year,
                "next_year": next_year,
            },
            request,
        )
    )


def about(request):
    template = loader.get_template("about/index.html")
    return HttpResponse(template.render({}, request))
