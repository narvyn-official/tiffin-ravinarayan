from datetime import date, datetime, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from .forms import OrderForm
from .geo import delivery_fee_for_distance
from .models import DeliveryArea, Order, Plan, SiteSettings


class DeliveryFeeTests(TestCase):
    def test_delivery_fee_uses_started_two_km_slabs_after_free_distance(self):
        self.assertEqual(delivery_fee_for_distance(None), 0)
        self.assertEqual(delivery_fee_for_distance(2), 0)
        self.assertEqual(delivery_fee_for_distance(2.01), 10)
        self.assertEqual(delivery_fee_for_distance(4), 10)
        self.assertEqual(delivery_fee_for_distance(4.01), 20)

    def test_order_form_adds_delivery_fee_to_total(self):
        site = SiteSettings.get()
        site.delivery_center_lat = 0
        site.delivery_center_lng = 0
        site.delivery_radius_km = 4
        site.pickup_enabled = True
        site.save()

        area = DeliveryArea.objects.create(name="Test Area", is_active=True)
        plan = Plan.objects.create(
            slug="test-daily",
            name="Test Daily",
            price=70,
            unit="per meal",
            items="Meal",
            is_active=True,
        )

        form = OrderForm(data={
            "delivery_method": Order.Method.DELIVERY,
            "full_name": "Test Customer",
            "phone": "9876543210",
            "address": "House 1, Test Street",
            "area": str(area.pk),
            "plan": str(plan.pk),
            "quantity": "1",
            "meal_time": Order.MealTime.LUNCH,
            "delivery_date": (date.today() + timedelta(days=1)).isoformat(),
            "location_url": "https://maps.google.com/?q=0.027000,0.000000",
        })

        self.assertTrue(form.is_valid(), form.errors.as_text())
        order = form.save()

        self.assertEqual(order.delivery_fee, 10)
        self.assertEqual(order.total_price, 80)
        self.assertAlmostEqual(float(order.delivery_distance_km), 3.0, places=1)


