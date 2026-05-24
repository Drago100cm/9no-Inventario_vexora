from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

from vexora.models import (
    Company,
    Subscription,
    Plan,
    SiteConfiguration
)


@receiver(post_save, sender=Company)
def create_company_setup(sender, instance, created, **kwargs):

    if created:

        # =========================
        # Crear configuración inicial
        # =========================

        SiteConfiguration.objects.create(
            company=instance
        )

        # =========================
        # Obtener plan trial
        # =========================

        trial_plan = Plan.objects.filter(
            active=True
        ).first()

        # =========================
        # Crear suscripción
        # =========================

        if trial_plan:

            Subscription.objects.create(
                company=instance,
                plan=trial_plan,
                status='active',
                start_date=timezone.now().date(),
                end_date=timezone.now().date() + timedelta(days=14),
                trial=True,
                active=True
            )