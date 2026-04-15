from django.apps import AppConfig

class EventsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'events'
    # THIS RENAMES THE HEADER IN JAZZMIN!
    verbose_name = 'NGO Management'