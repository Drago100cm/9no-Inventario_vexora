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

        if path.startswith(tuple(EXCLUDED_PATHS)):
            return self.get_response(request)

        if not request.user.is_authenticated:
            return self.get_response(request)

        company = request.user.company

        if company is None:
            return JsonResponse(
                {"error": "No perteneces a ninguna empresa."},
                status=403
            )

        if not subscription_is_active(company):
            return JsonResponse(
                {
                    "error": "La suscripción de tu empresa expiró o no está activa."
                },
                status=403
            )

        return self.get_response(request)