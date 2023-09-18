import typing
from collections import OrderedDict

from django.contrib.auth.models import Group
from django.db import models, transaction
from rest_framework import serializers
from rest_framework.fields import ChoiceField

from workflow.libs.utils.common_util import sort_nodes_by_parent, chain_getattr
from workflow.apps.user.models import User
from workflow.libs.frameworks.validators import is_identifier, is_choice_format

__all__ = ['Component', 'FormField', 'Workflow', 'WorkflowChain', 'WorkflowNode', 'WorkflowEvent']


class Action(models.TextChoices):
    PENDING = 'PENDING', '待处理'
    APPROVED = 'APPROVED', '已通过'
    REJECTED = 'REJECTED', '已驳回'


class State(models.TextChoices):
    PENDING = 'PENDING', '待处理'
    PROCESSING = 'PROCESSING', '进行中'
    APPROVED = 'APPROVED', '已通过'
    REJECTED = 'REJECTED', '已驳回'


class Component(models.Model):
    class UIType(models.TextChoices):
        INPUT = 'INPUT', '单行输入框'
        TEXT = 'TEXT', '多行输入框'
        RADIO = 'RADIO', '单选框'
        CHECKBOX = 'CHECKBOX', '多选框'
        DATEPICKER = 'DATEPICKER', '日期选择器'

    class DataType(models.TextChoices):
        STR = 'STR', '字符串'
        INT = 'INT', '整数'
        DATETIME = 'DATETIME', '日期时间'
        DATA = 'DATA', '日期'

        @classmethod
        def map(cls):
            return {
                cls.STR: serializers.CharField,
                cls.INT: serializers.IntegerField,
                cls.DATETIME: serializers.DateTimeField,
                cls.DATA: serializers.DateField,
            }

    name = models.CharField(max_length=64, verbose_name='名称')
    ui_type = models.CharField(max_length=32, choices=UIType.choices, verbose_name='UI类型')
    data_type = models.CharField(max_length=32, choices=DataType.choices, verbose_name='数据类型')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'wf_component'
        verbose_name = '工作流表单组件'
        verbose_name_plural = verbose_name


class FormField(models.Model):

    field_name = models.CharField(max_length=64, validators=[is_identifier], verbose_name='字段名称')
    component = models.ForeignKey(Component, on_delete=models.PROTECT, verbose_name='组件')
    workflow = models.ForeignKey('Workflow', related_name='form_fields', on_delete=models.CASCADE, verbose_name='工作流')
    placeholder = models.CharField(max_length=128, default='', blank=True, verbose_name='提示语')
    rank = models.IntegerField(verbose_name='字段在表单中的上下排列顺序')
    required = models.BooleanField(default=False, verbose_name='是否必须')
    # choices: ['婚假', '产假', ...]
    choices = models.JSONField(default=list, blank=True, validators=[is_choice_format], verbose_name='可选项(针对单/多选框组件)')

    def __str__(self):
        return self.field_name

    def to_serializer_field(self):
        field = Component.DataType.map().get(self.component.data_type)
        kwargs = {'required': False}
        if self.required:
            kwargs['required'] = True
        if len(self.choices) != 0:
            kwargs['choices'] = OrderedDict([(c, c) for c in self.choices])
            return ChoiceField(**kwargs)
        return field(**kwargs)

    class Meta:
        db_table = 'wf_form_field'
        verbose_name = '工作流表单字段'
        verbose_name_plural = verbose_name
        ordering = ['rank']
        unique_together = [('workflow_id', 'field_name')]


class Workflow(models.Model):
    """
    工作流。
    如请假流/报销流
    """
    name = models.CharField(max_length=128, unique=True, verbose_name='工作流名称', help_text='如请假/报销等')
    comment = models.CharField(max_length=256, null=True, blank=True, verbose_name='备注')

    class Meta:
        db_table = 'wf_workflow'
        verbose_name = '工作流'
        verbose_name_plural = verbose_name
        ordering = ['name']

    def __str__(self):
        return self.name

    def generate_form_serializer(self):
        fields = self.form_fields.all()
        serializer_fields = {f.field_name: f.to_serializer_field() for f in fields}
        return type('WorkflowFormSerializer', (serializers.Serializer,), serializer_fields)


