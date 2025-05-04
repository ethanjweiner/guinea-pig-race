from django.http import HttpResponse
from django.template import loader
from main_site.models import Result
from django.shortcuts import redirect


def index(request):
    template = loader.get_template("home/index.html")

    men_results = Result.objects.filter(registrant__gender="male").order_by(
        "dnf", "overall_place"
    )[:5]
    women_results = Result.objects.filter(registrant__gender="female").order_by(
        "dnf", "overall_place"
    )[:5]

    return HttpResponse(
        template.render(
            {"men_results": men_results, "women_results": women_results}, request
        )
    )


def home(_):
    return redirect("index")


def register(request):
    template = loader.get_template("register/index.html")
    return HttpResponse(template.render({}, request))


# TODO: Iterate by year
def results(request):
    template = loader.get_template("results/index.html")

    men_results = Result.objects.filter(registrant__gender="male").order_by(
        "dnf", "overall_place"
    )
    women_results = Result.objects.filter(registrant__gender="female").order_by(
        "dnf", "overall_place"
    )

    return HttpResponse(
        template.render(
            {"men_results": men_results, "women_results": women_results}, request
        )
    )
