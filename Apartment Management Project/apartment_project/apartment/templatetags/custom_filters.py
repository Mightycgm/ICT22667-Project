from django import template

register = template.Library()

@register.filter
def enumerate(value):
    # ใช้กับ list → คืนค่า (index, item)
    return list(__builtins__['enumerate'](value)) if isinstance(__builtins__, dict) \
           else list(__builtins__.enumerate(value) if hasattr(__builtins__, 'enumerate') \
           else zip(range(len(value)), value))