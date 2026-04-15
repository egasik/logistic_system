from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Умножение двух чисел в шаблоне"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0