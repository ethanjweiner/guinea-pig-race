from django import forms


class HeatBuilderForm(forms.Form):
    largest_heat_size = forms.IntegerField(
        label="Largest co-ed heat size",
        min_value=1,
        initial=8,
        help_text="The slowest co-ed heat starts at this size; faster co-ed heats get progressively smaller.",
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

        if largest_heat_size is None:
            return cleaned_data

        if (
            men_championship_size is not None
            and men_championship_size > largest_heat_size
        ):
            self.add_error(
                "men_championship_size",
                "Men's championship heat size must be no larger than the largest co-ed heat size.",
            )

        if (
            women_championship_size is not None
            and women_championship_size > largest_heat_size
        ):
            self.add_error(
                "women_championship_size",
                "Women's championship heat size must be no larger than the largest co-ed heat size.",
            )

        return cleaned_data
