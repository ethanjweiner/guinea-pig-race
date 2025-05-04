from django_components import Component, register


@register("nav_item")
class MobileNavItem(Component):
    template_file = "nav_item.html"

    def get_context_data(self, label: str, url: str, icon: str):
        path = self.request.path[1:]
        is_active = path.startswith(url) or (url == "home" and path == "")

        return {
            "is_active": is_active,
            "label": label,
            "url": url,
            "icon": icon,
        }
