from django.db import models
from django.db import models
from django.db import models
import os
import uuid
from django.core.exceptions import ValidationError
from PIL import Image
from django.utils import timezone

from django.db import models

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    numero_documento = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número de documento"
    )
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    direccion = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.apellido}, {self.nombre} ({self.numero_documento})"

# Create your models here.
