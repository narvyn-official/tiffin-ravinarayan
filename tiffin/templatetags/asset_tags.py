"""
{% asset 'css/styles.css' %} → /static/css/styles.css?v=<short hash of file mtime/size>

Cache-busts whenever the file changes, so the browser never serves a stale
cached copy after we update CSS or JS.
"""
import hashlib
import os

from django import template
from django.conf import settings
from django.contrib.staticfiles.finders import find as find_static
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def asset(path: str) -> str:
    url = static(path)
    abs_path = find_static(path)
    if abs_path and os.path.exists(abs_path):
        st = os.stat(abs_path)
        token = hashlib.md5(f"{st.st_mtime_ns}-{st.st_size}".encode()).hexdigest()[:10]
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}v={token}"
    return url
