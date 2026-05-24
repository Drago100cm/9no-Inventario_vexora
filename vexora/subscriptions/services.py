from django.utils import timezone

def subscription_is_active(company):

    try:

        subscription = company.subscription

        if not subscription.active:
            return False

        if subscription.end_date < timezone.now().date():
            return False

        return True

    except:
        return False
    
def can_add_users(company):

    subscription = company.subscription

    current_users = company.customuser_set.count()

    return current_users < subscription.plan.max_users

def can_add_products(company):

    subscription = company.subscription

    current_products = company.product_set.count()

    return current_products < subscription.plan.max_products