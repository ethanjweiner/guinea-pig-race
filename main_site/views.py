from django.http import HttpResponse
from django.template import loader
from main_site.models import Result, Registrant
from django.shortcuts import redirect
from django.core.exceptions import ValidationError
from main_site.helpers import send_email


def index(request):
    template = loader.get_template("home/index.html")

    men_results = list(Result.objects.filter(registrant__gender="male", year=2025))
    men_results.sort(key=lambda x: (x.dnf, x.time_seconds))
    men_results = men_results[:5]

    
    women_results = list(Result.objects.filter(registrant__gender="female", year=2025))
    women_results.sort(key=lambda x: (x.dnf, x.time_seconds))
    women_results = women_results[:5]

    return HttpResponse(
        template.render(
            {"men_results": men_results, "women_results": women_results}, request
        )
    )


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


# TODO: Iterate by year
def results(request):
    template = loader.get_template("results/index.html")

    # Get all results and sort in Python
    men_results = list(Result.objects.filter(registrant__gender="male", year=2025))
    men_results.sort(key=lambda x: (x.dnf, x.time_seconds))
    
    women_results = list(Result.objects.filter(registrant__gender="female", year=2025))
    women_results.sort(key=lambda x: (x.dnf, x.time_seconds))

    return HttpResponse(
        template.render(
            {"men_results": men_results, "women_results": women_results}, request
        )
    )


def about(request):
    template = loader.get_template("about/index.html")
    return HttpResponse(template.render({}, request))
