from django.http import HttpResponse
from django.template import loader
from main_site.models import Result
from django.shortcuts import redirect


def index(request):
    template = loader.get_template("home/index.html")
    context = {
        "results": [
            Result(place=1, name="Ethan Weiner", time="4:29"),
            Result(place=2, name="Ethan Weiner", time="4:29"),
            Result(place=3, name="Ethan Weiner", time="4:29"),
            Result(place=4, name="Ethan Weiner", time="4:29"),
            Result(place=5, name="Ethan Weiner", time="4:29"),
        ]
    }
    return HttpResponse(template.render(context, request))


def home(_):
    return redirect("index")


def register(request):
    template = loader.get_template("register/index.html")
    return HttpResponse(template.render({}, request))