class OrderRuleTests(TestCase):
    def setUp(self):
        site = SiteSettings.get()
        site.delivery_center_lat = 0
        site.delivery_center_lng = 0
        site.delivery_radius_km = 4
        site.pickup_enabled = True
        site.save()
        self.area = DeliveryArea.objects.create(name="Test Area", is_active=True)

    def form_data(self, plan, **overrides):
        data = {
            "delivery_method": Order.Method.DELIVERY,
            "full_name": "Test Customer",
            "phone": "9876543210",
            "address": "House 1, Test Street",
            "area": str(self.area.pk),
            "plan": str(plan.pk),
            "quantity": "1",
            "meal_time": Order.MealTime.LUNCH,
            "delivery_date": date.today().isoformat(),
            "location_url": "https://maps.google.com/?q=0.010000,0.000000",
        }
        data.update(overrides)
        return data

    def make_plan(self, **overrides):
        values = {
            "slug": "test-plan",
            "name": "Test Plan",
            "price": 70,
            "unit": "per meal",
            "items": "Meal",
            "is_active": True,
        }
        values.update(overrides)
        return Plan.objects.create(**values)

    def test_same_day_lunch_tiffin_closes_after_1030(self):
        plan = self.make_plan(category=Plan.Category.TIFFIN)
        now = timezone.make_aware(datetime.combine(date.today(), datetime.strptime("10:31", "%H:%M").time()))

        with patch("tiffin.forms.timezone.localtime", return_value=now):
            form = OrderForm(data=self.form_data(plan, delivery_date=now.date().isoformat()))
            is_valid = form.is_valid()

        self.assertFalse(is_valid)
        self.assertIn("Lunch tiffin orders close at 10:30 AM.", form.errors["meal_time"])

    def test_same_day_after_lunch_cutoff_allows_only_dinner(self):
        plan = self.make_plan(category=Plan.Category.TIFFIN)
        now = timezone.make_aware(datetime.combine(date.today(), datetime.strptime("10:31", "%H:%M").time()))

        with patch("tiffin.forms.timezone.localtime", return_value=now):
            dinner_form = OrderForm(data=self.form_data(
                plan,
                delivery_date=now.date().isoformat(),
                meal_time=Order.MealTime.DINNER,
            ))
            both_form = OrderForm(data=self.form_data(
                plan,
                delivery_date=now.date().isoformat(),
                meal_time=Order.MealTime.BOTH,
            ))

            dinner_valid = dinner_form.is_valid()
            both_valid = both_form.is_valid()

        self.assertTrue(dinner_valid, dinner_form.errors.as_text())
        self.assertFalse(both_valid)
        self.assertIn("Lunch + Dinner tiffin orders close at 10:30 AM", both_form.errors["meal_time"][0])

    def test_delivery_is_rejected_beyond_four_km(self):
        plan = self.make_plan(category=Plan.Category.TIFFIN)
        form = OrderForm(data=self.form_data(
            plan,
            delivery_date=(date.today() + timedelta(days=1)).isoformat(),
            location_url="https://maps.google.com/?q=0.045000,0.000000",
        ))

        self.assertFalse(form.is_valid())
        self.assertIn("deliver only within 4 km", form.errors["location_url"][0])

    def test_monthly_lunch_or_dinner_uses_single_meal_price(self):
        plan = self.make_plan(
            slug="monthly",
            name="Monthly",
            category=Plan.Category.TIFFIN,
            price=3500,
            monthly_single_meal_price=2000,
            unit="per month",
        )
        form = OrderForm(data=self.form_data(
            plan,
            delivery_date=(date.today() + timedelta(days=1)).isoformat(),
            meal_time=Order.MealTime.DINNER,
        ))

        self.assertTrue(form.is_valid(), form.errors.as_text())
        order = form.save()
        self.assertEqual(order.plan_price, 2000)
        self.assertEqual(order.plan_subtotal, 2000)

    def test_rice_bowl_respects_day_and_order_window(self):
        today = date.today()
        plan = self.make_plan(
            slug="rice-bowl-test",
            name="Rice Bowl Test",
            category=Plan.Category.RICE_BOWL,
            price=60,
            unit="per bowl",
            available_day_of_week=today.weekday(),
        )
        now = timezone.make_aware(datetime.combine(today, datetime.strptime("12:00", "%H:%M").time()))

        with patch("tiffin.forms.timezone.localtime", return_value=now):
            form = OrderForm(data=self.form_data(plan, delivery_date=today.isoformat()))
            is_valid = form.is_valid()

        self.assertTrue(is_valid, form.errors.as_text())
        order = form.save()
        self.assertEqual(order.plan_price, 60)
        self.assertEqual(order.total_price, 60)

    def test_rice_bowl_closes_outside_9_to_9_window(self):
        today = date.today()
        plan = self.make_plan(
            slug="rice-bowl-late",
            name="Rice Bowl Late",
            category=Plan.Category.RICE_BOWL,
            price=60,
            unit="per bowl",
            available_day_of_week=today.weekday(),
        )
        now = timezone.make_aware(datetime.combine(today, datetime.strptime("21:01", "%H:%M").time()))

        with patch("tiffin.forms.timezone.localtime", return_value=now):
            form = OrderForm(data=self.form_data(plan, delivery_date=today.isoformat()))
            is_valid = form.is_valid()

        self.assertFalse(is_valid)
        self.assertIn("Rice bowl orders are open from 9:00 AM to 9:00 PM.", form.errors["plan"])

    def test_snacks_require_minimum_15_pieces_and_are_price_on_request(self):
        plan = self.make_plan(
            slug="samosa-test",
            name="Samosa",
            category=Plan.Category.SNACK,
            price=0,
            price_on_request=True,
            unit="price on request",
            min_quantity=15,
        )

        low_qty_form = OrderForm(data=self.form_data(plan, quantity="14"))
        self.assertFalse(low_qty_form.is_valid())
        self.assertIn("Samosa has a minimum order of 15 pcs.", low_qty_form.errors["quantity"])

        form = OrderForm(data=self.form_data(plan, quantity="15"))
        self.assertTrue(form.is_valid(), form.errors.as_text())
        order = form.save()
        self.assertTrue(order.plan_price_on_request)
        self.assertEqual(order.plan_price, 0)


class SeededBusinessDataTests(TestCase):
    def test_seeded_prices_and_local_seo_defaults_match_public_copy(self):
        site = SiteSettings.get()
        daily = Plan.objects.get(slug="daily-tiffin")
        monthly = Plan.objects.get(slug="pg-monthly")

        self.assertEqual(daily.price, 80)
        self.assertEqual(monthly.monthly_single_meal_price, 2000)
        self.assertIn("₹2000/month", monthly.items)
        self.assertIn("tiffin service in Metcity", site.seo_keywords)
        self.assertIn("tiffin service in Jhajjar", site.seo_keywords)
        self.assertIn("Daily tiffin ₹80", site.site_description)
        self.assertEqual(site.business_name, "Ravinarayan PG & Tiffin Services")
        self.assertEqual(site.address, "7A, Yakubpur, Jhajjar, Haryana 124103")
        self.assertEqual(site.postal_code, "124103")
        self.assertEqual(str(site.delivery_center_lat), "28.484427")
        self.assertEqual(str(site.delivery_center_lng), "76.784015")
        self.assertEqual(site.google_maps_url, "https://www.google.com/maps?cid=16202019902653058804")
        self.assertEqual(site.google_business_url, "https://share.google/kvPQQtTdyJ65cEiqi")

        active_areas = list(DeliveryArea.objects.filter(is_active=True).values_list("name", flat=True))
        self.assertEqual(active_areas, ["Metcity", "Yakubpur", "Jhajjar"])


