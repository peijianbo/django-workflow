from django.apps import AppConfig


class WorkflowConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'workflow.apps.workflow'
    verbose_name = '工作流'

    def ready(self):
        super().ready()
        from . import signals
