from django import forms
from django.core.exceptions import ValidationError
from .models import Producto, MovimientoStock
from crispy_forms.layout import Layout, Row, Column, Submit, Reset, ButtonHolder, Field, Div, HTML
from crispy_forms.bootstrap import AppendedText, PrependedText, FormActions
from .crispy import BaseFormHelper
from crispy_forms.helper import FormHelper


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["sku","nombre", "descripcion", "precio", "stock", "stock_minimo", "imagen"]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
             "stock_minimo": "Stock Minimo (alerta)",
        }

        help_texts = {
            "stock_minimo": "Se mostrará una alerta cuando el stock esté por debajo de ese valor"
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = BaseFormHelper()
    
        self.helper.layout = Layout(
            Field("nombre"),
            Field("descripcion"),
            PrependedText("precio", "$", placeholder="0.00"),
            Field("stock"),
            Field("stock_minimo"),
            Field("imagen"),
            ButtonHolder(
                Submit("submit", "Guardar", css_class="btn btn-success"),
                Reset("reset", "Limpiar", css_class="btn btn-outline-secondary"),
                HTML('<a href="{% url "productos:producto_list" %}" class="btn btn-secondary">Cancelar</a>')

            )
        )
     
    def clean_precio(self):
        precio = self.cleaned_data.get("precio")
        if precio and precio <= 0:
           raise ValidationError("El precio debe ser mayor a cero")
        return precio
    
    def clean_stock(self):
        stock = self.cleaned_data.get("stock")
        if stock and stock < 0:
           raise ValidationError("No puede haber valor negativo de stock")
        return stock
    
    def clean_stock_minimo(self):
        stock_minimo = self.cleaned_data.get("stock_minimo")
        if stock_minimo and stock_minimo < 0:
          raise ValidationError("No puede haber valor negativo de stock minimo")
        return stock_minimo
   #Estos tres son para producto

   #Ahora formulario de movimiento de stock



class MovimientoStockForm(forms.ModelForm):
    class Meta:
        model = MovimientoStock
        fields = ["tipo", "cantidad", "motivo"]
        widgets = {
            "motivo": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "tipo": "Tipo de movimiento",
            "cantidad": "Cantidad",
            "motivo": "Motivo (opcional)",
        }
        
    def __init__(self, *args, **kwargs):
       self.producto = kwargs.pop("producto", None)
       super().__init__(*args, **kwargs)
       self.helper = BaseFormHelper()

       stock_info = ""
       if self.producto:
           stock_info = f"""
           <div class="alert alert-info">
               <strong>Producto:</strong> {self.producto.nombre}<br>
               <strong>Stock actual:</strong> {self.producto.stock}
           </div>
           """
            
           self.helper.layout = Layout(
                HTML(stock_info),
                Field("tipo"),
                Field("cantidad"),
                Field("motivo"),
                ButtonHolder(
                    Submit("submit", "Registrar movimiento", 
                    css_class="btn btn-success"),
                    HTML('<a href="{{ request.META.HTTP_REFERER }}" ' \
                    'class="btn btn-secondary">Cancelar</a>')

                )
            )
    def clean_cantidad(self):
        cantidad = self.cleaned_data.get("cantidad")
        if cantidad <= 0:
           raise ValidationError("La cantidad debe ser mayor a cero")
            
        if self.producto and self.cleaned_data.get("tipo") == "salida":
           if cantidad > self.producto.stock:
               raise ValidationError(
                  f"No hay suficiente stock. Disponible: {self.producto.stock}"
    )
        return cantidad
        

class AjusteStockForm(forms.Form):
    """
    Formulario genérico para ajustar el stock de un producto.
    No se basa en un modelo, sino en una acción.
    """
    cantidad = forms.IntegerField(
        min_value=0,
        label="Nuevo Stock",
        help_text="Establece el nuevo valor de stock para el producto."
    )
    motivo = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
        label="Motivo del Ajuste",
        help_text="Explica por qué estás ajustando el stock (opcional)."
    )

    def __init__(self, *args, **kwargs):
        self.producto = kwargs.pop('producto', None)
        super().__init__(*args, **kwargs)
        self.helper = BaseFormHelper()
        
        # Mostramos el stock actual para contexto del usuario
        stock_info = ""
        if self.producto:
            stock_info = f"""
            <div class="alert alert-info">
                <strong>Producto:</strong> {self.producto.nombre}<br>
                <strong>Stock actual:</strong> {self.producto.stock}
            </div>
            """
            # Establecemos el valor inicial del campo 'cantidad' al stock actual
            self.fields['cantidad'].initial = self.producto.stock
        
        self.helper.layout = Layout(
            HTML(stock_info),
            Field('cantidad'),
            Field('motivo'),
            ButtonHolder(
                Submit('submit', 'Ajustar Stock', css_class='btn btn-warning'),
                HTML('<a href="{{ request.META.HTTP_REFERER }}" class="btn btn-secondary">Cancelar</a>')
            )
        )
class FiltroFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'get'  # Los formularios de filtro usan el método GET
        self.form_class = 'form-inline'  # Clase de Bootstrap para formularios en línea
        # Plantilla específica para campos en línea, muy útil para este tipo de formularios
        self.field_template = 'bootstrap4/layout/inline_field.html'
     
class FiltroProductosForm(forms.Form):
    """
    Formulario para aplicar filtros a la lista de productos.
    No se basa en un modelo.
    """
    TIPO_FILTRO_CHOICES = [
        ('', 'Todos los productos'),
        ('stock_bajo', 'Solo stock bajo'),
        ('stock_ok', 'Stock normal'),
    ]
    
    filtro = forms.ChoiceField(
        choices=TIPO_FILTRO_CHOICES,
        required=False,
        label="Filtrar por"
    )
    buscar = forms.CharField(
        required=False,
        label="Buscar",
        widget=forms.TextInput(attrs={'placeholder': 'Nombre, descripción...'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Usamos el helper de filtro específico
        self.helper = FiltroFormHelper()
        
        # Definimos un layout más complejo con Row y Column
        self.helper.layout = Layout(
            Row(
                Column('filtro', css_class='form-group col-md-4 mb-0'),
                Column('buscar', css_class='form-group col-md-4 mb-0'),
                Column(
                    ButtonHolder(
                        Submit('submit', 'Filtrar', css_class='btn btn-primary'),
                        HTML('<a href="." class="btn btn-secondary">Limpiar</a>')
                    ),
                    css_class='form-group col-md-4 mb-0'
                ),
                # Alineamos los elementos verticalmente al centro
                css_class='form-row align-items-center'
            )
        )