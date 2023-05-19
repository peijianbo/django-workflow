from django.contrib.auth.models import AbstractUser
from django.db import models


__all__ = ['User', 'Department']


class User(AbstractUser):
    pass


class Department(models.Model):
    name = models.CharField(max_length=128, verbose_name='部门名称')
    code = models.CharField(max_length=128, verbose_name='部门编号')
    leader = models.ForeignKey('User', on_delete=models.PROTECT, verbose_name='部门领导')

    class Meta:
        db_table = 'workflow_department'
        verbose_name = '部门'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name
