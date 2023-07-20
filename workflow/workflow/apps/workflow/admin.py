from django.contrib import admin

# Register your models here.

from .models import *

admin.site.register(Component)
admin.site.register(FormField)
admin.site.register(Workflow)
admin.site.register(WorkflowChain)
admin.site.register(WorkflowNode)
admin.site.register(WorkflowEvent)
