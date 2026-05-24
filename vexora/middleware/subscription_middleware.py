from django.http import JsonResponse

from vexora.subscriptions.services import (
    subscription_is_active
)


EXCLUDED_PATHS = [
    '/login/',
    '/Registro/',
    '/register/',
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

        # =========================
        # Ignorar rutas públicas
        # =========================

        if path.startswith(tuple(EXCLUDED_PATHS)):
            return self.get_response(request)

        if request.user.is_authenticated:

            company = request.user.company

            if company:

                active = subscription_is_active(
                    company
                )

                if not active:

                    return JsonResponse({
                        "error": "Tu suscripción expiró"
                    }, status=403)

        return self.get_response(request)