
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "home.html"
    login_url = "account_login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context["es_admin"] = (
            user.is_superuser
            or user.groups.filter(name="administradores").exists()
        )
        context["es_stock"] = user.groups.filter(name="stock").exists()
        context["es_ventas"] = user.groups.filter(name="ventas").exists()

        return context
