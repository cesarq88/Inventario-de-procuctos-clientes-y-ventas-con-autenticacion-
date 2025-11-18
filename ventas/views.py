from django.shortcuts import render, redirect
from django.views import View
from django.db import transaction
from django.contrib import messages
from django.db.models import Q
from django.db.models import Sum         
import json  
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa



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
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(
                self.request,
                "Tampoco aca, acordate,  ni en Ventas y Clientes."
            )
            return redirect('home')
        return super().handle_no_permission()

class VentaListView(LoginRequiredMixin, VentasPermissionMixin,ListView):
    model = Venta
    template_name = "ventas/venta_list.html"
    context_object_name = "ventas"
    ordering = ["-fecha"]  # las más nuevas primero, orden decendente
    login_url = 'account_login'
    paginate_by = 5 

    def get_queryset(self):
        queryset = super().get_queryset()

        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(
                Q(codigo__icontains=q) |          # busca por código de venta
                Q(cliente__nombre__icontains=q) |   # busca por nombre de cliente
                Q(cliente__apellido__icontains=q)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")

            # datos para el gráfico de ventas por día
        ventas_por_dia = (
            Venta.objects
            .values("fecha__date")
            .order_by("fecha__date")
            .annotate(total_dia=Sum("total"))
        )

        labels = []
        data = []

        for v in ventas_por_dia:
            fecha = v["fecha__date"]
            total = v["total_dia"] or 0
            labels.append(fecha.strftime("%d/%m"))   
            data.append(float(total))

        context["chart_labels"] = json.dumps(labels)
        context["chart_data"] = json.dumps(data)

        return context

class VentaDetailView(LoginRequiredMixin, VentasPermissionMixin,DetailView):
    model = Venta
    template_name = "ventas/venta_detail.html"
    context_object_name = "venta"
    login_url = 'account_login'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["items"] = self.object.items.all()
        return context
class VentaPDFView(LoginRequiredMixin, VentasPermissionMixin, DetailView):
    model = Venta
    template_name = "ventas/venta_pdf.html"
    context_object_name = "venta"
    login_url = 'account_login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["items"] = self.object.items.all()
        return context

    def render_to_response(self, context, **response_kwargs):
        # 1) Renderizamos la plantilla a HTML (string)
        html_string = render_to_string(
            self.template_name,
            context,
            request=self.request,
        )

        # 2) Armamos la respuesta HTTP de tipo PDF
        filename = f"venta_{self.object.codigo}.pdf"
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{filename}"'

        
        pisa_status = pisa.CreatePDF(
            html_string,
            dest=response,
        )

        # Si hubo error, devolvemos un mensaje simple
        if pisa_status.err:
            return HttpResponse("Error al generar el PDF de la venta", status=500)

        return response



class VentaCreateView(LoginRequiredMixin, VentasPermissionMixin, View):
    template_name = "ventas/venta_form.html"
    login_url = 'account_login'

    def get(self, request):
        venta_form = VentaForm()
        items_formset = ItemVentaFormSet()
        return render(request, self.template_name, {
            "venta_form": venta_form,
            "items_formset": items_formset,
        })

    def post(self, request):
        venta_form = VentaForm(request.POST)
        items_formset = ItemVentaFormSet(request.POST)

        if not (venta_form.is_valid() and items_formset.is_valid()):
            # Si hay errores normales de form/formset, los mostramos
            return render(request, self.template_name, {
                "venta_form": venta_form,
                "items_formset": items_formset,
            })

        #  validar stock y calcular total (sin guardar nada)
        total = 0

        for form in items_formset:
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False):
                producto = form.cleaned_data["producto"]
                cantidad = form.cleaned_data["cantidad"]
                precio_unitario = form.cleaned_data["precio_unitario"]

                # Verificamos stock antes de tocar la BD
                if producto.stock < cantidad:
                    messages.error(
                        request,
                        f"No hay stock suficiente para {producto.nombre}. "
                        f"Stock disponible: {producto.stock}"
                    )
                    return render(request, self.template_name, {
                        "venta_form": venta_form,
                        "items_formset": items_formset,
                    })

                total += cantidad * precio_unitario

        #  ahora sí guardamos todo dentro de una transacción
        with transaction.atomic():
            # Creamos la venta con el total calculado
            venta = venta_form.save(commit=False)
            venta.total = total
            venta.save()

            # Creamos items y descontamos stock
            for form in items_formset:
                if form.cleaned_data and not form.cleaned_data.get("DELETE", False):
                    producto = form.cleaned_data["producto"]
                    cantidad = form.cleaned_data["cantidad"]
                    precio_unitario = form.cleaned_data["precio_unitario"]
                    subtotal = cantidad * precio_unitario

                    ItemVenta.objects.create(
                        venta=venta,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=precio_unitario,
                        subtotal=subtotal,
                    )

                    producto.stock -= cantidad
                    producto.save()

        messages.success(request, "Venta registrada exitosamente")
        return redirect("ventas:venta_detail", pk=venta.pk)

