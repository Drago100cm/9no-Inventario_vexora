from vexora.models import Product, Branch


def get_subscription(user):
    """
    Obtiene la suscripción activa del usuario.
    """
    subscription = getattr(user, "subscription", None)

    if not subscription:
        return None

    if not subscription.active:
        return None

    return subscription


def can_add_user(user):
    """
    Verifica si puede agregar más usuarios.
    """
    subscription = get_subscription(user)

    if not subscription:
        return False

    company = getattr(user, "company", None)

    if not company:
        return False

    current_users = company.members.count()

    return current_users < subscription.plan.max_users


def can_add_product(user):
    """
    Verifica si puede agregar más productos.
    """
    subscription = get_subscription(user)

    if not subscription:
        return False

    company = getattr(user, "company", None)

    if not company:
        return False

    current_products = Product.objects.filter(
        company=company
    ).count()

    return current_products < subscription.plan.max_products


def can_add_branch(user):
    """
    Verifica si puede agregar más sucursales.
    """
    subscription = get_subscription(user)

    if not subscription:
        return False

    company = getattr(user, "company", None)

    if not company:
        return False

    current_branches = Branch.objects.filter(
        company=company
    ).count()

    return current_branches < subscription.plan.max_branches


def has_custom_domain(user):
    """
    Verifica si el plan permite dominio personalizado.
    """
    subscription = get_subscription(user)

    if not subscription:
        return False

    return subscription.plan.custom_domain


def has_priority_support(user):
    """
    Verifica si el plan tiene soporte prioritario.
    """
    subscription = get_subscription(user)

    if not subscription:
        return False

    return subscription.plan.priority_support


def get_plan_limits(user):
    """
    Retorna todos los límites del plan.
    """
    subscription = get_subscription(user)

    if not subscription:
        return None

    return {
        "max_users": subscription.plan.max_users,
        "max_products": subscription.plan.max_products,
        "max_branches": subscription.plan.max_branches,
        "custom_domain": subscription.plan.custom_domain,
        "priority_support": subscription.plan.priority_support,
    }