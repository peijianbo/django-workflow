from collections import OrderedDict

from django.contrib.auth.models import Group
from django.db import models, transaction
from rest_framework import serializers
from rest_framework.fields import ChoiceField

from workflow.apps.user.models import User
from workflow.libs.frameworks.validators import is_identifier, is_choice_format

__all__ = ['Component', 'FormField', 'Workflow', 'WorkflowChain', 'WorkflowNode', 'WorkflowEvent']


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

    field_name = models.CharField(max_length=64, unique=True, validators=[is_identifier], verbose_name='字段名称')
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
    rank = models.IntegerField(verbose_name='分支优先级', help_text='用在条件分支中，条件分支都未命中时，根据rank升序并使用最后一个分支')

    type = models.CharField(max_length=16, choices=Type.choices, default=Type.DEPART_LEADER, verbose_name='审批类型')
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
            str(self.Type.SELF): requester,
            str(self.Type.ELECT): elected_approver,
            str(self.Type.PERSON): self.person,
            str(self.Type.ROLE): self.role.user_set.all().first() if self.role and self.role.user_set.all().exists() else None,  # TODO 多人处理
            str(self.Type.DEPART_LEADER): self.department.leader if self.department else None,
        }
        return approver_map.get(self.type, None)


class WorkflowEvent(models.Model):
    """工作流事件，由员工发起。如一个具体的请假/报销/办公用品申请"""

    class State(models.TextChoices):
        PENDING = 'PENDING', '待处理'
        PROCESSING = 'PROCESSING', '进行中'
        APPROVED = 'APPROVED', '已通过'
        REJECTED = 'REJECTED', '已驳回'

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


class WorkflowNode(models.Model):
    """
    具体的审批节点。
    申请人提交申请事件后，根据WorkflowChain定义的工作流程链，将具体审批节点拆解到此表。
    """

    class Action(models.TextChoices):
        PENDING = 'PENDING', '待处理'
        APPROVED = 'APPROVED', '已通过'
        REJECTED = 'REJECTED', '已驳回'

    event = models.ForeignKey('WorkflowEvent', on_delete=models.CASCADE, verbose_name='工作流事件')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children', verbose_name='父节点')
    approver = models.ForeignKey('user.User', null=True, on_delete=models.SET_NULL, related_name='nodes', verbose_name='审批者')
    action = models.CharField(max_length=16, choices=Action.choices, default=Action.PENDING, verbose_name='动作')
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

    def allow_action(self):
        if self.next_node and self.next_node.action != self.Action.PENDING:  # 下一节点已经审批完成
            return False
        if not self.previous_node:
            return True
        else:
            if self.previous_node.action == self.Action.APPROVED:
                return True
            return False

    @property
    def has_next(self):
        return WorkflowNode.objects.filter(event=self.event, rank__gt=self.rank).exists()

    @property
    def next_node(self):
        next_node = WorkflowNode.objects.filter(event=self.event, rank__gt=self.rank).first()
        if next_node:
            return next_node
        else:
            return None

    @property
    def previous_node(self):
        previous_node = WorkflowNode.objects.filter(event=self.event, rank__lt=self.rank).last()
        if previous_node:
            return previous_node
        else:
            return None

    def change_event_state(self):
        if self.action == self.Action.APPROVED:
            if self.has_next:
                self.event.state = WorkflowEvent.State.PROCESSING
            else:
                self.event.state = WorkflowEvent.State.APPROVED
        else:
            self.event.state = WorkflowEvent.State.REJECTED
        self.event.save()

    def approve(self, comment=None, actor=None):
        if not self.allow_action():
            raise Exception('拒绝审批')

        self.action = self.Action.APPROVED
        self.comment = comment
        self.actor = actor if actor else self.approver
        with transaction.atomic():
            self.save()
            self.change_event_state()

        from .signals import node_approved
        node_approved.send(sender=self.__class__, instance=self)

    def reject(self, comment=None, actor=None):
        if not self.allow_action():
            raise Exception('拒绝审批')

        self.action = self.Action.REJECTED
        self.comment = comment
        self.actor = actor if actor else self.approver
        with transaction.atomic():
            self.save()
            self.change_event_state()

        from .signals import node_rejected
        node_rejected.send(sender=self.__class__, instance=self)

    @classmethod
    def generate_workflow_node(cls, event: WorkflowEvent, approvers: dict):
        """生成审批节点
            当为审批者为发起人自选时需要传approvers: {'chain_id': 'user_id', ...}
        """
        parent_node = None
        next_chains = event.workflow.chains.filter(parent__isnull=True).all()  # 找到最靠前的审批节点链
        if not next_chains.exists():
            raise Exception('此工作流尚未设置审批链，请联系管理员配置审批链')

        def recursion_create_node(parent_node, next_chains):
            """递归创建审批节点"""
            with transaction.atomic():
                for chain in next_chains:
                    approver = chain.get_approver(approvers, event.requester)
                    if chain == next_chains.last():  # 最后一个默认条件分支
                        condition = '1 == 1'
                    else:
                        actual_value = int(event.form_fields.get(chain.form_field.field_name))
                        condition = f'{actual_value} {chain.operator} {chain.condition_value}'
                    if eval(condition):
                        parent_node = WorkflowNode.objects.create(event=event, approver=approver, parent=parent_node, comment=chain.comment)
                        next_chains = chain.children.all().order_by('rank')
                        has_find_branch = True
                    else:
                        continue
                    if next_chains.count() > 0:
                        recursion_create_node(parent_node, next_chains)
                    if has_find_branch:  # 一旦找到满足条件分支，终止循环
                        break

        recursion_create_node(parent_node, next_chains)
