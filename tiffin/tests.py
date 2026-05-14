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
        site.delivery_radius_km = 2
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
        site.delivery_radius_km = 2
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

    def test_monthly_lunch_or_dinner_uses_single_meal_price(self):
        plan = self.make_plan(
            slug="monthly",
            name="Monthly",
            category=Plan.Category.TIFFIN,
            price=3500,
            monthly_single_meal_price=1800,
            unit="per month",
        )
        form = OrderForm(data=self.form_data(
            plan,
            delivery_date=(date.today() + timedelta(days=1)).isoformat(),
            meal_time=Order.MealTime.DINNER,
        ))

        self.assertTrue(form.is_valid(), form.errors.as_text())
        order = form.save()
        self.assertEqual(order.plan_price, 1800)
        self.assertEqual(order.plan_subtotal, 1800)

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
