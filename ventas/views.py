from django.shortcuts import render, redirect
from django.views import View
from django.db import transaction
from django.contrib import messages

from .models import Venta, ItemVenta
from .forms import VentaForm, ItemVentaFormSet
from productos.models import Producto
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class VentasPermissionMixin(UserPassesTestMixin):
   
    def test_func(self):
        user = self.request.user
        return (
            user.is_superuser
            or user.groups.filter(name__in=["ventas", "administradores"]).exists()
        )


class VentaListView(LoginRequiredMixin, VentasPermissionMixin,ListView):
    model = Venta
    template_name = "ventas/venta_list.html"
    context_object_name = "ventas"
    ordering = ["-fecha"]  # las más nuevas primero, orden decendente
    login_url = 'account_login'

class VentaDetailView(LoginRequiredMixin, VentasPermissionMixin,DetailView):
    model = Venta
    template_name = "ventas/venta_detail.html"
    context_object_name = "venta"
    login_url = 'account_login'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["items"] = self.object.items.all()
        return context

class VentaCreateView(LoginRequiredMixin, VentasPermissionMixin,View):
    template_name = "ventas/venta_form.html"
    login_url = 'account_login'
    def get(self, request):
        venta_form = VentaForm()
        items_formset = ItemVentaFormSet()
        return render(request, self.template_name, {
            "venta_form": venta_form,
            "items_formset": items_formset,
        })

    @transaction.atomic
    def post(self, request):
        venta_form = VentaForm(request.POST)
        items_formset = ItemVentaFormSet(request.POST)

        if venta_form.is_valid() and items_formset.is_valid():
            # Creamos la venta, pero todavía sin total
            venta = venta_form.save(commit=False)
            venta.total = 0
            venta.save()

            total = 0

            for form in items_formset:
                if form.cleaned_data and not form.cleaned_data.get("DELETE", False):
                    producto = form.cleaned_data["producto"]
                    cantidad = form.cleaned_data["cantidad"]
                    precio_unitario = form.cleaned_data["precio_unitario"]

                    # Calculamos subtotal de la línea
                    subtotal = cantidad * precio_unitario

                    # Creamos el item
                    ItemVenta.objects.create(
                        venta=venta,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=precio_unitario,
                        subtotal=subtotal,
                    )

                    # Descontamos stock del producto
                    if producto.stock >= cantidad:
                        producto.stock -= cantidad
                        producto.save()
                    else:
                        # Si no hay stock suficiente, revertimos toda la transacción
                        raise ValueError(f"No hay stock suficiente para {producto.nombre}")

                    total += subtotal

            # Guardamos el total de la venta
            venta.total = total
            venta.save()

            messages.success(request, "Venta registrada exitosamente")
            # Más adelante podemos cambiar esto a 'ventas:venta_list'
            return redirect("ventas:venta_detail", pk=venta.pk)


        # Si algo falla, volvemos a mostrar el formulario con errores
        return render(request, self.template_name, {
            "venta_form": venta_form,
            "items_formset": items_formset,
        })


# Create your views here.
