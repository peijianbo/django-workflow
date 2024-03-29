from rest_framework.routers import DefaultRouter

from .views import *

router = DefaultRouter()
router.register('workflows', WorkflowViewSet, 'workflows')
router.register('components', ComponentViewSet, 'components')
router.register('form_fields', WorkflowFormFieldViewSet, 'form_fields')
router.register('workflow_chains', WorkflowChainViewSet, 'workflow_chains')
router.register('workflow_nodes', WorkflowNodeViewSet, 'workflow_nodes')
router.register('workflow_events', WorkflowEventViewSet, 'workflow_events')

urlpatterns = [
]

urlpatterns += router.urls
