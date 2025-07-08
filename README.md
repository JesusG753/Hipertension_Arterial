# Hipertension_Arterial
Este modelo de machine learning se ha realizado con el fin de prevenir la hipertension arterial en adultos tomando en cuenta diferentes datos fisiologicos y médicos.

# Machine Learning
La carpeta ML contiene 2 archivos .ipynb, Python_Balanceo_Dataset, en donde se toma el archivo csv limpio y se aplica la técnica Smoke-Tomek para su balanceo, y HTA con RandomForest_Optimizado_API, donde se encuentra la significancia de los atributos, se construye el modelo y se ejecuta el API.

# Formulario
En la carpeta Formulario se encuentra la aplicación hecha con Django, llamado hipertension_web, el cual se ejecuta con el API ya funcionando, mediante consola, llamando desde /Formulario/hipertension_web con el comando python manage.py runserver

# Importante
Para la implementación de la opción "enviar reporte por correo" del formulario funcione, requiere un correo y una contraseña de aplicación asociada en /Formulario/hipertension_web/hipertension_web/settings.py en las líneas EMAIL_HOST_USER y EMAIL_HOST_PASSWORD respectivamente.
Para el uso del formulario de manera remota requiere un servicio web como AWS, también puede usarse con un servicio de prueba como Ngrok, el URL que provee el servicio debe colocarse en /Formulario/hipertension_web/hipertension_web/settings.py, en la línea CSRF_TRUSTED_ORIGINS
