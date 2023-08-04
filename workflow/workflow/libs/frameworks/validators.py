import keyword

from django.core.exceptions import ValidationError


def is_identifier(value):
    """验证value是否可以作为python变量名"""
    if not value.isidentifier() or keyword.iskeyword(value):
        raise ValidationError(message='字段名称不合法')


def is_choice_format(value):
    """验证value是否符合格式：['字符串']"""
    if not isinstance(value, list):
        raise ValidationError(message='数据格式错误，要求为列表')
    # for v in value:
    #     if not isinstance(v, str):
    #         raise ValidationError(message='列表的元素格式错误，要求为字符串')
