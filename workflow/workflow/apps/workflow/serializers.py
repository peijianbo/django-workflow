import datetime

from rest_framework.serializers import ModelSerializer
from rest_framework.settings import api_settings

from .models import *


__all__ = ['ComponentSerializer', 'FormFieldSerializer', 'WorkFlowSerializer', 'WorkFlowChainSerializer',
           'WorkFlowNodeSerializer', 'WorkflowEventSerializer']


class ComponentSerializer(ModelSerializer):

    class Meta:
        model = Component
        fields = '__all__'


class FormFieldSerializer(ModelSerializer):

    class Meta:
        model = FormField
        fields = '__all__'


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
        read_only_fields = ('state',)

    def __init__(self, *args, **kwargs):
        # 根据不同工作流，动态生成表单序列化器字段
        super(WorkflowEventSerializer, self).__init__(*args, **kwargs)
        workflow_id = None
        if hasattr(self, 'initial_data'):
            workflow_id = self.initial_data.get('workflow')
        if not workflow_id:
            return
        wf = Workflow.objects.filter(id=workflow_id).first()
        if not wf:
            return
        self.fields['form_fields'] = wf.generate_form_serializer()()

    def to_internal_value(self, data):
        # 将特殊格式的值如DateTimeField/FileField/ForeignKey等转为可json序列化的值
        result = super(WorkflowEventSerializer, self).to_internal_value(data)
        if 'form_fields' in result:
            for key, value in result['form_fields'].items():
                if isinstance(value, datetime.datetime):
                    result['form_fields'][key] = value.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(value, datetime.date):
                    result['form_fields'][key] = value.strftime('%Y-%m-%d')
                # TODO 处理其他无法json序列化的字段
        return result
