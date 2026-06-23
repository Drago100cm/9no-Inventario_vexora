from django.utils import timezone

def subscription_is_active(user):
    try:
        subscription = user.subscription

        if not subscription.active:
            return False

        if subscription.end_date < timezone.now().date():
            return False

        return True

    except AttributeError:
        return False

def can_add_users(user):
    subscription = user.subscription
    return subscription is not None and subscription.active and subscription.plan is not None

def can_add_products(user):
    subscription = user.subscription
    return subscription is not None and subscription.active and subscription.plan is not None
