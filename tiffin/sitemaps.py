"""XML sitemap for crawlers. Only includes public, indexable pages."""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticPagesSitemap(Sitemap):
    changefreq = "daily"
    priority = 1.0
    protocol = "https"

    def items(self):
        return [
            ("home",  1.0, "daily"),
            ("menu",  0.9, "weekly"),
            ("order", 0.8, "monthly"),
        ]

    def location(self, item):
        return reverse(item[0])

    def priority(self, item):  # type: ignore[override]
        return item[1]

    def changefreq(self, item):  # type: ignore[override]
        return item[2]


SITEMAPS = {
    "static": StaticPagesSitemap,
}
