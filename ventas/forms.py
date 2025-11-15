from django import forms
from django.forms import inlineformset_factory

from .models import Venta, ItemVenta


class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ["codigo", "cliente"]   # fecha y total se manejan desde el sistema


class ItemVentaForm(forms.ModelForm):
    class Meta:
        model = ItemVenta
        fields = ["producto", "cantidad", "precio_unitario"]
        widgets = {
            "precio_unitario": forms.TextInput(
                attrs={
                    "placeholder": "Ej: 0.53",   # ponermos cualquier numero
                }
            )
        }


# Formset para cargar varios items en una misma venta
ItemVentaFormSet = inlineformset_factory(
    parent_model=Venta,
    model=ItemVenta,
    form=ItemVentaForm,
    extra=3,          # cantidad de filas vacías por defecto
    can_delete=True   # permitir marcar items para borrar en edición
)
