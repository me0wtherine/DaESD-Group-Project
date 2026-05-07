"""
Seed the database with realistic Bristol-area demo data.

Usage:
    python manage.py seed_demo            # idempotent: adds anything missing
    python manage.py seed_demo --reset    # wipes demo data first

Demo product/producer images live in BRFoodNetwork/media/demo_images/.
See that folder's README.md for the file-naming convention.
"""
import os
import random
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Accounts, Producers, Admins
from accounts.geocoding import geocode_address
from products.models import Products, Reviews
from orders.models import Orders, OrderItem
from payments.models import Payments


# ----------------------------------------------------------------------
# Demo data definitions
# ----------------------------------------------------------------------

DEMO_PASSWORD = "Demo1234!"          # all demo accounts use this password
ADMIN_PASSWORD = "admin1234"         # global shared admin account
DEMO_TAG = "[demo]"                  # marker stored in description fields so --reset can find them


# Real Bristol-area postcodes (all within the 20-mile service radius)
PRODUCERS = [
    {
        "business_name": "Mendip Hill Farm",
        "email": "hello@mendiphill.demo",
        "address": "Hill Lane, Chew Stoke",
        "postal_code": "BS40 8XB",
        "phone_number": "01275 333111",
        "description": "Family-run organic vegetable farm at the foot of the Mendips.",
        "store_description": "Three generations of growers producing seasonal organic veg, free-range eggs and pasture-fed lamb.",
        "certifications": "Soil Association Organic",
        "delivery_available": True,
        "collection_available": True,
        "products": [
            {"name": "Carrots (1kg)",       "category": "vegetables", "price": "1.80", "unit": "per kg",      "stock": 80, "organic": True,  "allergens": ""},
            {"name": "Potatoes (2.5kg)",    "category": "vegetables", "price": "3.50", "unit": "per 2.5kg bag","stock": 50, "organic": True,  "allergens": ""},
            {"name": "Mixed Salad Leaves",  "category": "vegetables", "price": "2.20", "unit": "per 150g bag","stock": 30, "organic": True,  "allergens": "",
             "surplus": True, "surplus_price": "1.20"},
            {"name": "Free Range Eggs (dozen)", "category": "dairy",  "price": "4.50", "unit": "per dozen",   "stock": 24, "organic": False, "allergens": "egg"},
        ],
    },
    {
        "business_name": "Bristol Bake House",
        "email": "orders@bristolbakehouse.demo",
        "address": "12 Gloucester Road, Bristol",
        "postal_code": "BS7 8AE",
        "phone_number": "0117 4422 100",
        "description": "Wood-fired sourdough and pastries baked daily on Gloucester Road.",
        "store_description": "Slow-fermented sourdough, croissants and seasonal cakes, all baked on the premises.",
        "certifications": "Real Bread Campaign",
        "delivery_available": True,
        "collection_available": True,
        "products": [
            {"name": "Sourdough Loaf",      "category": "bakery", "price": "4.20", "unit": "each",      "stock": 40, "allergens": "gluten, wheat"},
            {"name": "Wholemeal Loaf",      "category": "bakery", "price": "4.00", "unit": "each",      "stock": 25, "allergens": "gluten, wheat"},
            {"name": "Pain au Chocolat (4)","category": "bakery", "price": "6.00", "unit": "pack of 4", "stock": 15, "allergens": "gluten, wheat, milk, egg"},
            {"name": "Day-Old Sourdough",   "category": "bakery", "price": "4.20", "unit": "each",      "stock": 8,  "allergens": "gluten, wheat",
             "surplus": True, "surplus_price": "2.00"},
        ],
    },
    {
        "business_name": "Severn Vale Dairy",
        "email": "shop@severnvale.demo",
        "address": "Marsh Lane, Easter Compton",
        "postal_code": "BS35 5RD",
        "phone_number": "01454 632100",
        "description": "Pasture-fed Jersey herd making award-winning cheese and butter.",
        "store_description": "Creamy whole milk, hand-rolled butter and a small range of soft and hard cheeses.",
        "certifications": "Pasture for Life",
        "delivery_available": True,
        "collection_available": False,
        "products": [
            {"name": "Whole Milk (1L)",     "category": "dairy", "price": "1.40", "unit": "per litre", "stock": 100, "allergens": "milk"},
            {"name": "Salted Butter (250g)","category": "dairy", "price": "3.20", "unit": "per 250g",  "stock": 35,  "allergens": "milk"},
            {"name": "Aged Cheddar (200g)", "category": "dairy", "price": "5.50", "unit": "per 200g",  "stock": 20,  "allergens": "milk"},
            {"name": "Greek-Style Yoghurt (500g)","category":"dairy","price":"3.00","unit":"per 500g","stock": 25, "allergens": "milk"},
        ],
    },
    {
        "business_name": "Avon Apple Orchard",
        "email": "info@avonapples.demo",
        "address": "Church Road, Wrington",
        "postal_code": "BS40 5LP",
        "phone_number": "01934 862255",
        "description": "Heritage apples, pears and pressed cider from a 12-acre orchard near Wrington.",
        "store_description": "Pick-your-own in season; cold-pressed juice and unpasteurised cider available year-round.",
        "certifications": "LEAF Marque",
        "delivery_available": False,
        "collection_available": True,
        "products": [
            {"name": "Cox Apples (1kg)",    "category": "fruits", "price": "2.80", "unit": "per kg",  "stock": 60, "allergens": ""},
            {"name": "Pressed Apple Juice", "category": "drinks", "price": "3.50", "unit": "per 750ml","stock": 40, "allergens": ""},
            {"name": "Bramley Cooking Apples (2kg)","category":"fruits","price":"4.20","unit":"per 2kg","stock": 18, "allergens":""},
        ],
    },
    {
        "business_name": "Chew Valley Honey",
        "email": "buzz@chewvalleyhoney.demo",
        "address": "Bath Road, Bishop Sutton",
        "postal_code": "BS39 5UU",
        "phone_number": "01275 333800",
        "description": "Raw, unblended honey from hives across the Chew Valley.",
        "store_description": "Single-apiary jars, beeswax candles and seasonal blossom honey.",
        "certifications": "",
        "delivery_available": True,
        "collection_available": True,
        "products": [
            {"name": "Wildflower Honey (340g)","category":"other","price":"7.50","unit":"per jar","stock": 30, "allergens": ""},
            {"name": "Beeswax Candle",         "category":"other","price":"6.00","unit":"each",  "stock": 12, "allergens": ""},
        ],
    },
]

