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


class WorkflowChainViewSet(mixins.CreateModelMixin,
                           GenericViewSet):
    filter_fields = ()
    search_fields = filter_fields

    queryset = WorkflowChain.objects.all()
    serializer_class = WorkFlowChainSerializer

    def create(self, request, *args, **kwargs):
        """ request.data:
            [
                {
                    "workflow_id": 1,
                    "form_field_id": 9,
                    "condition": "GTE",
                    "condition_value": 2,
                    "type": "PERSON",
                    "person_id": 2,
                    "rank": 1,
                    "comment": "大于等于2天，a_leader审批",
                    "children": [
                        {
                            "workflow_id": 1,
                            "form_field_id": null,
                            "condition": null,
                            "condition_value": null,
                            "type": "PERSON",
                            "person_id": 2,
                            "rank": 1,
                            "comment": "大于等于2天的子节点，a_leader审批",
                            "children": []
                        }
                    ]
                },
                {
                    "workflow_id": 1,
                    "form_field_id": 9,
                    "condition": "LT",
                    "condition_value": 2,
                    "type": "PERSON",
                    "person_id": 1,
                    "rank": 2,
                    "comment": "小于2，admin审批",
                    "children": []
                },
                {
                    "workflow_id": 1,
                    "form_field_id": null,
                    "condition": null,
                    "condition_value": null,
                    "type": "PERSON",
                    "person_id": 3,
                    "rank": 3,
                    "comment": "其他情况，打工人审批",
                    "children": []
                }
            ]
        """
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(status=status.HTTP_201_CREATED)

    @action(methods=['get'], detail=False, url_path='chain_tree', name='chain_tree')
    def chain_tree(self, request, **kwargs):
        """返回类似创建chain时前端传过来的数据接口，方便前端回显"""
        workflow_id = request.query_params.get('workflow_id', None)
        if not workflow_id:
            return Response(data={'msg': '请求参数缺失。'}, status=status.HTTP_400_BAD_REQUEST)
        chains_queryset = WorkflowChain.objects.filter(workflow_id=workflow_id)
        chains = WorkFlowChainSerializer(chains_queryset, many=True).data
        tree = [chain for chain in chains if chain['parent_id'] is None]
        for chain in chains:
            chain['children'] = [c for c in chains if chain['id'] == c['parent_id']]
        return Response(data=tree, status=status.HTTP_200_OK)


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
        obj.approve(approver=request.user, comment=comment)
        return Response(data={'msg': '审批成功'}, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path='reject', name='reject', permission_classes=[IsApprover])
    def reject_view(self, request, pk=None):
        comment = request.data.get('comment')
        obj = self.get_object()
        obj.reject(approver=request.user, comment=comment)
        return Response(data={'msg': '已驳回'}, status=status.HTTP_200_OK)
