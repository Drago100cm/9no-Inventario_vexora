from .models import SiteConfiguration

def site_config(request):

    config = None

    if request.user.is_authenticated:

        if request.user.company:

            config, created = SiteConfiguration.objects.get_or_create(
                company=request.user.company
            )

    return {
        'site_config': config
    }