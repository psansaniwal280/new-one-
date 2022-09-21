from django.contrib import admin
from .models import *

# admin.site.register(Post)
# admin.site.register(PostLike)
# admin.site.register(PostVenue)
# admin.site.register(User)
# admin.site.register(Venue)
# admin.site.register(VenueExternal)
# admin.site.register(VenueInternal)

from django.apps import apps
app_config = apps.get_app_config('app')  # Replace your_app_name it is just a placeholder
models = app_config.get_models()


for model in models:
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass
