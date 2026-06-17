"""XML sitemap for crawlers. Only includes public, indexable pages."""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .local_seo import SERVICE_AREA_SLUGS


class StaticPagesSitemap(Sitemap):
    changefreq = "daily"
    priority = 1.0
    protocol = "https"

    def items(self):
        pages = [
            ("home",  1.0, "daily"),
            ("menu",  0.9, "weekly"),
            ("order", 0.8, "monthly"),
        ]
        pages.extend((("location_page", slug), 0.9, "weekly") for slug in SERVICE_AREA_SLUGS)
        return pages

    def location(self, item):
        if isinstance(item[0], tuple):
            return reverse(item[0][0], args=[item[0][1]])
        return reverse(item[0])

    def priority(self, item):  # type: ignore[override]
        return item[1]

    def changefreq(self, item):  # type: ignore[override]
        return item[2]


SITEMAPS = {
    "static": StaticPagesSitemap,
}
