from django import template
import markdown

register = template.Library()

@register.filter(name='markdown')
def markdown_filter(value):
    """Convert markdown content to HTML"""
    return markdown.markdown(value, extensions=['extra', 'nl2br', 'sane_lists']) 