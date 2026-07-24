from django import forms


class HeatBuilderForm(forms.Form):
    regular_heat_size = forms.IntegerField(
        label="Regular co-ed heat target size",
        min_value=1,
        initial=8,
        help_text="Remaining runners are split into this many-per-heat target as evenly as possible.",
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
