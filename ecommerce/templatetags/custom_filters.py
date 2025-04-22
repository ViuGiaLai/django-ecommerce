from django import template

register = template.Library()

@register.filter
def get_attr(obj, attr):
    """Get attribute value dynamically."""
    return getattr(obj, attr, 0)

@register.filter
def widthratio(value, arg):
    """Calculate percentage ratio."""
    try:
        return (value / arg) * 100
    except ZeroDivisionError:
        return 0

@register.filter
def replace(value, arg):
    old, new = arg.split(',')
    return value.replace(old, new)
