import datetime

from rest_framework.serializers import ModelSerializer
from rest_framework.settings import api_settings

from .models import *


__all__ = ['WorkFlowSerializer', 'WorkFlowChainSerializer', 'WorkFlowNodeSerializer', 'WorkflowEventSerializer']


class WorkFlowSerializer(ModelSerializer):

    class Meta:
        model = Workflow
        fields = '__all__'


class WorkFlowChainSerializer(ModelSerializer):

    class Meta:
        model = WorkflowChain
        fields = '__all__'


class WorkFlowNodeSerializer(ModelSerializer):

    class Meta:
        model = WorkflowNode
        fields = '__all__'
        depth = 1


class WorkflowEventSerializer(ModelSerializer):

    class Meta:
        model = WorkflowEvent
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        # 根据不同工作流，动态生成序列化器字段, 如请假需要请假开始时间/结束时间/原因
        super(WorkflowEventSerializer, self).__init__(*args, **kwargs)
        workflow_id = None
        if hasattr(self, 'initial_data'):
            workflow_id = self.initial_data.get('workflow')
        if not workflow_id:
            return
        wf = Workflow.objects.filter(id=workflow_id).first()
        if not wf:
            return
        self.fields['extra_props'] = wf.generate_serializer()()

    def to_internal_value(self, data):
        # 将特殊格式的值如DateTimeField/FileField/ForeignKey等转为可json序列化的值
        result = super(WorkflowEventSerializer, self).to_internal_value(data)
        if 'extra_props' in result:
            for key, value in result['extra_props'].items():
                if isinstance(value, datetime.datetime):
                    result['extra_props'][key] = value.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(value, datetime.date):
                    result['extra_props'][key] = value.strftime('%Y-%m-%d')
                # TODO 处理其他无法json序列化的字段
        return result
