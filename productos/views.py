from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Q, F
from django.utils import timezone
from .models import Producto, MovimientoStock
from .forms import ProductoForm, MovimientoStockForm, AjusteStockForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class StockPermissionMixin(UserPassesTestMixin):
   # Permite acceder solo a: usuarios del grupo 'stock' ,usuarios del grupo 'administradores'  o superusuarios


    def test_func(self):
        user = self.request.user
        return (
            user.is_superuser
            or user.groups.filter(name__in=["stock", "administradores"]).exists()
        )




class ProductoListView(LoginRequiredMixin, StockPermissionMixin,ListView):
    model = Producto
    template_name = "productos/producto_list.html"
    context_object_name = "productos"
    login_url = 'account_login'
    
    def get_queryset(self):
        queryset = super().get_queryset()

        stock_bajo = self.request.GET.get('stock_bajo')
        if stock_bajo:
            queryset = queryset.filter(stock__lt=F("stock_minimo"))

        return queryset.order_by('nombre')
    
    def get_context_data(self, **kwargs):
        context =super().get_context_data(**kwargs)
        context['stock_bajo']=self.request.GET.get('stock_bajo')
    
        return context

class ProductoDetailView(LoginRequiredMixin, StockPermissionMixin,DetailView):
    model = Producto
    template_name = "productos/producto_detail.html"
    context_object_name = "producto"
    login_url = 'account_login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["movimientos"] = self.object.movimientos.all()[:10]
        context["form_ajuste"] = AjusteStockForm
        return context
    
class ProductoCreateView(LoginRequiredMixin, StockPermissionMixin,CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = "productos/producto_form.html"
    success_url = reverse_lazy("productos:producto_list")
    login_url = 'account_login'

    def form_valid(self, form):
        response = super().form_valid(form)

        if form.cleaned_data["stock"] > 0:
            MovimientoStock.objects.create(
                producto=self.object,
                tipo="entrada",
                cantidad=form.cleaned_data["stock"],
                motivo="Stock inicial",
                fecha=timezone.now(),
                usuario=self.request.user.username if self.request.user.is_authenticated else "Sistema"
            )

        messages.success(self.request, "Producto creado exitosamente")

        return response

class ProductoUpdateView(LoginRequiredMixin, StockPermissionMixin,UpdateView):
    model = Producto
    template_name = "productos/producto_form.html"
    form_class = ProductoForm
    success_url = reverse_lazy("productos:producto_list")
    login_url = 'account_login'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Producto actualizado exitosamente")
        return response


class ProductoDeleteView(LoginRequiredMixin, StockPermissionMixin,DeleteView):
    model = Producto
    template_name = "productos/producto_confirm_delete.html"
    success_url = reverse_lazy("productos:producto_list")
    login_url = 'account_login'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Producto eliminado exitosamente")
        return super().delete(request, *args, **kwargs)


class MovimientoStockCreateView(LoginRequiredMixin, StockPermissionMixin,CreateView):
    model = MovimientoStock
    template_name = "productos/movimiento_form.html"
    form_class = MovimientoStockForm
    login_url = 'account_login'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["producto"] = get_object_or_404(Producto, pk=self.kwargs["pk"])
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["producto"] = get_object_or_404(Producto, pk=self.kwargs["pk"])
        return context 

    def form_valid(self, form):
        movimiento = form.save(commit=False)
        movimiento.producto = get_object_or_404(Producto, pk=self.kwargs["pk"])
        movimiento.usuario= self.request.user.username if self.request.user.is_authenticated else "Sistema"

        
        if movimiento.tipo == "entrada":
            movimiento.producto.stock += movimiento.cantidad
        elif movimiento.tipo == "salida":
           if movimiento.producto.stock >= movimiento.cantidad:
               movimiento.producto.stock -= movimiento.cantidad
           else:
               form.add_error("cantidad", "No hay stock suficiente")
               return self.form_invalid(form)

        movimiento.producto.save()
        movimiento.save()

        messages.success(self.request, "Movimiento de stock registrado exitosamente")
        return redirect("productos:producto_detail", pk=movimiento.producto.pk)

class AjusteStockView(LoginRequiredMixin, StockPermissionMixin,FormView):
    form_class = AjusteStockForm
    template_name = "productos/ajuste_stock_form.html"
    login_url = 'account_login'


    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["producto"] = get_object_or_404(Producto, pk=self.kwargs["pk"])
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["producto"] = get_object_or_404(Producto, pk=self.kwargs["pk"])
        return context 
    
    def form_valid(self, form):
        producto = get_object_or_404(Producto, pk=self.kwargs["pk"])
        nueva_cantidad = form.cleaned_data["cantidad"]
        motivo = form.cleaned_data["motivo"] or "Ajuste de stock"

        diferencia = nueva_cantidad - producto.stock

        if diferencia != 0:
            tipo = "entrada" if diferencia > 0 else "salida"
            MovimientoStock.objects.create(
                producto=producto,
                tipo=tipo,
                cantidad=abs(diferencia),
                motivo=motivo,
                fecha=timezone.now(),
                usuario=self.request.user.username if self.request.user.is_authenticated else "Sistema"
            )
             
            producto.stock = nueva_cantidad
            producto.save()

            messages.success(self.request, "Stock actualizado exitosamente")
        else:
             messages.info(self.request, "El stock no ha cambiado")

        return redirect("productos:producto_detail", pk=producto.pk)

class StockBajoListView(LoginRequiredMixin, StockPermissionMixin,ListView):
    model = Producto
    template_name = "productos/stock_bajo_list.html"
    context_object_name = "productos"
    login_url = 'account_login'

    def get_queryset(self):
        return Producto.objects.filter(stock__lt=F("stock_minimo")).order_by("stock")
