from django.http import HttpResponse
from django.template import loader
from main_site.models import Result, Registrant
from django.shortcuts import redirect
from django.core.exceptions import ValidationError


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
    context = {"errors": {}}

    if request.method == "POST":
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

            return redirect("success")

        except ValidationError as e:
            # Handle validation errors
            context["errors"] = e.message_dict
            # Preserve the submitted data
            context["form_data"] = request.POST

            # TODO: Don't raise validation error, instead render the form with errors
            raise ValidationError(e)

        except Exception as e:
            print("Exception: ", e)

    return HttpResponse(template.render(context, request))


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


def about(request):
    template = loader.get_template("about/index.html")
    return HttpResponse(template.render({}, request))
