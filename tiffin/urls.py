from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("menu/", views.menu, name="menu"),
    path("order/", views.order, name="order"),
    path("review/", views.review_redirect, name="review_redirect"),
    path("tiffin-service-in-<slug:area_slug>/", views.location_page, name="location_page"),
    path("order/success/<str:code>/", views.order_success, name="order_success"),

    # SEO
    path("robots.txt", views.robots_txt, name="robots_txt"),
    path("sitemap.xml", views.sitemap_xml, name="sitemap"),

    # Custom auth (separate from /django-admin/ which has its own)
    path("admin-login/", views.admin_login, name="admin_login"),
    path("admin-logout/", views.admin_logout, name="admin_logout"),

    # Staff-only order dashboard
    path("admin-orders/", views.admin_orders, name="admin_orders"),
    path("admin-orders/<str:code>/status/", views.admin_update_status, name="admin_update_status"),
]