class WorkflowChain(models.Model):
    """
    工作流程链。每个工作流下都关联一个完整的工作流程链。
    如一个请假工作流的流程链：部门部长-->HRBP-->人事专员-->CEO
    """

    class Type(models.TextChoices):
        """
            type的作用：确定每个审批节点的类型。
            type=SELF表示该节点由发起人审批。
            type=CUSTOM表示该节点由发起人指定。
            type=PERSON表示该节点由指定的具体的人审批。
            type=ROLE表示该节点由指定的角色进行审批而非具体到人。
            type=DEPART_LEADER表示该节点由部门领导进行审批。
            用法详见WorkflowChain.get_approver函数
        """
        SELF = 'SELF', '发起人自己'
        ELECT = 'ELECT', '发起人自选'
        PERSON = 'PERSON', '指定人'
        ROLE = 'ROLE', '指定角色'
        DEPART_LEADER = 'DEPART_LEADER', '部门领导'

    class Mode(models.TextChoices):
        OR = 'OR', '或签'
        AND = 'AND', '会签'

    class Condition(models.TextChoices):
        LT = 'LT', '小于'
        LTE = 'LTE', '小于等于'
        E = 'E', '等于'
        GT = 'GT', '大于'
        GTE = 'GTE', '大于等于'
        # RANGE = 'RANGE', '介于(两数之间)'

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='chains', verbose_name='工作流')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children', verbose_name='父节点')

    form_field = models.ForeignKey(FormField, null=True, blank=True, on_delete=models.PROTECT, related_name='conditions', verbose_name='表单字段')
    condition = models.CharField(max_length=16, null=True, blank=True, choices=Condition.choices, verbose_name='条件')
    condition_value = models.IntegerField(null=True, blank=True, verbose_name='条件值')
    rank = models.IntegerField(verbose_name='分支优先级', help_text='用在条件分支中，条件分支都未命中时，根据rank升序并使用最后一个分支，'
                                                                    '这也就要求创建chain时，条件分支都要加一个rank最大的默认分支')

    type = models.CharField(max_length=16, choices=Type.choices, default=Type.DEPART_LEADER, verbose_name='审批人类型')
    mode = models.CharField(max_length=16, choices=Mode.choices, default=Mode.AND, verbose_name='审批方式')

    person = models.ForeignKey('user.User', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='审批人')
    role = models.ForeignKey(Group, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='角色')
    department = models.ForeignKey('user.Department', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='审批部门')
    comment = models.CharField(max_length=256, null=True, blank=True, verbose_name='备注')

    class Meta:
        db_table = 'wf_chain'
        verbose_name = '工作流程链'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.workflow.name}-审批链节点-{self.id}"

    @property
    def operator(self):
        operator_map = {
            str(self.Condition.LT): '<',
            str(self.Condition.LTE): '<=',
            str(self.Condition.E): '==',
            str(self.Condition.GT): '>',
            str(self.Condition.GTE): '>=',
        }
        return operator_map.get(self.condition, None)

    def get_approver(self, approvers: dict, requester: User):
        elected_approver = None
        if self.type == WorkflowChain.Type.ELECT and str(self.id) in approvers:
            elected_approver = User.objects.filter(id=approvers[str(self.id)]).first()
        approver_map = {
            str(self.Type.SELF): [requester],
            str(self.Type.ELECT): [elected_approver],
            str(self.Type.PERSON): [self.person],
            str(self.Type.ROLE): self.role.user_set.all() if self.role and self.role.user_set.all().exists() else [],  # TODO 多人处理
            str(self.Type.DEPART_LEADER): [self.department.leader] if self.department else [],
        }
        return approver_map.get(self.type, [])


