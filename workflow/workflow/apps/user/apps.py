from django.apps import AppConfig


class UserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'workflow.apps.user'
    verbose_name = '用户'

    def ready(self):
        super().ready()