CUSTOMERS = [
    # Individuals
    {"name": "Alice Walker",   "email": "alice.walker@demo.test",   "address": "21 Park Street",      "postal_code": "BS1 5JL", "phone": "07700 900111", "type": "individual"},
    {"name": "Ben Carter",     "email": "ben.carter@demo.test",     "address": "8 Whiteladies Road",  "postal_code": "BS8 2LX", "phone": "07700 900222", "type": "individual"},
    {"name": "Priya Patel",    "email": "priya.patel@demo.test",    "address": "15 Wells Road",       "postal_code": "BS4 2AG", "phone": "07700 900333", "type": "individual"},
    {"name": "Marcus Reid",    "email": "marcus.reid@demo.test",    "address": "44 Stoke Lane",       "postal_code": "BS9 3DW", "phone": "07700 900444", "type": "individual"},
    {"name": "Holly Tran",     "email": "holly.tran@demo.test",     "address": "9 Coronation Road",   "postal_code": "BS3 1AS", "phone": "07700 900555", "type": "individual"},
    # Restaurants
    {"name": "The Olive Branch Bistro",  "email": "kitchen@olivebranch.demo",  "address": "5 Clifton Down Road",  "postal_code": "BS8 4AL", "phone": "0117 222 3344", "type": "restaurant"},
    {"name": "Harbourside Tapas",        "email": "orders@harbourtapas.demo", "address": "Wapping Wharf",         "postal_code": "BS1 4RW", "phone": "0117 222 3355", "type": "restaurant"},
    # Community groups
    {"name": "Easton Community Kitchen", "email": "hello@eastonkitchen.demo", "address": "St Mark's Road",       "postal_code": "BS5 6JP", "phone": "0117 444 1100", "type": "community_group"},
    {"name": "Bedminster Food Bank",     "email": "contact@bedminsterfb.demo","address": "144 East Street",      "postal_code": "BS3 4EJ", "phone": "0117 444 1101", "type": "community_group"},
]

ADMINS = [
    {"name": "Demo Admin",   "email": "admin@brfn.demo",            "password": DEMO_PASSWORD},
    {"name": "BRFN Admin",   "email": "admin@brfoodnetwork.com",    "password": ADMIN_PASSWORD},
]

REVIEW_COMMENTS = [
    "Absolutely delicious — will be ordering again!",
    "Great quality and arrived really fresh.",
    "Excellent value for money, perfect for a family.",
    "Fantastic flavour, you can really taste the difference.",
    "Reliable delivery and beautifully packaged.",
    "Tastes just like it should — proper local food.",
]


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _slug(text):
    return ''.join(c if c.isalnum() else '-' for c in text.lower()).strip('-').replace('--', '-')