class WorkflowEvent(models.Model):
    """工作流事件，由员工发起。如一个具体的请假/报销/办公用品申请"""

    requester = models.ForeignKey('user.User', on_delete=models.CASCADE, verbose_name='申请人')
    workflow = models.ForeignKey('Workflow', on_delete=models.PROTECT, verbose_name='工作流')
    state = models.CharField(max_length=16, choices=State.choices, default=State.PENDING, verbose_name='状态')
    # 根据不同工作流程链，存储不同信息。如请假会包含开始时间/结束时间
    form_fields = models.JSONField(default=dict, blank=True, verbose_name='表单信息')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'wf_event'
        verbose_name = '工作流事件'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.requester.username}-{self.workflow.name}-{self.get_state_display()}"

    def node_process(self):
        node_objs = self.nodes.all()
        nodes = []
        for node in node_objs:
            approvers = []
            for a in node.nodeapprover_set.all():
                approvers.append({'user_id': a.approver_id, 'username': User.objects.get(id=a.approver_id).username, 'state': a.action})
            nodes.append({
                'id': node.id,
                'parent_id': node.parent_id,
                'approvers': approvers,
                'mode': node.mode,
                'mode_display': node.get_mode_display(),
                'actor': node.actor.username if node.actor else '',
                'node_state': node.state,
            })
        order_nodes = sort_nodes_by_parent(nodes)
        return order_nodes


