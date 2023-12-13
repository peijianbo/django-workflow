from django.contrib.auth.models import AbstractUser, Group
from django.db import models


__all__ = ['User', 'Department', 'Menu']


class User(AbstractUser):
    """用户模型"""
    class Meta:
        verbose_name_plural = '用户管理'


class Department(models.Model):
    """部门模型"""
    name = models.CharField(max_length=128, verbose_name='部门名称')
    code = models.CharField(max_length=128, verbose_name='部门编号')
    leader = models.ForeignKey('User', on_delete=models.PROTECT, verbose_name='部门领导')

    class Meta:
        db_table = 'workflow_department'
        verbose_name = '部门'
        verbose_name_plural = '部门管理'

    def __str__(self):
        return self.name


class Menu(models.Model):
    """菜单/按钮模型，菜单宽泛讲也算是一种按钮，所以共用一张表，也方便前端router配置"""
    class Type(models.TextChoices):
        MENU = 'MENU', '菜单'
        BUTTON = 'BUTTON', '按钮'

    name = models.CharField(max_length=32, verbose_name='名称')
    code = models.CharField(max_length=32, unique=True, verbose_name='编码')
    type = models.CharField(max_length=16, default=Type.MENU, choices=Type.choices, verbose_name='类型')
    path = models.CharField(max_length=512, null=True, verbose_name='菜单路径', help_text='游览器url框中显示的路径,顶级菜单须以`/`开头')
    active_menu = models.CharField(max_length=512, null=True, verbose_name='活跃菜单', help_text='高亮效果的菜单')
    component = models.CharField(max_length=256, null=True, blank=True, verbose_name='前端组件', help_text='父级菜单可不填此项')
    icon = models.CharField(max_length=256, null=True, verbose_name='菜单图标', help_text='el-icon图标编码')
    rank = models.IntegerField(default=0, verbose_name='菜单排序')
    hidden = models.BooleanField(default=False, verbose_name='是否隐藏')
    allow_show = models.BooleanField(default=False, verbose_name='是否总是显示', help_text='控制父级菜单仅有一个子菜单时，是否显示父级菜单')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, verbose_name='上级菜单')
    roles = models.ManyToManyField(Group, blank=True, verbose_name='角色')

    class Meta:
        db_table = 'wf_menu'
        verbose_name = '菜单/按钮'
        verbose_name_plural = '菜单/按钮管理'

    def __str__(self):
        return self.name
