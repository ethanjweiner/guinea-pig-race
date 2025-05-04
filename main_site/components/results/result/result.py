from django_components import Component, register
from main_site.models import Result as ResultModel

PLACE_TO_COLOR = {
    1: "gold",
    2: "silver",
    3: "bronze",
}


@register("result")
class Result(Component):
    template_file = "result.html"

    def get_context_data(self, result: ResultModel):
        color = PLACE_TO_COLOR.get(result.overall_place, None)

        return {
            "place": result.overall_place,
            "name": result.registrant.first_name + " " + result.registrant.last_name,
            "time": result.time,
            "dnf": result.dnf,
            "color": color,
        }
