from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    print(f"Applying add_class filter to field: {field} with class: {css_class}")
    return field.as_widget(attrs={"class": css_class})