class PublicSeoTests(TestCase):
    def test_public_pages_render_complete_local_seo_metadata(self):
        response = self.client.get("/")
        self.assertContains(response, '<html lang="en-IN">')
        self.assertContains(response, "<title>Tiffin Service in Metcity, Yakubpur &amp; Jhajjar</title>")
        self.assertContains(response, 'meta name="geo.region" content="IN-HR"')
        self.assertNotContains(response, 'hreflang="en-IN"')
        self.assertContains(response, '"@type":"WebSite"')
        self.assertContains(response, '"keywords":"tiffin service, tiffin service near me')
        self.assertContains(response, "Tiffin service in Metcity")
        self.assertContains(response, "Tiffin service in Yakubpur")
        self.assertContains(response, "Tiffin service in Jhajjar")
        self.assertContains(response, 'meta name="twitter:url" content="http://testserver/"')
        self.assertContains(response, 'meta name="twitter:domain" content="testserver"')
        self.assertContains(response, 'meta name="twitter:site" content="@ravinarayantiffin"')
        self.assertContains(response, 'meta name="twitter:creator" content="@ravinarayantiffin"')
        self.assertContains(response, 'meta property="og:image:type" content="image/png"')
        self.assertContains(response, "/static/img/hero.png")
        self.assertContains(response, 'meta property="og:image:width" content="1100"')
        self.assertContains(response, 'meta property="og:image:height" content="619"')
        self.assertContains(response, 'meta name="twitter:image:width" content="1100"')
        self.assertContains(response, 'meta name="twitter:image:height" content="619"')
        self.assertContains(response, "<h1>Tiffin Service in Metcity, Yakubpur &amp; Jhajjar — Fresh Homemade Meals Delivered Daily</h1>")
        self.assertNotContains(response, "<h4>")
        self.assertContains(response, "Lunch tiffin online order")
        self.assertContains(response, "Daily veg tiffin booking")
        self.assertContains(response, "Tiffin in Metcity")
        self.assertContains(response, 'href="/static/img/logo-small.png')
        self.assertContains(response, 'width="180" height="180"')
        self.assertContains(response, 'rel="preload" as="image" href="/static/img/hero.webp')
        self.assertNotContains(response, "fonts.googleapis.com")
        self.assertContains(response, 'width="1100" height="825"')
        self.assertContains(response, 'href="https://share.google/kvPQQtTdyJ65cEiqi"')
        self.assertNotContains(response, 'href="/review/"')

        order = self.client.get("/order/")
        self.assertContains(order, "<title>Order Tiffin Online in Metcity")
        self.assertContains(order, '<link rel="canonical" href="http://testserver/order/"')
        self.assertContains(order, '"@type":"BreadcrumbList"')
        self.assertContains(order, "<h2>Build your order</h2>")
        self.assertContains(order, '<h2 class="summary-title">Order summary</h2>')
        self.assertContains(order, 'alt="Samosa Snack order option from Ravinarayan Tiffin"')
        self.assertContains(order, 'fetchpriority="low"')
        self.assertNotContains(order, "<h4>")

        menu = self.client.get("/menu/")
        self.assertContains(menu, "<h2>Choose your tiffin plan</h2>")

    def test_location_pages_and_sitemap_are_indexable(self):
        for slug, area in [
            ("metcity", "Metcity"),
            ("yakubpur", "Yakubpur"),
            ("jhajjar", "Jhajjar"),
        ]:
            response = self.client.get(f"/tiffin-service-in-{slug}/")
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, f"Tiffin Service in {area}")
            self.assertContains(response, '"@type":"Service"')
            self.assertContains(response, f"tiffin service in {area}")
            self.assertContains(response, f'<link rel="canonical" href="http://testserver/tiffin-service-in-{slug}/"')

        sitemap = self.client.get("/sitemap.xml")
        self.assertEqual(sitemap.status_code, 200)
        self.assertEqual(sitemap["Content-Type"], "application/xml")
        self.assertNotIn("X-Robots-Tag", sitemap.headers)
        self.assertContains(sitemap, "https://testserver/tiffin-service-in-metcity/")
        self.assertContains(sitemap, "https://testserver/tiffin-service-in-yakubpur/")
        self.assertContains(sitemap, "https://testserver/tiffin-service-in-jhajjar/")

        robots_head = self.client.head("/robots.txt")
        self.assertEqual(robots_head.status_code, 200)

    def test_review_redirect_uses_google_profile_url(self):
        response = self.client.get("/review/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://share.google/kvPQQtTdyJ65cEiqi")