class WorkflowNode(models.Model):
    """
    具体的审批节点。
    申请人提交申请事件后，根据WorkflowChain定义的工作流程链，将具体审批节点拆解到此表。
    """

    class Mode(models.TextChoices):
        OR = 'OR', '或签'
        AND = 'AND', '会签'
    # TODO 维护一个processing_node字段
    event = models.ForeignKey('WorkflowEvent', related_name='nodes', on_delete=models.CASCADE, verbose_name='工作流事件')
    parent = models.OneToOneField('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children', verbose_name='父节点')  # 注意OneToOneField的子节点不存在时，obj.children会报错
    approvers = models.ManyToManyField('user.User', through='NodeApprover', related_name='nodes', verbose_name='审批者')
    mode = models.CharField(max_length=16, choices=Mode.choices, default=Mode.AND, verbose_name='审批方式')
    state = models.CharField(max_length=16, choices=State.choices, default=State.PENDING, verbose_name='状态')

    actor = models.ForeignKey('user.User', null=True, on_delete=models.SET_NULL, verbose_name='执行者',
                              help_text='实际执行者，可能是权限更高的角色如人事')
    action_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    comment = models.CharField(max_length=256, null=True, blank=True, verbose_name='备注')

    class Meta:
        db_table = 'wf_node'
        verbose_name = '工作流节点'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.event.requester.username}-{self.event.workflow.name}-" \
               f"{self.get_action_display()}({getattr(self.approver, 'username', '')})"

    def validate_action(self, approver: User):
        if approver not in self.approvers.all():
            return False, '不是审批人'
        if self.mode == self.Mode.OR and NodeApprover.objects.filter(node_id=self.id).exclude(action=Action.PENDING).exists():
            return False, '已被或签成员审批'
        if hasattr(self, 'children') and getattr(self, 'children').state != Action.PENDING:  # 下一节点已经在审批中或审批完成
            return False, '禁止操作，下一节点已经审批完成'
        if self.parent and self.parent.state != Action.APPROVED:  # 上一节点审批尚未通过
            return False, '禁止操作，父节点审批尚未通过'
        return True, ''

    def change_node_state(self, action: typing.Literal[Action.APPROVED, Action.REJECTED]):
        if action == Action.REJECTED:
            self.state = State.REJECTED
        else:
            nas = NodeApprover.objects.filter(node_id=self.id)
            if self.mode == self.Mode.OR:
                self.state = State.APPROVED
                if hasattr(self, 'children'):
                    self.children.state = State.PROCESSING
                    self.children.save()
            else:
                if all(action == Action.APPROVED for action in nas.values_list('action', flat=True)):
                    self.state = State.APPROVED
                    if hasattr(self, 'children'):
                        self.children.state = State.PROCESSING
                        self.children.save()
                else:
                    self.state = State.PROCESSING
        self.save()
        return self.state

    def change_event_state(self, action: typing.Literal[Action.APPROVED, Action.REJECTED]):
        if action == Action.REJECTED:
            self.event.state = State.REJECTED
            return self.event.save()
        if self.mode == self.Mode.OR or \
           (self.mode == self.Mode.AND and all(action == Action.APPROVED for action in NodeApprover.objects.filter(node_id=self.id).values_list('action', flat=True))):
            self.event.state = State.APPROVED
            return self.event.save()
        if self.mode == self.Mode.AND and NodeApprover.objects.filter(node_id=self.id, action=Action.PENDING).exists():
            self.event.state = State.PROCESSING
            return self.event.save()

    def approve(self, approver: User, comment=None):
        can_do_action, msg = self.validate_action(approver)
        if not can_do_action:
            raise Exception(f'当前节点不允许审批-{msg}')

        an = NodeApprover.objects.filter(approver_id=approver.id, node_id=self.id).first()
        with transaction.atomic():
            an.action = Action.APPROVED
            an.comment = comment
            an.save()
            self.change_node_state(Action.APPROVED)
            self.change_event_state(Action.APPROVED)

        from .signals import node_approved
        node_approved.send(sender=self.__class__, instance=self)

    def reject(self, approver: User, comment=None):
        can_do_action, msg = self.validate_action(approver)
        if not can_do_action:
            raise Exception(f'当前节点不允许审批-{msg}')

        an = NodeApprover.objects.filter(approver_id=approver.id, node_id=self.id).first()
        with transaction.atomic():
            an.action = Action.REJECTED
            an.comment = comment
            an.save()
            self.change_node_state(Action.REJECTED)
            self.change_event_state(Action.REJECTED)

        from .signals import node_rejected
        node_rejected.send(sender=self.__class__, instance=self)

    @classmethod
    def generate_workflow_node(cls, event: WorkflowEvent, chain_approver_dict: dict):
        """生成审批节点
            当为审批者为发起人自选时需要传chain_approver_dict: {'chain_id': 'user_id', ...}
        """
        parent_node = None
        next_chains = event.workflow.chains.filter(parent__isnull=True).all()  # 找到最靠前的审批节点链
        if not next_chains.exists():
            raise Exception('此工作流尚未设置审批链，请联系管理员配置审批链')

        def recursion_create_node(parent_node, next_chains):
            """递归创建审批节点"""
            with transaction.atomic():
                for chain in next_chains:
                    approvers = chain.get_approver(chain_approver_dict, event.requester)
                    if chain == next_chains.last():  # 非条件分支节点或条件分支的最后一个默认分支
                        condition = '1 == 1'
                    else:
                        actual_value = int(event.form_fields.get(chain.form_field.field_name))
                        condition = f'{actual_value} {chain.operator} {chain.condition_value}'
                    if eval(condition):
                        state = State.PROCESSING if parent_node is None else State.PENDING  # 首节点设置状态为进行中
                        parent_node = WorkflowNode.objects.create(event=event, mode=chain.mode, parent=parent_node, state=state, comment=chain.comment)
                        parent_node.approvers.add(*approvers)
                        next_chains = chain.children.all().order_by('rank')
                        has_find_branch = True
                    else:
                        continue
                    if next_chains.count() > 0:
                        recursion_create_node(parent_node, next_chains)
                    if has_find_branch:  # 一旦找到满足条件分支，终止循环
                        break

        recursion_create_node(parent_node, next_chains)


class NodeApprover(models.Model):
    """审批节点-审批人"""

    node = models.ForeignKey(WorkflowNode, on_delete=models.CASCADE, verbose_name='节点')
    approver = models.ForeignKey('user.User', on_delete=models.CASCADE, verbose_name='审批人')
    action = models.CharField(max_length=16, choices=Action.choices, default=Action.PENDING, verbose_name='动作')
    comment = models.CharField(max_length=256, null=True, blank=True, verbose_name='备注')

    class Meta:
        db_table = 'wf_node_approver'
        verbose_name = '审批节点-审批人'
        verbose_name_plural = verbose_name
