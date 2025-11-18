from django.shortcuts import render, redirect, get_object_or_404
# clientes/views.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models.deletion import ProtectedError
from django.db.models import ProtectedError
from .models import Cliente
from .forms import ClienteForm

class VentasPermissionMixin(UserPassesTestMixin):
   # esto es para acceder solo a usuarioso de grupo ventas , usuarios del grupo administradores o susperusuarios
    def test_func(self):
        user = self.request.user
        return (
            user.is_superuser
            or user.groups.filter(name__in=["ventas", "administradores"]).exists()
        )
    def handle_no_permission(self):
        # Si está logueado pero no tiene permisos, te dice qeu no tenes permisos
        if self.request.user.is_authenticated:
            messages.error(
                self.request,
                "Sos de stock, no tenés permiso para acceder a Ventas/Clientes...."
            )
            return redirect("home")

        # Si no está logueado, se acciona el LoginRequiredMixin
        return super().handle_no_permission()


class ClienteListView(LoginRequiredMixin, VentasPermissionMixin,ListView):
    model = Cliente
    template_name = "clientes/cliente_list.html"
    context_object_name = "clientes"
    login_url = 'account_login'
    paginate_by = 5





    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(nombre__icontains=q)
 
        return queryset.order_by('nombre')

class ClienteDetailView(LoginRequiredMixin, VentasPermissionMixin,DetailView):
    model = Cliente
    template_name = "clientes/cliente_detail.html"
    context_object_name = "cliente"
    login_url = 'account_login'


class ClienteCreateView(LoginRequiredMixin, VentasPermissionMixin,CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "clientes/cliente_form.html"
    success_url = reverse_lazy("clientes:cliente_list")
    login_url = 'account_login'

    def form_valid(self, form):
        messages.success(self.request, "Cliente creado exitosamente")
        return super().form_valid(form)


class ClienteUpdateView(LoginRequiredMixin, VentasPermissionMixin,UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "clientes/cliente_form.html"
    success_url = reverse_lazy("clientes:cliente_list")
    login_url = 'account_login'

    def form_valid(self, form):
        messages.success(self.request, "Cliente actualizado exitosamente")
        return super().form_valid(form)


class ClienteDeleteView(LoginRequiredMixin, VentasPermissionMixin, DeleteView):
    model = Cliente
    template_name = "clientes/cliente_confirm_delete.html"
    success_url = reverse_lazy("clientes:cliente_list")
    login_url = 'account_login'

    def post(self, request, *args, **kwargs):
        # Obtenemos el cliente que se quiere borrar
        self.object = self.get_object()

        try:
            # Intentamos borrar normalmente
            response = super().post(request, *args, **kwargs)
            messages.success(request, "Cliente eliminado exitosamente")
            return response

        except ProtectedError:
            # Si hay ventas asociadas, Django lanza ProtectedError
            messages.error(
                request,
                "No se puede eliminar el cliente porque tiene ventas registradas."
            )
            # Volvemos al detalle del cliente (podés mandarlo a la lista si preferís)
            return redirect("clientes:cliente_detail", pk=self.object.pk)
