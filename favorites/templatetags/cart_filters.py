from django import template
register = template.Library()
@register.filter(name='get_quantity')
def get_fav_quantity(fav, movie_id):
    return fav[str(movie_id)]