def _find_demo_image(slug):
    """Return a Path for the first matching image file, or None."""
    folder = Path(settings.MEDIA_ROOT) / 'demo_images'
    if not folder.exists():
        return None
    for ext in ('.jpg', '.jpeg', '.png', '.webp'):
        p = folder / f"{slug}{ext}"
        if p.exists():
            return p
    return None


def _attach_image(instance, field_name, slug):
    """Attach a demo image to an ImageField if found on disk. Idempotent."""
    if getattr(instance, field_name):
        return  # already has an image
    path = _find_demo_image(slug)
    if not path:
        return
    with open(path, 'rb') as f:
        getattr(instance, field_name).save(path.name, File(f), save=True)


# ----------------------------------------------------------------------
# Command
# ----------------------------------------------------------------------

class Command(BaseCommand):
    help = "Seed the database with realistic Bristol-area demo accounts, products and orders."

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing demo data before re-seeding.',
        )

    def handle(self, *args, **opts):
        if opts['reset']:
            self._reset()

        self.stdout.write(self.style.MIGRATE_HEADING('Seeding demo data…'))

        admins = self._seed_admins()
        producers = self._seed_producers()
        customers = self._seed_customers()
        products = self._seed_products(producers)
        orders = self._seed_orders(customers, products)
        self._seed_reviews(customers, products)

        self.stdout.write(self.style.SUCCESS(
            f"Done. Admins: {len(admins)}, Producers: {len(producers)}, "
            f"Customers: {len(customers)}, Products: {len(products)}, Orders: {len(orders)}"
        ))
        self.stdout.write("")
        self.stdout.write(self.style.WARNING(
            f"All demo accounts use password: {DEMO_PASSWORD}"
        ))
        self.stdout.write(self.style.WARNING(
            "Drop matching .jpg/.png files into BRFoodNetwork/media/demo_images/ to give products images. "
            "Re-run the command to attach them."
        ))

    # ------------------------------------------------------------------
    def _reset(self):
        self.stdout.write(self.style.WARNING("Wiping demo data…"))
        # Tagged producers and their cascade-deleted products / orders
        prod_emails = [p['email'] for p in PRODUCERS]
        cust_emails = [c['email'] for c in CUSTOMERS]
        admin_emails = [a['email'] for a in ADMINS]
        Producers.objects.filter(email__in=prod_emails).delete()
        Accounts.objects.filter(email__in=cust_emails).delete()
        Admins.objects.filter(email__in=admin_emails).delete()

    # ------------------------------------------------------------------
    def _seed_admins(self):
        created = []
        for a in ADMINS:
            obj, was_new = Admins.objects.get_or_create(
                email=a['email'],
                defaults={
                    'name': a['name'],
                    'password': make_password(a['password']),
                },
            )
            created.append(obj)
            if was_new:
                self.stdout.write(f"  + admin: {obj.email}")
        return created

    # ------------------------------------------------------------------
    def _seed_producers(self):
        created = []
        for p in PRODUCERS:
            obj, was_new = Producers.objects.get_or_create(
                email=p['email'],
                defaults={
                    'business_name': p['business_name'],
                    'description': p['description'],
                    'store_description': p['store_description'],
                    'password': make_password(DEMO_PASSWORD),
                    'address': p['address'],
                    'phone_number': p['phone_number'],
                    'postal_code': p['postal_code'],
                    'collection_available': p['collection_available'],
                    'delivery_available': p['delivery_available'],
                    'certifications': p['certifications'],
                    'is_active': True,
                    'opening_hours': [
                        {'day': d, 'open': '09:00', 'close': '17:00'}
                        for d in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
                    ],
                },
            )
            # Attach images if present
            slug = _slug(obj.business_name)
            _attach_image(obj, 'business_image', slug)
            _attach_image(obj, 'banner_image', f"{slug}-banner")
            # Geocode if missing so the producer shows on the map
            if obj.latitude is None or obj.longitude is None:
                lat, lng = geocode_address(obj.address, obj.postal_code)
                if lat is not None and lng is not None:
                    obj.latitude = lat
                    obj.longitude = lng
                    obj.save(update_fields=['latitude', 'longitude'])
            created.append(obj)
            if was_new:
                self.stdout.write(f"  + producer: {obj.business_name}")
        return created

    # ------------------------------------------------------------------
    def _seed_customers(self):
        created = []
        for c in CUSTOMERS:
            obj, was_new = Accounts.objects.get_or_create(
                email=c['email'],
                defaults={
                    'name': c['name'],
                    'password': make_password(DEMO_PASSWORD),
                    'address': c['address'],
                    'phone_number': c['phone'],
                    'postal_code': c['postal_code'],
                    'customer_type': c['type'],
                },
            )
            created.append(obj)
            if was_new:
                self.stdout.write(f"  + customer ({c['type']}): {obj.name}")
        return created

    # ------------------------------------------------------------------
    def _seed_products(self, producers_objs):
        created = []
        producer_by_email = {p.email: p for p in producers_objs}
        for definition in PRODUCERS:
            producer = producer_by_email.get(definition['email'])
            if not producer:
                continue
            for prod in definition['products']:
                obj, was_new = Products.objects.get_or_create(
                    producer=producer,
                    name=prod['name'],
                    defaults={
                        'category': prod['category'],
                        'description': f"{DEMO_TAG} {prod['name']} from {producer.business_name}.",
                        'price': Decimal(prod['price']),
                        'unit': prod['unit'],
                        'stock_quantity': prod['stock'],
                        'is_available': True,
                        'is_organic': prod.get('organic', False),
                        'allergens': prod.get('allergens', ''),
                        'is_surplus': prod.get('surplus', False),
                        'surplus_price': Decimal(prod['surplus_price']) if prod.get('surplus') else None,
                        'best_before': (timezone.now().date() + timedelta(days=3)) if prod.get('surplus') else None,
                    },
                )
                slug = _slug(obj.name)
                _attach_image(obj, 'image', slug)
                created.append(obj)
                if was_new:
                    self.stdout.write(f"    · product: {obj.name}")
        return created

    # ------------------------------------------------------------------
    def _seed_orders(self, customers_objs, products_objs):
        if not customers_objs or not products_objs:
            return []
        # Skip if we already have a healthy number of orders to avoid spamming
        existing_demo_orders = Orders.objects.filter(user__in=customers_objs).count()
        if existing_demo_orders >= 8:
            self.stdout.write(f"  (skipping orders — {existing_demo_orders} already exist)")
            return list(Orders.objects.filter(user__in=customers_objs))

        rng = random.Random(42)
        statuses = ['pending', 'confirmed', 'ready']
        orders = []
        for i in range(12):
            customer = rng.choice(customers_objs)
            num_items = rng.randint(1, 4)
            picked = rng.sample(products_objs, min(num_items, len(products_objs)))
            order = Orders.objects.create(
                user=customer,
                fulfillment_type=rng.choice(['delivery', 'collection']),
                delivery_address=customer.address,
                payment_method='card',
                order_status=rng.choice(statuses),
                total_price=Decimal('0'),
            )
            # Backdate for variety
            days_ago = rng.randint(0, 30)
            order.order_date = timezone.now() - timedelta(days=days_ago)
            order.save(update_fields=['order_date'])

            total = Decimal('0')
            producers_in_order = {}
            for product in picked:
                qty = rng.randint(1, 3)
                unit_price = product.surplus_price if product.is_surplus and product.surplus_price else product.price
                line_total = unit_price * qty
                OrderItem.objects.create(order=order, product=product, quantity=qty, price=unit_price)
                total += line_total
                producers_in_order.setdefault(product.producer, Decimal('0'))
                producers_in_order[product.producer] += line_total
            order.total_price = total
            order.save(update_fields=['total_price'])

            # Create matching Payments rows (5% commission split)
            commission_rate = Decimal('0.05')
            for prod, prod_total in producers_in_order.items():
                commission = (prod_total * commission_rate).quantize(Decimal('0.01'))
                Payments.objects.create(
                    order=order,
                    producer=prod,
                    network_commission=commission,
                    producer_payment=(prod_total - commission).quantize(Decimal('0.01')),
                )

            orders.append(order)
            self.stdout.write(f"    · order #{order.id} for {customer.name} (£{total})")
        return orders

    # ------------------------------------------------------------------
    def _seed_reviews(self, customers_objs, products_objs):
        rng = random.Random(7)
        # Add a couple of reviews per product, only on products that have been ordered
        ordered_product_ids = OrderItem.objects.values_list('product_id', flat=True).distinct()
        for product in products_objs:
            if product.id not in ordered_product_ids:
                continue
            if Reviews.objects.filter(product=product).count() >= 2:
                continue
            for _ in range(rng.randint(1, 2)):
                customer = rng.choice(customers_objs)
                if Reviews.objects.filter(product=product, customer=customer).exists():
                    continue
                Reviews.objects.create(
                    product=product,
                    customer=customer,
                    rating=rng.randint(4, 5),
                    comment=rng.choice(REVIEW_COMMENTS),
                )
