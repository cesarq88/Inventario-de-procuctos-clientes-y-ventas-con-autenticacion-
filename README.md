# Sistema de Inventario – Django y Docker

Sistema de inventario desarrollado con Django y PostgreSQL, para  la materia de  Práctica Profecionalizante  de  la Tecnicatura en Desarrollo de Software.

Permite gestionar:

- Productos y stock
- Clientes
- Ventas con ítems
- Roles de usuario por grupo (administradores, stock, ventas)
- Generación de comprobante en PDF y gráfico de ventas



####  Alcance funcional(minimo)



- Autenticación con django-allauth (login / logout).
- Vista de inicio (`home`) que muestra mensajes distintos según el grupo:
  - administradores
  - stock
  - ventas
- Menú de navegación que se adapta al usuario autenticado.
- Uso de LoginRequdMixin, PermissionRequedMixin y mixins propios
  para restringir vistas a los grupos correctos.

###  Productos

- Modelo Producto (nombre, descripción, precio, SKU, stock, imagen, etc.).

  - Listado con tabla y botones de acción.
  - Formulario con crispy-forms.
  - Eliminación con plantilla de confirmación amigable.
- Gestión de stock:
  - Formulario de movimiento  (`movimiento_form.html`) para ajustar
    la cantidad disponible.
  - Vista protegida para que sólo usuarios con permisos de stock o
    administradores puedan modificar stock.
- Vista de productos con stock bajo (acceso desde el botón “Stock Bajo”).

###  Clientes

- Modelo Cliente:
  - nombre, apellido, numero_documento (único),
    email, telefono, direccion.

  - cliente_list.html con búsqueda por nombre, apellido o documento.
  - cliente_form.html con crispy-forms.
  - cliente_detail.htm con ficha del cliente.
- Protección al borrar:
  - Si un cliente tiene ventas asociadas, la vista de borrado captura
    `ProtectedError` y muestra un mensaje explcicando que no se puede borrar
    porque tiene ventas registradas.

Ventas

- Venta (código, cliente, fecha, total).
- Modelo ItemVenta (venta, producto, cantidad, precio unitario, subtotal).
- Alta de venta:
  - Vista de creación que usa un VentaForm y un ItemVentaFormSet.
  - Se utiliza django-crispy-forms para maquetar el form y el formset.
  - Se calcula el subtotal de cada ítem y el total de la venta.
  - Se descuenta stock de los productos involucrados.
  - La lógica de guardado se hace dentro de una transacción para garantizar
    consistencia entre venta, items y stock.
- Listado de ventas:
  - `venta_list.html` muestra tabla con codigo, cliente, fecha y total.
  - Campo de búsqueda por código o cliente.
  - Gráfico de “Ventas por día” usando Chart.js (chart_labels y
    chart_data provistos desde la vista).
- Detalle de venta:
  - venta_detail.html muestra cabecera (código, cliente, fecha, total) y
    tabla de ítems (producto, cantidad, precio, subtotal).
  - Botón para descargar comprobante en PDF.
- Comprobante en PDF:
  - Plantilla venta_pdf.html pensada para xhtml2pdf, con todos los datos
    de la venta e ítems, formateado como comprobante.



## Tecnología

-
  - Python 
  - Django
  - django-allauth
  - django-crispy-forms + crispy-bootstrap4
  - xhtml2pdf (genersción de comprobantes en PDF)
  - PostgreSQL 15 (en Docker)
  - Bootstrap 4
  - Chart.js
  - Docker y Docker Compose


## Estructura del proyecto

En la carpeta raíz del proyecto (inventario/):


inventario/
   clientes/          # App de clientes (modelos, vistas, forms, urls)
   inventario/        # Configuración del proyecto (settings, urls)
   media/             # Archivos subidos (imágenes de productos, etc.)
   productos/         # App de productos y stock
   static/            # Archivos estáticos 
   templates/         # Twemplates base y/o compartidos (home, etc.)
   ventas/            # App de ventas e ítems de venta
   .dockerignore
   .env               # Variables de entorno 
  .gitignore
   backup.json        # Datos de ejemplo (dump de la BD)
   db.sqlite3         # Base local alternativa (para desarrollo sin Docker)
   docker-compose.yml
   Dockerfile
manage.py
 requirements.txt
