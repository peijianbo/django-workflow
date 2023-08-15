import datetime

from django.db import transaction
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from workflow.libs.frameworks.serializers import DisplayModelSerializer
from .models import *
from ..user.serializers import UserSerializer


__all__ = ['ComponentSerializer', 'FormFieldSerializer', 'WorkFlowSerializer', 'WorkFlowChainSerializer',
           'WorkFlowNodeSerializer', 'WorkflowEventSerializer']


class ComponentSerializer(ModelSerializer):

    class Meta:
        model = Component
        fields = '__all__'


class FormFieldSerializer(ModelSerializer):
    workflow_id = serializers.IntegerField(label='工作流ID')
    component_id = serializers.IntegerField(label='组件ID')

    class Meta:
        model = FormField
        fields = '__all__'
        extra_kwargs = {
            'workflow': {'required': False},
            'component': {'required': False},
        }


class WorkFlowSerializer(ModelSerializer):

    class Meta:
        model = Workflow
        fields = '__all__'


class WorkFlowChainListSerializer(serializers.ListSerializer):
    @classmethod
    def recursion_create_chain(cls, validated_data, parent=None, created_chains=None):
        """递归创建审批链节点"""
        if created_chains is None:
            created_chains = []
        for data in validated_data:
            serializer = WorkFlowChainSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            children = data.pop('children', [])
            chain = WorkflowChain.objects.create(parent=parent, **data)
            created_chains.append(chain)
            cls.recursion_create_chain(children, parent=chain, created_chains=created_chains)
        return created_chains

    def create(self, validated_data):
        with transaction.atomic():
            workflow_id = validated_data[0].get('workflow_id', None) if len(validated_data) > 0 else None
            WorkflowChain.objects.filter(workflow_id=workflow_id).delete()  # 不支持编辑，想要修改流程链，走创建逻辑
            return self.recursion_create_chain(validated_data)


class WorkFlowChainSerializer(ModelSerializer):
    parent_id = serializers.IntegerField(read_only=True, label='父节点ID')
    workflow_id = serializers.IntegerField(write_only=True, label='工作流ID')
    form_field_id = serializers.IntegerField(write_only=True, required=False, allow_null=True, label='表单字段ID')
    person_id = serializers.IntegerField(write_only=True, required=False, allow_null=True, label='用户ID')
    role_id = serializers.IntegerField(write_only=True, required=False, allow_null=True, label='角色ID')
    department_id = serializers.IntegerField(write_only=True, required=False, allow_null=True, label='部门ID')
    workflow = WorkFlowSerializer(read_only=True, label='工作流')
    children = serializers.ListSerializer(child=serializers.DictField(), write_only=True, required=False)

    class Meta:
        model = WorkflowChain
        fields = '__all__'
        list_serializer_class = WorkFlowChainListSerializer


class WorkFlowNodeSerializer(ModelSerializer):

    class Meta:
        model = WorkflowNode
        fields = '__all__'
        depth = 1


class WorkflowEventSerializer(DisplayModelSerializer):
    # 审批链节点类型为发起人自选时，需要传该参数，格式为：{'chain_id': 'user_id', ...}
    requester_id = serializers.IntegerField(write_only=True, label='发起人ID')
    requester = UserSerializer(read_only=True, label='发起人')
    workflow_id = serializers.IntegerField(write_only=True, label='工作流ID')
    workflow = WorkFlowSerializer(read_only=True, label='工作流')
    node_process = serializers.ListField(label='审批进度')
    chain_approver_dict = serializers.DictField(child=serializers.CharField(), allow_empty=True, allow_null=True, required=False, write_only=True)

    class Meta:
        model = WorkflowEvent
        fields = '__all__'
        read_only_fields = ('state',)

    def __init__(self, *args, **kwargs):
        # 根据不同工作流，动态生成表单序列化器字段
        super(WorkflowEventSerializer, self).__init__(*args, **kwargs)
        workflow_id = None
        if hasattr(self, 'initial_data'):
            workflow_id = self.initial_data.get('workflow_id')
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

    def validate_approvers(self, value):
        """校验自选审批人节点是否指定了审批人"""
        chains = Workflow.objects.filter(id=self.initial_data['workflow_id']).first().chains.all()
        for chain in chains:
            if chain.type == WorkflowChain.Type.ELECT and str(chain.id) not in value:
                raise serializers.ValidationError(f'自选审批人节点未指定审批人【chain_id:{chain.id}】')
        return value

    def create(self, validated_data):
        """创建工作流事件时，触发生成审批节点动作"""
        chain_approver_dict = validated_data.pop('chain_approver_dict', {})
        with transaction.atomic():
            instance = super(WorkflowEventSerializer, self).create(validated_data)
            WorkflowNode.generate_workflow_node(instance, chain_approver_dict)
        return instance
