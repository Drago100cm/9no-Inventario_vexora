from django.http import JsonResponse

from vexora.subscriptions.services import (
    subscription_is_active
)


EXCLUDED_PATHS = [
    '/login/',
    '/Registro/',
    '/register/',
    '/logout/',
    '/admin/',
    '/users/',
    '/subscription_list/',
    '/subscriptions/choose/',
    '/subscriptions/detail/',
]


class SubscriptionMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        path = request.path

        # Ignorar rutas públicas
        if path.startswith(tuple(EXCLUDED_PATHS)):
            return self.get_response(request)

        # Usuario no autenticado
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Verificar suscripción del usuario
        active = subscription_is_active(request.user)

        if not active:
            return JsonResponse(
                {
                    "error": "Tu suscripción expiró o no está activa"
                },
                status=403
            )

        return self.get_response(request)