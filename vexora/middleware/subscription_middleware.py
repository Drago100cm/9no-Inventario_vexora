from django.shortcuts import redirect

from vexora.subscriptions.services import subscription_is_active


# Rutas que cualquier usuario puede abrir
PUBLIC_PATHS = [
    "/",
    "/login/",
    "/Registro/",
    "/register/",
    "/logout/",
]

# Rutas que puede abrir un usuario autenticado que todavía no tiene empresa
NO_COMPANY_PATHS = [
    "/Dashboard/",
    "/company_create/",
    "/companies/",
    "/logout/",
]

# Rutas relacionadas con la contratación de una suscripción
SUBSCRIPTION_PATHS = [
    "/subscription_list/",
    "/subscriptions/choose/",
    "/subscriptions/detail/",
    "/logout/",
]


class SubscriptionMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        path = request.path

        # Dejar pasar archivos estáticos y archivos multimedia
        if path.startswith(("/static/", "/media/")):
            return self.get_response(request)

        # Rutas públicas
        if path in PUBLIC_PATHS:
            return self.get_response(request)

        # Si no inició sesión, dejamos que Django maneje la protección
        if not request.user.is_authenticated:
            return self.get_response(request)

        company = request.user.company

        # Usuario recién registrado sin empresa
        if company is None:

            # Puede entrar al dashboard y a la creación de empresas
            if path in NO_COMPANY_PATHS:
                return self.get_response(request)

            # Para cualquier otra ruta, mandarlo a crear una empresa
            return redirect("vexora:company_create")

        # Si ya tiene empresa, permitirle ver las opciones de suscripción
        if path in SUBSCRIPTION_PATHS:
            return self.get_response(request)

        # Si la empresa no tiene una suscripción activa
        if not subscription_is_active(company):
            return redirect("vexora:subscription_list")

        return self.get_response(request)