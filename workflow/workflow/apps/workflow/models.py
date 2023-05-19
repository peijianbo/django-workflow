from django.contrib.auth.models import Group
from django.db import models, transaction
from rest_framework import serializers


__all__ = ['Field', 'Workflow', 'WorkflowChain', 'WorkflowNode', 'WorkflowEvent']


class Field(models.Model):
    class Type(models.TextChoices):
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

    name = models.CharField(max_length=32, verbose_name='字段名称')
    label = models.CharField(max_length=64, verbose_name='字段标签')
    type = models.CharField(max_length=32, choices=Type.choices, default=Type.STR, verbose_name='字段类型')
    default = models.JSONField(default=dict, blank=True, verbose_name='默认值')
    required = models.BooleanField(default=False, verbose_name='是否必须')

    def __str__(self):
        return self.label

    class Meta:
        db_table = 'workflow_field'
        verbose_name = '工作流字段'
        verbose_name_plural = verbose_name

    def to_serializer_field(self):
        field = self.Type.map().get(self.type)
        kwargs = {'required': False}
        if self.required:
            kwargs['required'] = True
            return field(**kwargs)
        if self.default:
            kwargs['default'] = self.default
        return field(**kwargs)


class Workflow(models.Model):
    """
    工作流。
    如请假流/报销流
    """
    name = models.CharField(max_length=128, unique=True, verbose_name='工作流名称', help_text='如请假/报销等')
    fields = models.ManyToManyField(Field, verbose_name='字段', help_text='工作流的必要字段，如请假需要开始时间/结束时间')
    comment = models.CharField(max_length=256, null=True, blank=True, verbose_name='备注')

    class Meta:
        db_table = 'workflow_workflow'
        verbose_name = '工作流'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

    def generate_serializer(self):
        fields = self.fields.all()
        serializer_fields = {f.name: f.to_serializer_field() for f in fields}
        return type('WorkflowFieldSerializer', (serializers.Serializer,), serializer_fields)


class WorkflowChain(models.Model):
    """
    工作流程链。每个工作流下都关联一个完整的工作流程链。
    如一个请假工作流的流程链：部门部长-->HRBP-->人事专员-->CEO
    建议大层级rank值以10为间隔递增，小层级rank值以1为间隔递增,方便实现同一级的多人审批
    如 部门副部长(rank=1) -->  HRBP(rank=20)  -->  人事专员(rank=30)  -->  CEO(rank=40)
       部门部长(rank=2)                       -->  人事部长(rank=31)
    """

    class Type(models.TextChoices):
        PERSON = 'PERSON', '人'
        ROLE = 'ROLE', '角色'
        DEPART_LEADER = 'DEPART_LEADER', '部门领导'

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='chains', verbose_name='工作流')
    type = models.CharField(max_length=16, choices=Type.choices, default=Type.DEPART_LEADER, verbose_name='审批类型')
    person = models.ForeignKey('user.User', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='审批人')
    role = models.ForeignKey(Group, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='角色')
    department = models.ForeignKey('user.Department', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='审批部门')
    rank = models.IntegerField(verbose_name='审批顺序', help_text='数字由小到大，数字越大审批顺序越靠后')

    class Meta:
        db_table = 'workflow_chain'
        ordering = ['rank']
        verbose_name = '工作流程链'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.workflow.name

    def get_approver(self):
        if self.type == self.Type.PERSON:
            return self.person
        elif self.type == self.Type.ROLE:
            return self.role.user_set.all().first() if self.role and self.role.user_set.all().exists() else None
        elif self.type == self.Type.DEPART_LEADER:
            return self.department.leader if self.department else None


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
    extra_props = models.JSONField(default=dict, blank=True, verbose_name='其他信息')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'workflow_event'
        verbose_name = '工作流事件'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.requester.username}-{self.workflow.name}-{self.get_state_display()}"

    def save(self, *args, **kwargs):
        if not self.pk:  # 创建操作
            super().save(*args, **kwargs)
            WorkflowNode.generate_workflow_node(self)
        else:  # 更新操作
            super(WorkflowEvent, self).save(*args, **kwargs)


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
    approver = models.ForeignKey('user.User', null=True, on_delete=models.SET_NULL, related_name='nodes',
                                 verbose_name='审批者')
    rank = models.IntegerField(verbose_name='审批顺序', help_text='数字由小到大，数字越大审批顺序越靠后')
    action = models.CharField(max_length=16, choices=Action.choices, default=Action.PENDING, verbose_name='动作')
    actor = models.ForeignKey('user.User', null=True, on_delete=models.SET_NULL, verbose_name='执行者',
                              help_text='实际执行者，可能是权限更高的角色如人事')
    action_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    comment = models.CharField(max_length=256, null=True, blank=True, verbose_name='备注')

    class Meta:
        db_table = 'workflow_node'
        ordering = ['rank']
        verbose_name = '工作流节点'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.event.requester.username}-{self.event.workflow.name}-" \
               f"{self.get_action_display()}({self.approver.username})-{self.rank}"

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
        self.save()

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
    def generate_workflow_node(cls, event: WorkflowEvent):
        """生成审批节点"""
        chains = event.workflow.chains.all()
        if not chains.exists():
            raise Exception('此工作流尚未设置审批链，请联系管理员配置审批链')
        with transaction.atomic():
            for chain in chains:
                approver = chain.get_approver()
                wn = WorkflowNode.objects.create(event=event, approver=approver, rank=chain.rank)
