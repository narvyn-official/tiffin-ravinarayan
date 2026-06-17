"""
Seed data for first-time setup. Used by the data migration.
Owners can edit everything in /django-admin/ after seeding.
"""

DEFAULT_AREAS = ["Metcity", "Yakubpur", "Jhajjar"]

DEFAULT_PLANS = [
    {
        "slug": "regular-veg",
        "name": "Regular Veg Tiffin",
        "tagline": "Everyday homestyle meal",
        "price": 80,
        "unit": "per meal",
        "items": "4 Roti\nSabzi\nDal\nRice\nSalad",
        "badge": "Most Popular",
        "sort_order": 1,
    },
    {
        "slug": "premium-veg",
        "name": "Premium Veg Tiffin",
        "tagline": "Bigger portions, paneer or special sabzi",
        "price": 120,
        "unit": "per meal",
        "items": "5 Roti\nPaneer / Special Sabzi\nDal Tadka\nJeera Rice\nSalad\nSweet",
        "badge": "Chef's Pick",
        "sort_order": 2,
    },
    {
        "slug": "office-lunch",
        "name": "Office Lunch Tiffin",
        "tagline": "Light, balanced, delivered to your desk",
        "price": 90,
        "unit": "per meal",
        "items": "3 Roti\nSabzi\nDal\nRice\nCurd\nPickle",
        "badge": "",
        "sort_order": 3,
    },
    {
        "slug": "pg-monthly",
        "name": "PG Monthly Tiffin",
        "tagline": "Lunch + Dinner, 30 days, big savings",
        "price": 3500,
        "unit": "per month",
        "items": "Lunch + Dinner daily\nRoti, Sabzi, Dal, Rice\nWeekly menu rotation\n1 special meal / week\nLunch-only or dinner-only: ₹2000/month",
        "badge": "Best Value",
        "sort_order": 4,
    },
    {
        "slug": "corporate-bulk",
        "name": "Corporate / Bulk Tiffin",
        "tagline": "10+ tiffins, custom menus, on-time delivery",
        "price": 75,
        "unit": "per meal (10+ qty)",
        "items": "Bulk pricing\nCustom menu options\nScheduled daily delivery\nGST invoice on request",
        "badge": "",
        "sort_order": 5,
    },
]

DEFAULT_ADDONS = [
    {"name": "Extra Chapati", "description": "1 piece, soft & fresh", "price": 8, "unit": "per piece", "icon": "🫓", "sort_order": 1},
    {"name": "Curd", "description": "Fresh, set in earthen pot", "price": 30, "unit": "200 ml", "icon": "🥣", "sort_order": 2},
    {"name": "Raita", "description": "Cucumber & boondi raita", "price": 35, "unit": "200 ml", "icon": "🥗", "sort_order": 3},
    {"name": "Sweet of the Day", "description": "Gulab jamun, halwa, or kheer", "price": 40, "unit": "1 portion", "icon": "🍮", "sort_order": 4},
    {"name": "Lassi", "description": "Sweet, chilled", "price": 50, "unit": "300 ml", "icon": "🥛", "sort_order": 5},
    {"name": "Buttermilk (Chaas)", "description": "Light, masala-spiced", "price": 25, "unit": "300 ml", "icon": "🧉", "sort_order": 6},
    {"name": "Papad", "description": "Roasted, crisp", "price": 10, "unit": "2 pieces", "icon": "🍘", "sort_order": 7},
    {"name": "Pickle Pack", "description": "Mango / lemon", "price": 15, "unit": "small portion", "icon": "🌶", "sort_order": 8},
    {"name": "Paneer Sabzi Upgrade", "description": "Swap dal for paneer sabzi", "price": 40, "unit": "1 portion", "icon": "🧀", "sort_order": 9},
    {"name": "Extra Rice", "description": "Steamed", "price": 20, "unit": "1 portion", "icon": "🍚", "sort_order": 10},
]

# Day-of-week (0=Mon … 6=Sun) × meal_time
DEFAULT_DAILY_MENU = [
    (0, "lunch",  "Aloo Gobi\nDal Fry\nJeera Rice\n4 Roti\nSalad\nPickle"),
    (0, "dinner", "Mix Veg\nDal Tadka\nSteamed Rice\n4 Roti\nCurd\nSweet"),
    (1, "lunch",  "Bhindi Masala\nMoong Dal\nRice\n4 Roti\nSalad\nPapad"),
    (1, "dinner", "Paneer Bhurji\nDal Makhani\nJeera Rice\n4 Roti\nCurd"),
    (2, "lunch",  "Cabbage Sabzi\nToor Dal\nRice\n4 Roti\nSalad\nPickle"),
    (2, "dinner", "Aloo Matar\nDal Tadka\nSteamed Rice\n4 Roti\nRaita"),
    (3, "lunch",  "Lauki Chana\nMix Dal\nJeera Rice\n4 Roti\nSalad"),
    (3, "dinner", "Tinda Sabzi\nDal Fry\nRice\n4 Roti\nSweet"),
    (4, "lunch",  "Baingan Bharta\nDal\nJeera Rice\n4 Roti\nSalad\nPickle"),
    (4, "dinner", "Gawar Sabzi\nDal Tadka\nRice\n4 Roti\nCurd"),
    (5, "lunch",  "Special: Paneer Butter Masala\nDal Makhani\nJeera Rice\n4 Roti\nSalad"),
    (5, "dinner", "Veg Pulao\nDal Tadka\nRaita\n2 Roti\nSweet"),
    (6, "lunch",  "Chole\nBhature / Roti\nJeera Rice\nSalad\nSweet"),
    (6, "dinner", "Veg Biryani\nDal\nRaita\nPapad"),
]
