from .models import SiteConfiguration

def site_config(request):

    config = None

    if request.user.is_authenticated:
        company = getattr(request.user, 'company', None)

        if company:
            config, created = SiteConfiguration.objects.get_or_create(
                company=company
            )

    return {
        'site_config': config
    }