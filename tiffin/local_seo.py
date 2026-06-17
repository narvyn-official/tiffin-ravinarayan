"""Local SEO keyword clusters and service-area landing page copy."""

SEO_KEYWORDS = (
    "tiffin service, tiffin service near me, tiffin service in Metcity, "
    "tiffin service in Yakubpur, tiffin service in Jhajjar, homemade tiffin service, "
    "veg tiffin service, monthly tiffin service, daily tiffin service, "
    "lunch tiffin service, dinner tiffin service, PG tiffin service, "
    "office lunch tiffin, dabba service, ghar ka khana"
)

SITE_DESCRIPTION = (
    "Homemade veg tiffin service in Metcity, Yakubpur and Jhajjar. Daily tiffin "
    "₹80, monthly plans from ₹2000, lunch and dinner delivery, rice bowls and snacks. "
    "Order online."
)

GOOGLE_MAPS_URL = "https://www.google.com/maps?cid=16202019902653058804"

SERVICE_AREAS = {
    "metcity": {
        "name": "Metcity",
        "title": "Tiffin Service in Metcity | Homemade Veg Meals",
        "description": (
            "Order homemade veg tiffin service in Metcity. Daily tiffin ₹80, monthly "
            "lunch or dinner plans from ₹2000, rice bowls and group snacks."
        ),
        "headline": "Tiffin Service in Metcity",
        "intro": (
            "Fresh vegetarian tiffin for Metcity residents, PG students, office teams "
            "and working professionals who want dependable ghar ka khana without daily cooking."
        ),
        "detail": (
            "Choose Daily Tiffin for occasional lunch or dinner, the PG Monthly Plan for "
            "regular meals, or today's rice bowl when you need a quick homestyle option."
        ),
        "keyword_focus": [
            "tiffin service in Metcity",
            "tiffin service near me",
            "monthly tiffin service Metcity",
            "veg tiffin service Metcity",
        ],
    },
    "yakubpur": {
        "name": "Yakubpur",
        "title": "Tiffin Service in Yakubpur | Daily & Monthly Tiffin",
        "description": (
            "Fresh homemade tiffin service in Yakubpur, Haryana. Daily veg meals, "
            "monthly lunch/dinner plans, rice bowl and snacks from Ravinarayan Tiffin."
        ),
        "headline": "Tiffin Service in Yakubpur",
        "intro": (
            "Ravinarayan PG & Tiffin Services cooks from Yakubpur, making it easy to order "
            "fresh lunch, dinner, monthly tiffin and snacks from nearby homes, PGs and offices."
        ),
        "detail": (
            "Our pickup point is at 7A, Yakubpur, and delivery is available within the local "
            "4 km service zone. Orders are confirmed on WhatsApp with no online payment required."
        ),
        "keyword_focus": [
            "tiffin service in Yakubpur",
            "homemade tiffin Yakubpur",
            "daily tiffin Yakubpur",
            "PG tiffin service Yakubpur",
        ],
    },
    "jhajjar": {
        "name": "Jhajjar",
        "title": "Tiffin Service in Jhajjar | Veg Homemade Tiffin",
        "description": (
            "Looking for tiffin service in Jhajjar? Order homemade veg tiffin, lunch, dinner, "
            "monthly meal plans, rice bowls and group snacks online."
        ),
        "headline": "Tiffin Service in Jhajjar",
        "intro": (
            "For people searching for tiffin service near me in Jhajjar, we offer simple, "
            "homestyle vegetarian meals with daily, monthly and on-order food options."
        ),
        "detail": (
            "The menu focuses on roti, sabzi, dal, rice, salad, day-wise rice bowls and "
            "group snacks such as samosa, bread pakora and burger on advance order."
        ),
        "keyword_focus": [
            "tiffin service in Jhajjar",
            "tiffin service near me Jhajjar",
            "homemade tiffin service Jhajjar",
            "dabba service Jhajjar",
        ],
    },
}

SERVICE_AREA_SLUGS = tuple(SERVICE_AREAS.keys())
