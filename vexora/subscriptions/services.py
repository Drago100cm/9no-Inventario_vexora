from django.utils import timezone


def get_subscription(company):
    """
    Obtiene la suscripción de una empresa.
    """
    if company is None:
        return None

    try:
        return company.subscription
    except AttributeError:
        return None


def subscription_is_active(company):
    """
    Verifica si la suscripción de la empresa está activa.
    """
    subscription = get_subscription(company)

    if subscription is None:
        return False

    if not subscription.active:
        return False

    if subscription.status != "active":
        return False

    if subscription.end_date < timezone.now().date():
        return False

    return True


def can_add_users(company):
    """
    Verifica si la empresa puede agregar más usuarios.
    """
    subscription = get_subscription(company)

    if subscription is None:
        return False

    if not subscription_is_active(company):
        return False

    return company.members.count() < subscription.plan.max_users


def can_add_products(company):
    """
    Verifica si la empresa puede agregar más productos.
    """
    subscription = get_subscription(company)

    if subscription is None:
        return False

    if not subscription_is_active(company):
        return False

    return company.products.count() < subscription.plan.max_products