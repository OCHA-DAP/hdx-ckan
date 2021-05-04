from flask import Blueprint
import ckan.plugins.toolkit as tk

render = tk.render
ValidationError = tk.ValidationError

hdx_colored_page = Blueprint(u'hdx_colored_page', __name__, url_prefix=u'/colored_page')


def read(category, title, color='fff'):
    color = color if color else 'FFFFFF'
    title = '' if title is None else title
    _validate(color)
    template_data = {
        'color': '#' + color,
        'title': title,
    }
    return render(u'colored_page/index.html', template_data)


def _validate(color):
    lower_color = color.lower()
    if len(lower_color) == 6 and '000000' <= lower_color <= 'ffffff':
        return True
    if len(lower_color) == 3 and '000' <= lower_color <= 'fff':
        return True

    raise ValidationError('Color format is incorrect')


hdx_colored_page.add_url_rule(u'/<category>/<title>', view_func=read)
hdx_colored_page.add_url_rule(u'/<category>/<title>/<color>', view_func=read)
