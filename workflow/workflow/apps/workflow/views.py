from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from workflow.libs.frameworks.permissions import IsApprover
from .models import *
from .serializers import *


__all__ = ['ComponentViewSet', 'WorkflowFormFieldViewSet', 'WorkflowViewSet', 'WorkflowChainViewSet',
           'WorkflowNodeViewSet', 'WorkflowEventViewSet']


class ComponentViewSet(ModelViewSet):
    filter_fields = ()
    search_fields = filter_fields

    queryset = Component.objects.all()
    serializer_class = ComponentSerializer


class WorkflowFormFieldViewSet(ModelViewSet):
    filter_fields = ()
    search_fields = filter_fields

    queryset = FormField.objects.all()
    serializer_class = FormFieldSerializer


class WorkflowViewSet(ModelViewSet):
    filter_fields = ()
    search_fields = filter_fields

    queryset = Workflow.objects.all()
    serializer_class = WorkFlowSerializer


class WorkflowChainViewSet(ModelViewSet):
    filter_fields = ()
    search_fields = filter_fields

    queryset = WorkflowChain.objects.all()
    serializer_class = WorkFlowChainSerializer


class WorkflowEventViewSet(ModelViewSet):
    filter_fields = ()
    search_fields = filter_fields

    queryset = WorkflowEvent.objects.all()
    serializer_class = WorkflowEventSerializer


class WorkflowNodeViewSet(mixins.RetrieveModelMixin,
                          mixins.UpdateModelMixin,
                          mixins.ListModelMixin,
                          GenericViewSet):
    filter_fields = ()
    search_fields = filter_fields

    queryset = WorkflowNode.objects.all()
    serializer_class = WorkFlowNodeSerializer

    @action(methods=['post'], detail=True, url_path='approve', name='approve', permission_classes=[IsApprover])
    def approve_view(self, request, pk=None):
        comment = request.data.get('comment')
        obj = self.get_object()
        obj.approve(comment=comment)
        return Response(data={'msg': '审批成功'}, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path='reject', name='reject', permission_classes=[IsApprover])
    def reject_view(self, request, pk=None):
        comment = request.data.get('comment')
        obj = self.get_object()
        obj.reject(comment=comment)
        return Response(data={'msg': '已驳回'}, status=status.HTTP_200_OK)
