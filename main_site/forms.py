from math import ceil

from django import forms

from main_site.heats import COED_CHAMPIONSHIP_SIZE_MULTIPLIER


class HeatBuilderForm(forms.Form):
    coed_heat_count = forms.IntegerField(
        label="Number of co-ed heats",
        min_value=1,
        initial=4,
        help_text="How many slow-to-fast co-ed heats to build before the championship heats.",
    )
    largest_heat_size = forms.IntegerField(
        label="Largest co-ed heat size",
        min_value=1,
        initial=12,
        help_text=(
            "The slowest co-ed heat starts at this size; every co-ed heat must "
            "be at least 30% larger than the largest championship heat."
        ),
    )
    men_championship_size = forms.IntegerField(
        label="Men's championship heat size",
        min_value=1,
        initial=8,
        help_text="Fastest male registrants by seed time.",
    )
    women_championship_size = forms.IntegerField(
        label="Women's championship heat size",
        min_value=1,
        initial=8,
        help_text="Fastest female registrants by seed time.",
    )

    def clean(self):
        cleaned_data = super().clean()
        largest_heat_size = cleaned_data.get("largest_heat_size")
        men_championship_size = cleaned_data.get("men_championship_size")
        women_championship_size = cleaned_data.get("women_championship_size")

        if (
            largest_heat_size is None
            or men_championship_size is None
            or women_championship_size is None
        ):
            return cleaned_data

        minimum_coed_heat_size = ceil(
            max(men_championship_size, women_championship_size)
            * COED_CHAMPIONSHIP_SIZE_MULTIPLIER
        )

        if largest_heat_size < minimum_coed_heat_size:
            self.add_error(
                "largest_heat_size",
                "Largest co-ed heat size must be at least 30% larger than the largest championship heat size.",
            )

        if men_championship_size > largest_heat_size:
            self.add_error(
                "men_championship_size",
                "Men's championship heat size must be no larger than the largest co-ed heat size.",
            )

        if women_championship_size > largest_heat_size:
            self.add_error(
                "women_championship_size",
                "Women's championship heat size must be no larger than the largest co-ed heat size.",
            )

        return cleaned_data
