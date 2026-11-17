import pytest
from markupsafe import Markup

import ckan.plugins.toolkit as tk

from ckanext.hdx_theme.helpers.helpers import markdown_extract_strip


def _render(app, template, **kwargs):
    flask_app = app.flask_app
    with flask_app.test_request_context('/'):
        return flask_app.jinja_env.from_string(template).render(**kwargs)


@pytest.mark.usefixtures('app')
class TestMarkdownExtract(object):

    def test_helper_returns_unescaped_plain_str(self):
        result = tk.h.markdown_extract('Food Security & Nutrition <2024>')
        assert result == 'Food Security & Nutrition <2024>'
        assert not isinstance(result, Markup)

    def test_empty_text(self):
        assert tk.h.markdown_extract(None) == ''
        assert tk.h.markdown_extract('') == ''

    def test_truncation_still_applied(self):
        text = 'Food & Nutrition ' * 30
        assert tk.h.markdown_extract(text, 50).endswith('...')
        assert tk.h.markdown_extract(text, extract_length=50).endswith('...')
        assert len(tk.h.markdown_extract(text, extract_length=0)) > 400

    def test_special_chars_escaped_once_with_urlize(self, app):
        output = _render(app, '<div>{{ h.markdown_extract(v)|urlize }}</div>',
                         v='Food Security & Nutrition <2024>')
        assert output == '<div>Food Security &amp; Nutrition &lt;2024&gt;</div>'

    def test_urlize_link_keeps_query_string(self, app):
        output = _render(app, '{{ h.markdown_extract(v)|urlize }}', v='See https://data.humdata.org/?a=1&b=2')
        assert 'href="https://data.humdata.org/?a=1&amp;b=2"' in output
        assert '&amp;amp;' not in output

    def test_script_tag_still_stripped(self, app):
        output = _render(app, '{{ h.markdown_extract(v)|urlize }}', v='before <script>alert(1)</script> after')
        assert '<script' not in output
        assert 'alert(1)' not in output
        assert 'before' in output and 'after' in output

    def test_encoded_tag_is_not_rendered_as_html(self, app):
        output = _render(app, '{{ h.markdown_extract(v)|urlize }}', v='&lt;script&gt;alert(1)&lt;/script&gt;')
        assert '<script' not in output
        assert '&lt;script&gt;' in output

    def test_quotes_escaped_inside_attribute(self, app):
        output = _render(app, '<a title="{{ h.markdown_extract(v) }}"></a>', v='a" onmouseover="alert(1)')
        assert output == '<a title="a&#34; onmouseover=&#34;alert(1)"></a>'

    def test_markdown_extract_strip_unchanged(self):
        # used for the metadata downloads; it calls core's markdown_extract directly
        assert markdown_extract_strip('Food & "Nutrition"') == 'Food &amp; &quot;Nutrition&quot;'
