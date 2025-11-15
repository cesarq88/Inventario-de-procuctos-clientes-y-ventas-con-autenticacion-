from django.urls import path
from .views import VentaCreateView, VentaListView, VentaDetailView

app_name = "ventas"

urlpatterns = [
    path("", VentaListView.as_view(), name="venta_list"),
    path("nueva/", VentaCreateView.as_view(), name="venta_create"),
    path("<int:pk>/", VentaDetailView.as_view(), name="venta_detail"),
]
