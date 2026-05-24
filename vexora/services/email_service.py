from django.core.mail import send_mail

from django.conf import settings


def send_welcome_email(user):

    send_mail(

        subject='Bienvenido a Vexora 🚀',

        message=(
            f'Hola {user.first_name}, '
            'tu cuenta fue creada correctamente.'
        ),

        from_email=settings.DEFAULT_FROM_EMAIL,

        recipient_list=[user.email],

        fail_silently=False

    )