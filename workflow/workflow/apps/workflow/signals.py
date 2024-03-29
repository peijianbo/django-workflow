
from django.dispatch import receiver, Signal
from django.db.models.signals import post_save, pre_save

"""====================信号定义==================="""
node_approved = Signal()
node_rejected = Signal()


"""====================信号捕获==================="""


@receiver(node_approved)
def on_node_approved(sender, instance, **kwargs):
    # 发送邮件给申请者
    print('发送邮件给申请者:你的审批已经通过了xxx的审批', instance.event.requester.email)
    # 发送邮件提醒给下一级审批者
    # 更改工作流事件状态


@receiver(node_rejected)
def on_node_rejected(sender, instance, **kwargs):
    pass
