# Generated by Django 3.2 on 2023-05-19 07:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('user', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Field',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32, verbose_name='字段名称')),
                ('label', models.CharField(max_length=64, verbose_name='字段标签')),
                ('type', models.CharField(choices=[('STR', '字符串'), ('INT', '整数'), ('DATETIME', '日期时间'), ('DATA', '日期')], default='STR', max_length=32, verbose_name='字段类型')),
                ('default', models.JSONField(blank=True, default=dict, verbose_name='默认值')),
                ('required', models.BooleanField(default=False, verbose_name='是否必须')),
            ],
            options={
                'verbose_name': '工作流字段',
                'verbose_name_plural': '工作流字段',
                'db_table': 'workflow_field',
            },
        ),
        migrations.CreateModel(
            name='Workflow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='如请假/报销等', max_length=128, unique=True, verbose_name='工作流名称')),
                ('comment', models.CharField(blank=True, max_length=256, null=True, verbose_name='备注')),
                ('fields', models.ManyToManyField(help_text='工作流的必要字段，如请假需要开始时间/结束时间', to='workflow.Field', verbose_name='字段')),
            ],
            options={
                'verbose_name': '工作流',
                'verbose_name_plural': '工作流',
                'db_table': 'workflow_workflow',
            },
        ),
        migrations.CreateModel(
            name='WorkflowEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.CharField(choices=[('PENDING', '待处理'), ('PROCESSING', '进行中'), ('APPROVED', '已通过'), ('REJECTED', '已驳回')], default='PENDING', max_length=16, verbose_name='状态')),
                ('extra_props', models.JSONField(blank=True, default=dict, verbose_name='其他信息')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('requester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='申请人')),
                ('workflow', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='workflow.workflow', verbose_name='工作流')),
            ],
            options={
                'verbose_name': '工作流事件',
                'verbose_name_plural': '工作流事件',
                'db_table': 'workflow_event',
            },
        ),
        migrations.CreateModel(
            name='WorkflowNode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rank', models.IntegerField(help_text='数字由小到大，数字越大审批顺序越靠后', verbose_name='审批顺序')),
                ('action', models.CharField(choices=[('PENDING', '待处理'), ('APPROVED', '已通过'), ('REJECTED', '已驳回')], default='PENDING', max_length=16, verbose_name='动作')),
                ('action_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('comment', models.CharField(blank=True, max_length=256, null=True, verbose_name='备注')),
                ('actor', models.ForeignKey(help_text='实际执行者，可能是权限更高的角色如人事', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='执行者')),
                ('approver', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='nodes', to=settings.AUTH_USER_MODEL, verbose_name='审批者')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workflow.workflowevent', verbose_name='工作流事件')),
            ],
            options={
                'verbose_name': '工作流节点',
                'verbose_name_plural': '工作流节点',
                'db_table': 'workflow_node',
                'ordering': ['rank'],
            },
        ),
        migrations.CreateModel(
            name='WorkflowChain',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('PERSON', '人'), ('ROLE', '角色'), ('DEPART_LEADER', '部门领导')], default='DEPART_LEADER', max_length=16, verbose_name='类型')),
                ('rank', models.IntegerField(help_text='数字由小到大，数字越大审批顺序越靠后', verbose_name='审批顺序')),
                ('department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='user.department', verbose_name='审批部门')),
                ('person', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='审批人')),
                ('role', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.group', verbose_name='角色')),
                ('workflow', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chains', to='workflow.workflow', verbose_name='工作流')),
            ],
            options={
                'verbose_name': '工作流程链',
                'verbose_name_plural': '工作流程链',
                'db_table': 'workflow_chain',
                'ordering': ['rank'],
            },
        ),
    ]