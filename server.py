#!/usr/bin/env python3
"""
Simple delivery service website using Python's built‑in HTTP server.

This server implements a minimal e‑commerce style site that allows
customers to browse products, add them to a cart, and place an order.
The site supports three languages (French, English and Arabic) and
shows prices in Tunisian dinar (TND). A lightweight SQLite database
stores product information and orders. Payment processing is only a
placeholder form; no real transactions occur.

To run the site, execute this script from within the ``delivery_site``
directory. Then visit ``http://localhost:8000`` in your browser. The
default language is French; you can switch languages via the links in
the navigation bar.
"""

import http.server
import os
import sqlite3
import urllib.parse
import uuid
from http import cookies
import smtplib
from datetime import datetime
import csv
import base64  # for embedding payment icons
import os

# Path definitions relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
DB_PATH = os.path.join(BASE_DIR, "data.db")

# Simple translation dictionary. Each key maps to a translation in
# French (fr), English (en) and Arabic (ar). The values are plain
# strings without HTML.
translations = {
    # Add friendly emojis to navigation labels for a more engaging look
    'nav_home': {
        'fr': '🏠 Accueil',
        'en': '🏠 Home',
        'ar': '🏠 الصفحة الرئيسية',
    },
    'nav_products': {
        'fr': '🛍️ Produits',
        'en': '🛍️ Products',
        'ar': '🛍️ منتجات',
    },
    'nav_cart': {
        'fr': '🛒 Panier',
        'en': '🛒 Cart',
        'ar': '🛒 عربة التسوق',
    },
    'nav_language': {
        # Display only the globe icon without additional text to declutter the header
        'fr': '🌐',
        'en': '🌐',
        'ar': '🌐',
    },
    'site_title': {
        # Company name shown in the header/navigation. This has been updated
        # from "Theelja Delivery" to "Theelja Store" based on the provided logo and
        # branding materials.
        'fr': 'Theelja Store',
        'en': 'Theelja Store',
        # Correct Arabic transliteration of the company name. Arabic text is right‑to‑left
        'ar': 'ثالجة ستور',
    },
    'welcome_message': {
        # Add a delivery truck emoji to make the welcome message more engaging
        'fr': 'Bienvenue sur notre service de livraison 🚚 !',
        'en': 'Welcome to our delivery service 🚚!',
        'ar': 'مرحبًا بكم في خدمة التوصيل الخاصة بنا 🚚!',
    },
    'intro_text': {
        'fr': 'Parcourez nos produits et faites‑les livrer rapidement à votre porte.',
        'en': 'Browse our products and get them delivered to your door quickly.',
        'ar': 'تصفح منتجاتنا واحصل على توصيلها إلى باب منزلك بسرعة.',
    },
    'product_list_title': {
        'fr': 'Nos produits',
        'en': 'Our Products',
        'ar': 'منتجاتنا',
    },
    'add_to_cart': {
        # Append a cart emoji to the add‑to‑cart button to make it more visual
        'fr': 'Ajouter au panier 🛒',
        'en': 'Add to cart 🛒',
        'ar': 'أضف إلى السلة 🛒',
    },
    'cart_title': {
        'fr': 'Votre panier',
        'en': 'Your Cart',
        'ar': 'عربة التسوق الخاصة بك',
    },
    'product_name': {
        'fr': 'Produit',
        'en': 'Product',
        'ar': 'المنتج',
    },
    'quantity': {
        'fr': 'Quantité',
        'en': 'Quantity',
        'ar': 'الكمية',
    },
    'price': {
        'fr': 'Prix',
        'en': 'Price',
        'ar': 'السعر',
    },
    'total': {
        'fr': 'Total',
        'en': 'Total',
        'ar': 'المجموع',
    },
    'checkout_button': {
        # Include an emoji to emphasise the checkout action
        'fr': '🧾 Passer à la caisse',
        'en': '🧾 Proceed to checkout',
        'ar': '🧾 الانتقال إلى الدفع',
    },
    'empty_cart': {
        'fr': 'Votre panier est vide.',
        'en': 'Your cart is empty.',
        'ar': 'سلة التسوق فارغة.',
    },
    'checkout_title': {
        'fr': 'Informations sur la commande',
        'en': 'Order Information',
        'ar': 'معلومات الطلب',
    },
    'name_label': {
        'fr': 'Nom complet',
        'en': 'Full name',
        'ar': 'الاسم الكامل',
    },
    'address_label': {
        'fr': 'Adresse de livraison',
        'en': 'Delivery address',
        'ar': 'عنوان التوصيل',
    },
    'card_number_label': {
        'fr': 'Numéro de carte',
        'en': 'Card number',
        'ar': 'رقم البطاقة',
    },
    'place_order_button': {
        'fr': 'Passer la commande',
        'en': 'Place order',
        'ar': 'إتمام الطلب',
    },

    # Label shown in checkout when paying by card, indicating where to integrate a payment API
    'payment_api_label': {
        'fr': 'Intégration de paiement (API)',
        'en': 'Payment API integration',
        'ar': 'دمج بوابة الدفع (API)',
    },

    # Footer and newsletter translations
    'newsletter_signup': {
        'fr': 'Inscrivez‑vous pour recevoir nos offres et actualités',
        'en': 'Sign up for the latest deals and news',
        'ar': 'اشترك للحصول على أحدث العروض والأخبار',
    },
    'email_placeholder': {
        'fr': 'Votre e‑mail',
        'en': 'Your e‑mail',
        'ar': 'بريدك الإلكتروني',
    },
    'footer_category_title': {
        'fr': 'Catégories',
        'en': 'Categories',
        'ar': 'الفئات',
    },
    'footer_support_title': {
        'fr': 'Support',
        'en': 'Support',
        'ar': 'الدعم',
    },
    'footer_info_title': {
        'fr': 'Informations',
        'en': 'Info',
        'ar': 'معلومات',
    },
    'cat_pizza': {
        'fr': 'Pizzas',
        'en': 'Pizzas',
        'ar': 'بيتزا',
    },
    'cat_sandwich': {
        'fr': 'Sandwichs',
        'en': 'Sandwiches',
        'ar': 'شطائر',
    },
    'cat_salad': {
        'fr': 'Salades',
        'en': 'Salads',
        'ar': 'سلطات',
    },
    'cat_dessert': {
        'fr': 'Desserts',
        'en': 'Desserts',
        'ar': 'حلويات',
    },
    'support_faq': {
        'fr': 'FAQ',
        'en': 'FAQ',
        'ar': 'الأسئلة الشائعة',
    },
    'support_contact': {
        'fr': 'Contact',
        'en': 'Contact',
        'ar': 'اتصل بنا',
    },
    'support_delivery': {
        'fr': 'Infos livraison',
        'en': 'Delivery info',
        'ar': 'معلومات التوصيل',
    },
    'info_privacy': {
        'fr': 'Politique de confidentialité',
        'en': 'Privacy policy',
        'ar': 'سياسة الخصوصية',
    },
    'info_terms': {
        'fr': 'Conditions générales',
        'en': 'Terms & Conditions',
        'ar': 'الشروط والأحكام',
    },

    # Generic category placeholders (1, 2, 3) for footer; can be renamed later
    'category_1': {
        'fr': 'Catégorie 1',
        'en': 'Category 1',
        'ar': 'الفئة 1',
    },
    'category_2': {
        'fr': 'Catégorie 2',
        'en': 'Category 2',
        'ar': 'الفئة 2',
    },
    'category_3': {
        'fr': 'Catégorie 3',
        'en': 'Category 3',
        'ar': 'الفئة 3',
    },

    # Directional arrow for newsletter submit button; reversed for Arabic (RTL)
    'newsletter_submit_icon': {
        'fr': '➔',
        'en': '➔',
        'ar': '←',
    },

    # Static page titles and contents
    'privacy_title': {
        'fr': 'Politique de confidentialité',
        'en': 'Privacy Policy',
        'ar': 'سياسة الخصوصية',
    },
    'privacy_html': {
        'fr': '<p>Nous respectons votre vie privée. Nous ne collectons que les informations nécessaires pour traiter vos commandes et assurer la livraison de vos produits. Vos données ne sont pas partagées avec des tiers, sauf lorsque la loi l\'exige ou pour l\'accomplissement de la livraison.</p><p>En utilisant notre site, vous consentez à la collecte et à l\'utilisation de vos données personnelles telles que décrites ici.</p>',
        'en': '<p>We respect your privacy. We collect only the personal information needed to process your orders and deliver your products. Your data is not shared with third parties, except when required by law or to complete delivery.</p><p>By using our site, you consent to the collection and use of your personal data as described herein.</p>',
        'ar': '<p>نحن نحترم خصوصيتك. لا نجمع إلا المعلومات الشخصية اللازمة لمعالجة طلباتك وتوصيل منتجاتك. لا تتم مشاركة بياناتك مع جهات خارجية إلا إذا تطلب القانون ذلك أو لإكمال عملية التوصيل.</p><p>باستخدامك لموقعنا، فإنك توافق على جمع واستخدام بياناتك الشخصية كما هو موضح هنا.</p>',
    },
    'terms_title': {
        'fr': 'Conditions générales',
        'en': 'Terms and Conditions',
        'ar': 'الشروط والأحكام',
    },
    'terms_html': {
        'fr': '<p>Les présentes conditions régissent l\'achat et la livraison de produits de Theelja Store. En passant commande, vous acceptez ces conditions.</p><p>Les livraisons sont disponibles dans toute la Tunisie. Le paiement peut se faire par carte ou en espèces à la livraison. Les commandes sont traitées dès la réception du paiement ou de la confirmation.</p><p>Theelja Store se réserve le droit de refuser ou d\'annuler toute commande, y compris en cas de suspicion de fraude ou de non‑respect des présentes conditions. Les produits sont vendus « tels quels » et nous déclinons toute responsabilité pour les dommages indirects ou consécutifs. En cas de litige, les tribunaux de Tunis sont seuls compétents.</p><p>Nous nous réservons le droit de modifier ces conditions à tout moment. Les conditions en vigueur seront affichées sur cette page.</p>',
        'en': '<p>These terms govern the purchase and delivery of products from Theelja Store. By placing an order, you accept these terms.</p><p>Deliveries are available throughout Tunisia. Payment can be made by card or cash on delivery. Orders are processed upon receipt of payment or confirmation.</p><p>Theelja Store reserves the right to refuse or cancel any order, including in cases of suspected fraud or breach of these terms. Products are sold \"as is\" and we assume no liability for indirect or consequential damages. In the event of a dispute, the courts of Tunis shall have exclusive jurisdiction.</p><p>We reserve the right to modify these terms at any time. The current terms will be displayed on this page.</p>',
        'ar': '<p>تحكم هذه الشروط شراء وتوصيل المنتجات من متجر ثالجة. عند تقديم الطلب، فإنك تقبل هذه الشروط.</p><p>التوصيل متاح في جميع أنحاء تونس. يمكن الدفع ببطاقة الائتمان أو نقداً عند التسليم. تتم معالجة الطلبات عند استلام الدفع أو التأكيد.</p><p>يحتفظ متجر ثالجة بالحق في رفض أو إلغاء أي طلب، بما في ذلك في حالات الاشتباه في الاحتيال أو انتهاك هذه الشروط. تُباع المنتجات \"كما هي\" ولا نتحمل أي مسؤولية عن الأضرار غير المباشرة أو التبعية. في حالة النزاع، تكون محاكم تونس هي المختصة حصرياً.</p><p>نحتفظ بالحق في تعديل هذه الشروط في أي وقت. سيتم عرض الشروط الحالية في هذه الصفحة.</p>',
    },
    'faq_title': {
        'fr': 'FAQ',
        'en': 'FAQ',
        'ar': 'الأسئلة الشائعة',
    },
    'faq_html': {
        'fr': '<ul><li><strong>Comment passer une commande ?</strong> Rendez‑vous sur la page Produits, ajoutez des articles à votre panier et validez votre commande.</li><li><strong>Quels modes de paiement acceptez‑vous ?</strong> Nous acceptons actuellement le paiement à la livraison et les principales cartes bancaires (Visa, MasterCard et American Express).</li><li><strong>Où livrez‑vous ?</strong> Nous livrons dans toutes les régions de Tunisie.</li><li><strong>Combien de temps prend la livraison ?</strong> La plupart des commandes sont livrées en 24–48 heures.</li></ul>',
        'en': '<ul><li><strong>How do I place an order?</strong> Navigate to the Products page, add items to your cart and proceed to checkout.</li><li><strong>What payment methods are accepted?</strong> We currently accept cash on delivery and major credit cards (Visa, MasterCard and American Express).</li><li><strong>Where do you deliver?</strong> We deliver to all regions of Tunisia.</li><li><strong>How long does delivery take?</strong> Most orders are delivered within 24–48 hours.</li></ul>',
        'ar': '<ul><li><strong>كيف يمكنني تقديم طلب؟</strong> انتقل إلى صفحة المنتجات، أضف العناصر إلى سلة التسوق الخاصة بك ثم تابع الدفع.</li><li><strong>ما هي طرق الدفع المقبولة؟</strong> نقبل حالياً الدفع نقداً عند التسليم وبطاقات الائتمان الرئيسية (فيزا، ماستركارد وأمريكان إكسبريس).</li><li><strong>أين يتم التوصيل؟</strong> نقوم بالتوصيل إلى جميع مناطق تونس.</li><li><strong>كم يستغرق التوصيل؟</strong> يتم توصيل معظم الطلبات خلال 24–48 ساعة.</li></ul>',
    },
    'contact_title': {
        'fr': 'Contact',
        'en': 'Contact',
        'ar': 'اتصل بنا',
    },
    'contact_html': {
        'fr': '<p>Pour toute question ou assistance, veuillez nous contacter :</p><p>Téléphone : +216 55417232</p><p>E‑mail : [en cours de configuration]</p>',
        'en': '<p>For any questions or support, please contact us:</p><p>Phone: +216 55417232</p><p>Email: [to be configured]</p>',
        'ar': '<p>لأي استفسارات أو دعم، يرجى الاتصال بنا:</p><p>الهاتف: +216 55417232</p><p>البريد الإلكتروني: [سيتم تفعيله لاحقاً]</p>',
    },
    'delivery_title': {
        'fr': 'Infos livraison',
        'en': 'Delivery Info',
        'ar': 'معلومات التوصيل',
    },
    'delivery_html': {
        'fr': '<p>Nous livrons dans toutes les régions de Tunisie. Les commandes sont traitées quotidiennement et expédiées sous 24 heures.</p><p>Les délais de livraison varient entre 24 et 48 heures selon votre localisation. Des frais de livraison peuvent s\'appliquer en fonction de la distance et du montant de la commande.</p>',
        'en': '<p>We deliver to all regions of Tunisia. Orders are processed daily and shipped within 24 hours.</p><p>Delivery times vary between 24 and 48 hours depending on your location. Delivery fees may apply based on distance and order value.</p>',
        'ar': '<p>نقوم بالتوصيل إلى جميع مناطق تونس. تتم معالجة الطلبات يومياً ويتم شحنها في غضون 24 ساعة.</p><p>تتراوح مدة التوصيل بين 24 و48 ساعة حسب موقعك. قد يتم تطبيق رسوم توصيل بناءً على المسافة وقيمة الطلب.</p>',
    },
    'order_confirmation_title': {
        'fr': 'Confirmation de commande',
        'en': 'Order confirmation',
        'ar': 'تأكيد الطلب',
    },
    'order_success_message': {
        'fr': 'Votre commande a été passée avec succès.',
        'en': 'Your order has been placed successfully.',
        'ar': 'تم تقديم طلبك بنجاح.',
    },
    'back_home': {
        'fr': 'Retour à l\'accueil',
        'en': 'Back to home',
        'ar': 'العودة إلى الصفحة الرئيسية',
    },

    # New translations for enhanced checkout
    'email_label': {
        'fr': 'Adresse e‑mail',
        'en': 'Email address',
        'ar': 'البريد الإلكتروني',
    },
    'phone_label': {
        'fr': 'Numéro de téléphone',
        'en': 'Phone number',
        'ar': 'رقم الهاتف',
    },
    'payment_method_label': {
        'fr': 'Méthode de paiement',
        'en': 'Payment method',
        'ar': 'طريقة الدفع',
    },
    'payment_option_card': {
        'fr': 'Carte de crédit',
        'en': 'Credit card',
        'ar': 'بطاقة ائتمان',
    },
    'payment_option_cash': {
        'fr': 'Paiement à la livraison',
        'en': 'Cash on delivery',
        'ar': 'الدفع عند التسليم',
    },

    # Message shown when a product is added to the cart
    'item_added_message': {
        # Add a check mark emoji to reinforce the action feedback
        'fr': '✅ Produit ajouté à votre panier.',
        'en': '✅ Item added to your cart.',
        'ar': '✅ تم إضافة المنتج إلى سلة التسوق الخاصة بك.',
    },

    # Email related translations
    'email_subject': {
        'fr': 'Confirmation de votre commande',
        'en': 'Your order confirmation',
        'ar': 'تأكيد طلبك',
    },
    'email_body_intro': {
        'fr': 'Bonjour {name},\n\nMerci pour votre commande. Voici les détails de votre commande :',
        'en': 'Hello {name},\n\nThank you for your order. Here are the details of your purchase:',
        'ar': 'مرحبًا {name},\n\nشكرًا لك على طلبك. فيما يلي تفاصيل الطلب:',
    },
    'email_body_total': {
        'fr': 'Total : {total} TND',
        'en': 'Total: {total} TND',
        'ar': 'المجموع: {total} د.ت',
    },
    'email_body_thanks': {
        'fr': '\n\nNous vous remercions de votre confiance et espérons vous revoir bientôt.',
        'en': '\n\nWe appreciate your business and hope to see you again soon.',
        'ar': '\n\nنشكرك على ثقتك ونأمل أن نراك مرة أخرى قريبًا.',
    },

    # Link back to product listing from a single product page
    'back_to_products': {
        'fr': 'Retour aux produits',
        'en': 'Back to products',
        'ar': 'العودة إلى المنتجات',
    },

    # Placeholder text for the search bar
    'search_placeholder': {
        # Include a magnifying glass emoji to hint the search functionality
        'fr': '🔍 Rechercher...',
        'en': '🔍 Search...',
        'ar': '🔍 بحث...'
    },

    # Featured products section heading on the home page
    'featured_products': {
        # Add sparkles to highlight featured products section
        'fr': '✨ Produits en vedette',
        'en': '✨ Featured Products',
        'ar': '✨ منتجات مميزة',
    },
}

# -----------------------------------------------------------------
# Payment icon embedding
#
# To ensure payment icons display correctly across all browsers and
# languages, we embed the SVG files as base64 data URIs at server
# startup. This avoids potential MIME type issues and broken links.
def _load_icon_base64(filename: str) -> str:
    """Read an icon file from the static directory and return a base64 string."""
    try:
        icon_path = os.path.join(STATIC_DIR, 'icons', filename)
        with open(icon_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception:
        return ''

# Preload the icons. These constants are used when rendering
# templates. If the files are missing or unreadable, the strings will
# be empty which gracefully falls back to no image.
VISA_ICON_B64 = _load_icon_base64('visa.svg')
MASTERCARD_ICON_B64 = _load_icon_base64('mastercard.svg')
AMEX_ICON_B64 = _load_icon_base64('amex.svg')


def translate(key: str, lang: str) -> str:
    """Return the translation for the given key and language.

    If the key or language is not found, falls back to French and
    ultimately returns the key itself.
    """
    return translations.get(key, {}).get(lang) or translations.get(key, {}).get('fr') or key


def render_template(template_name: str, context: dict) -> str:
    """Render an HTML template by substituting placeholders.

    Placeholders in templates should be wrapped in double curly braces,
    for example ``{{title}}``. This function performs a simple
    replacement without any control structures.
    """
    template_path = os.path.join(TEMPLATE_DIR, template_name)
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Replace each key with its string representation
    for key, value in context.items():
        content = content.replace('{{' + key + '}}', str(value))
    return content


def init_db():
    """Initialize the SQLite database with tables and seed data.

    Creates tables ``product``, ``orders`` and ``order_items`` if they
    do not exist. If the product table is empty, inserts a few sample
    products with names and descriptions in the supported languages.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Create product table with multi‑lingual fields
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS product (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_fr TEXT NOT NULL,
            name_en TEXT NOT NULL,
            name_ar TEXT NOT NULL,
            description_fr TEXT NOT NULL,
            description_en TEXT NOT NULL,
            description_ar TEXT NOT NULL,
            price REAL NOT NULL,
            image_filename TEXT
        );
        """
    )
    # Ensure product table has image_filename column (for older DB versions)
    cur.execute("PRAGMA table_info(product)")
    prod_columns = [row[1] for row in cur.fetchall()]
    if 'image_filename' not in prod_columns:
        cur.execute("ALTER TABLE product ADD COLUMN image_filename TEXT")
    # Create orders table. Additional fields (phone, payment_method, email) are
    # optional; card_number may be NULL if payment method is cash.
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_address TEXT NOT NULL,
            card_number TEXT,
            total REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            customer_phone TEXT,
            payment_method TEXT,
            customer_email TEXT
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(product_id) REFERENCES product(id)
        );
        """
    )
    # Ensure orders table has all required columns in case of older database versions
    cur.execute("PRAGMA table_info(orders)")
    existing_columns = [row[1] for row in cur.fetchall()]
    for col_name, col_type in [
        ('customer_phone', 'TEXT'),
        ('payment_method', 'TEXT'),
        ('customer_email', 'TEXT'),
        # ensure card_number column exists as TEXT (used to be NOT NULL)
        ('card_number', 'TEXT'),
    ]:
        if col_name not in existing_columns:
            cur.execute(f"ALTER TABLE orders ADD COLUMN {col_name} {col_type}")
    # Check if products already exist
    cur.execute("SELECT COUNT(*) FROM product")
    count = cur.fetchone()[0]
    if count == 0:
        # Seed sample products; values correspond to (fr, en, ar, price)
        sample_products = [
            (
                'Pizza Margherita',
                'Margherita Pizza',
                'بيتزا مارغريتا',
                'Délicieuse pizza classique avec tomates, fromage et basilic.',
                'Delicious classic pizza with tomatoes, cheese and basil.',
                'بيتزا كلاسيكية لذيذة مع الطماطم والجبن والريحان.',
                15.0,
                'pizza.png',
            ),
            (
                'Sandwich au poulet',
                'Chicken Sandwich',
                'ساندويتش دجاج',
                'Sandwich savoureux avec poulet grillé et légumes frais.',
                'Tasty sandwich with grilled chicken and fresh vegetables.',
                'ساندويتش لذيذ مع الدجاج المشوي والخضروات الطازجة.',
                8.5,
                'sandwich.png',
            ),
            (
                'Salade César',
                'Caesar Salad',
                'سلطة سيزر',
                'Salade verte croquante avec sauce César et croûtons.',
                'Crunchy green salad with Caesar dressing and croutons.',
                'سلطة خضراء مقرمشة مع صلصة سيزر وقطع خبز محمص.',
                7.0,
                'salad.png',
            ),
            (
                'Tarte au chocolat',
                'Chocolate Tart',
                'فطيرة الشوكولاتة',
                'Tarte gourmande au chocolat noir et crème.',
                'Indulgent tart with dark chocolate and cream.',
                'فطيرة شهية بالشوكولاتة الداكنة والكريمة.',
                5.5,
                'dessert.png',
            ),
        ]
        cur.executemany(
            """
            INSERT INTO product (
                name_fr, name_en, name_ar,
                description_fr, description_en, description_ar,
                price, image_filename
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            sample_products,
        )
        conn.commit()
    conn.close()


class SessionManager:
    """Simple in‑memory session store.

    Each session is identified by a UUID stored in a cookie named
    ``session_id``. Session data is a dictionary that holds the
    customer's shopping cart and language preference. Because this
    program runs in a single process, storing sessions in memory is
    sufficient for demonstration purposes. In a real application, you
    would use a persistent session store.
    """
    def __init__(self):
        self._sessions = {}

    def get_session(self, handler):
        """Retrieve the session for the current request.

        If no session exists, a new one is created and a cookie is
        sent to the client. Returns a dictionary representing the
        session data.
        """
        session_id = None
        cookie_header = handler.headers.get('Cookie')
        if cookie_header:
            c = cookies.SimpleCookie(cookie_header)
            if 'session_id' in c:
                session_id = c['session_id'].value
        if not session_id or session_id not in self._sessions:
            # create new session
            session_id = str(uuid.uuid4())
            # Start a new session with Arabic as the default language so the site loads in Arabic for new visitors
            self._sessions[session_id] = {'cart': [], 'lang': 'ar'}
            # set cookie in header later by handler; here store id
            handler._new_session_id = session_id
        return self._sessions[session_id]

    def persist_cookie(self, handler):
        """If a new session was created, send a Set‑Cookie header."""
        session_id = getattr(handler, '_new_session_id', None)
        if session_id:
            handler.send_header('Set-Cookie', f'session_id={session_id}; Path=/; SameSite=Lax')


session_manager = SessionManager()


class DeliveryRequestHandler(http.server.BaseHTTPRequestHandler):
    """Custom request handler for the delivery service web application."""

    def do_GET(self):
        # Parse URL and query parameters
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)
        # Retrieve session and language
        session = session_manager.get_session(self)
        lang = params.get('lang', [session.get('lang', 'ar')])[0]
        # Update language in session
        session['lang'] = lang

        # Serve static files
        if path.startswith('/static/'):
            return self.serve_static(path)

        if path == '/' or path == '':
            return self.render_home(session)
        elif path == '/products':
            return self.render_products(session, params)
        elif path == '/product':
            return self.render_product_detail(session, params)
        elif path == '/add_to_cart':
            return self.handle_add_to_cart(session, params)
        elif path == '/update_cart':
            return self.handle_update_cart(session, params)
        elif path == '/cart':
            return self.render_cart(session)
        elif path == '/checkout':
            return self.render_checkout(session)
        elif path == '/confirmation':
            # We don't pass order_id; session holds last order id or skip
            return self.render_confirmation(session)
        # Static informational pages
        elif path == '/privacy':
            return self.render_static_page(session, 'privacy')
        elif path == '/terms':
            return self.render_static_page(session, 'terms')
        elif path == '/faq':
            return self.render_static_page(session, 'faq')
        elif path == '/contact':
            return self.render_static_page(session, 'contact')
        elif path == '/delivery':
            return self.render_static_page(session, 'delivery')
        else:
            return self.send_error(404, 'Not Found')

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        # Only checkout is a POST endpoint
        if path == '/checkout':
            return self.handle_checkout_post()
        else:
            return self.send_error(404, 'Not Found')

    # Helper: serve static files (images, css)
    def serve_static(self, path: str):
        # Remove /static/ prefix
        rel_path = path[len('/static/'):]
        file_path = os.path.join(STATIC_DIR, rel_path)
        if not os.path.abspath(file_path).startswith(os.path.abspath(STATIC_DIR)) or not os.path.isfile(file_path):
            return self.send_error(404, 'Static file not found')
        # Determine MIME type
        if file_path.endswith('.css'):
            content_type = 'text/css'
        elif file_path.endswith('.png'):
            content_type = 'image/png'
        elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
            content_type = 'image/jpeg'
        elif file_path.endswith('.svg'):
            content_type = 'image/svg+xml'
        elif file_path.endswith('.js'):
            content_type = 'application/javascript'
        else:
            content_type = 'application/octet-stream'
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            self.send_response(200)
            session_manager.persist_cookie(self)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            # Instruct browsers to cache static assets for one year to improve performance.
            # When assets change, their filenames or contents will also change (e.g. via
            # updated hashes), so long caching is safe here.
            self.send_header('Cache-Control', 'public, max-age=31536000')
            self.end_headers()
            self.wfile.write(data)
        except FileNotFoundError:
            return self.send_error(404, 'Static file not found')

    # -----------------------------------------------------------------
    # Static content pages
    #
    # The following helper renders static informational pages such as
    # privacy policy, terms & conditions, FAQ, contact and delivery
    # information. Each page's title and HTML content is defined in
    # the translations dictionary using keys ending with `_title` and
    # `_html`. For example, ``privacy`` maps to ``privacy_title`` and
    # ``privacy_html``. This helper builds a context and delegates
    # rendering to the ``static.html`` template wrapped in the base
    # layout. Pages are accessible via their slug (e.g. /privacy).
    def render_static_page(self, session, slug: str):
        lang = session['lang']
        # Determine translation keys for title and html content
        title_key = f"{slug}_title"
        html_key = f"{slug}_html"
        # Lookup translations; fallback handled in translate()
        page_title = translate(title_key, lang)
        page_html = translate(html_key, lang)
        # Build context common to all pages
        context = {
            'lang': lang,
            'site_title': translate('site_title', lang),
            'nav_home': translate('nav_home', lang),
            'nav_products': translate('nav_products', lang),
            'nav_cart': translate('nav_cart', lang),
            'nav_language': translate('nav_language', lang),
            'cart_count': len(session.get('cart', [])),
            'search_placeholder': translate('search_placeholder', lang),
            'newsletter_signup': translate('newsletter_signup', lang),
            'email_placeholder': translate('email_placeholder', lang),
            'footer_category_title': translate('footer_category_title', lang),
            'footer_support_title': translate('footer_support_title', lang),
            'footer_info_title': translate('footer_info_title', lang),
            'cat_pizza': translate('cat_pizza', lang),
            'cat_sandwich': translate('cat_sandwich', lang),
            'cat_salad': translate('cat_salad', lang),
            'cat_dessert': translate('cat_dessert', lang),
            'support_faq': translate('support_faq', lang),
            'support_contact': translate('support_contact', lang),
            'support_delivery': translate('support_delivery', lang),
            'info_privacy': translate('info_privacy', lang),
            'info_terms': translate('info_terms', lang),
            'category_1': translate('category_1', lang),
            'category_2': translate('category_2', lang),
            'category_3': translate('category_3', lang),
            'newsletter_submit_icon': translate('newsletter_submit_icon', lang),
            'dir': 'rtl' if lang == 'ar' else 'ltr',
            'page_title': page_title,
            'page_html': page_html,
        }
        # Render the static page content
        page_content = render_template('static.html', context)
        context['content'] = page_content
        html = render_template('base.html', context)
        self.send_response(200)
        session_manager.persist_cookie(self)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(html.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def render_home(self, session):
        lang = session['lang']
        # Build list of featured products (first 3 products) to display on home page
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        name_col = f'name_{lang}' if lang in ['fr', 'en', 'ar'] else 'name_fr'
        desc_col = f'description_{lang}' if lang in ['fr', 'en', 'ar'] else 'description_fr'
        cur.execute(f"SELECT id, {name_col}, {desc_col}, price, image_filename FROM product LIMIT 3")
        featured_products = cur.fetchall()
        conn.close()
        featured_items = []
        for pid, name, description, price, image_filename in featured_products:
            detail_link = f"/product?product_id={pid}&lang={lang}"
            item_html = (
                "<div class='product-item featured-item'>\n"
                f"  <a href='{detail_link}' class='product-link'>\n"
                f"    <img src='/static/images/{image_filename}' alt='{name}' class='product-image' loading='lazy' />\n"
                f"    <h2>{name}</h2>\n"
                "  </a>\n"
                f"  <p class='description'>{description}</p>\n"
                f"  <p class='price'>{translate('price', lang)}: {price:.2f} TND</p>\n"
                f"  <a class='button' href='/add_to_cart?product_id={pid}&lang={lang}'>{translate('add_to_cart', lang)}</a>\n"
                "</div>\n"
            )
            featured_items.append(item_html)
        featured_html = "\n".join(featured_items)
        context = {
            'lang': lang,
            'site_title': translate('site_title', lang),
            'nav_home': translate('nav_home', lang),
            'nav_products': translate('nav_products', lang),
            'nav_cart': translate('nav_cart', lang),
            'nav_language': translate('nav_language', lang),
            'welcome_message': translate('welcome_message', lang),
            'intro_text': translate('intro_text', lang),
            'button_products': translate('nav_products', lang),
            'cart_count': len(session.get('cart', [])),
            'featured_title': translate('featured_products', lang),
            'featured_html': featured_html,
            'search_placeholder': translate('search_placeholder', lang),
            # Set text direction based on the selected language
            'dir': 'rtl' if lang == 'ar' else 'ltr',
            # Footer translations
            'newsletter_signup': translate('newsletter_signup', lang),
            'email_placeholder': translate('email_placeholder', lang),
            'footer_category_title': translate('footer_category_title', lang),
            'footer_support_title': translate('footer_support_title', lang),
            'footer_info_title': translate('footer_info_title', lang),
            'cat_pizza': translate('cat_pizza', lang),
            'cat_sandwich': translate('cat_sandwich', lang),
            'cat_salad': translate('cat_salad', lang),
            'cat_dessert': translate('cat_dessert', lang),
            'support_faq': translate('support_faq', lang),
            'support_contact': translate('support_contact', lang),
            'support_delivery': translate('support_delivery', lang),
            'info_privacy': translate('info_privacy', lang),
            'info_terms': translate('info_terms', lang),
            'category_1': translate('category_1', lang),
            'category_2': translate('category_2', lang),
            'category_3': translate('category_3', lang),
            'newsletter_submit_icon': translate('newsletter_submit_icon', lang),
        }

        # Insert payment icons into context for footer
        context.update({
            'visa_icon': VISA_ICON_B64,
            'mastercard_icon': MASTERCARD_ICON_B64,
            'amex_icon': AMEX_ICON_B64,
        })

        # Add payment icons for footer
        context.update({
            'visa_icon': VISA_ICON_B64,
            'mastercard_icon': MASTERCARD_ICON_B64,
            'amex_icon': AMEX_ICON_B64,
        })

        # Provide payment icons for footer
        context.update({
            'visa_icon': VISA_ICON_B64,
            'mastercard_icon': MASTERCARD_ICON_B64,
            'amex_icon': AMEX_ICON_B64,
        })

        # Insert base64 encoded payment icons into the context. Using data URIs
        # ensures that the logos render correctly even if the browser has
        # trouble loading external SVGs.
        context.update({
            'visa_icon': VISA_ICON_B64,
            'mastercard_icon': MASTERCARD_ICON_B64,
            'amex_icon': AMEX_ICON_B64,
        })
        # Render index page with featured products
        index_html = render_template('index.html', context)
        context['content'] = index_html
        html = render_template('base.html', context)
        self.send_response(200)
        session_manager.persist_cookie(self)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(html.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def render_products(self, session, params):
        lang = session['lang']
        # Query products from DB, optionally filtering by a search term
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        # Select appropriate name and description columns based on language
        name_col = f'name_{lang}' if lang in ['fr', 'en', 'ar'] else 'name_fr'
        desc_col = f'description_{lang}' if lang in ['fr', 'en', 'ar'] else 'description_fr'
        search_term_list = params.get('search')
        if search_term_list:
            search_term = f"%{search_term_list[0]}%"
            cur.execute(f"SELECT id, {name_col}, {desc_col}, price, image_filename FROM product WHERE {name_col} LIKE ? COLLATE NOCASE", (search_term,))
        else:
            cur.execute(f"SELECT id, {name_col}, {desc_col}, price, image_filename FROM product")
        products = cur.fetchall()
        conn.close()
        # Build HTML for products. Each product links to its own detail page.
        product_items = []
        for pid, name, description, price, image_filename in products:
            # Each product card shows an image and name that link to the product detail page
            detail_link = f"/product?product_id={pid}&lang={lang}"
            item_html = (
                "<div class='product-item'>\n"
                f"  <a href='{detail_link}' class='product-link'>\n"
                f"    <img src='/static/images/{image_filename}' alt='{name}' class='product-image' loading='lazy' />\n"
                f"    <h2>{name}</h2>\n"
                "  </a>\n"
                f"  <p class='description'>{description}</p>\n"
                f"  <p class='price'>{translate('price', lang)}: {price:.2f} TND</p>\n"
                f"  <a class='button' href='/add_to_cart?product_id={pid}&lang={lang}'>{translate('add_to_cart', lang)}</a>\n"
                "</div>\n"
            )
            product_items.append(item_html)
        products_html = "\n".join(product_items)
        # Determine if an item was recently added to the cart
        added_html = ''
        if 'added' in params:
            added_html = f"<div class='added-message'>{translate('item_added_message', lang)}</div>"

        # Determine if the cart should appear as an overlay (when item just added)
        open_cart = 'open_cart' in params

        # Build a sidebar summary of the current cart to display on the products page
        cart = session.get('cart', [])
        sidebar_html = "<aside class='cart-sidebar'>"
        sidebar_html += f"<h3>{translate('cart_title', lang)}</h3>"
        if not cart:
            # Empty cart message
            sidebar_html += f"<p>{translate('empty_cart', lang)}</p>"
        else:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            name_col = f'name_{lang}' if lang in ['fr', 'en', 'ar'] else 'name_fr'
            sidebar_html += "<ul>"
            total_amount = 0.0
            for item in cart:
                cur.execute(f"SELECT {name_col}, price FROM product WHERE id = ?", (item['product_id'],))
                row = cur.fetchone()
                if not row:
                    continue
                name, price = row
                quantity = item['quantity']
                item_total = price * quantity
                total_amount += item_total
                # Each list item shows quantity, name and subtotal
                sidebar_html += (
                    f"<li>{quantity} × {name} — {item_total:.2f} TND</li>"
                )
            sidebar_html += "</ul>"
            sidebar_html += f"<p class='total'><strong>{translate('total', lang)}:</strong> {total_amount:.2f} TND</p>"
            # Link to the cart page
            sidebar_html += f"<a href='/cart?lang={lang}' class='checkout-button'>{translate('checkout_button', lang)}</a>"
            conn.close()
        sidebar_html += "</aside>"

        # Build cart overlay (visible only when there are items in the cart). When an item is just added,
        # the ``open_cart`` flag will cause it to slide in via the CSS class ``open``.
        if not cart:
            overlay_html = ''
        else:
            # Always open the cart overlay when there are items; the open_cart flag ensures
            # it opens immediately after an addition as well. This prevents the overlay
            # from covering the header when closed.
            open_cart_flag = True  # show overlay whenever cart has items
            overlay_class = 'cart-overlay open' if open_cart_flag else 'cart-overlay'
            overlay_html = f"<div class='{overlay_class}'>"
            # Add a close button so the user can hide the overlay without clearing the cart
            overlay_html += "<button class='cart-close' aria-label='Close'>&times;</button>"
            overlay_html += f"<h3>{translate('cart_title', lang)}</h3>"
            overlay_html += "<ul>"
            total_amount_overlay = 0.0
            # Re-query product names and prices for each cart item
            conn_o = sqlite3.connect(DB_PATH)
            cur_o = conn_o.cursor()
            name_col_o = name_col
            for item in cart:
                cur_o.execute(f"SELECT {name_col_o}, price FROM product WHERE id = ?", (item['product_id'],))
                row_o = cur_o.fetchone()
                if not row_o:
                    continue
                name_o, price_o = row_o
                quantity_o = item['quantity']
                item_total_o = price_o * quantity_o
                total_amount_overlay += item_total_o
                # Controls to modify quantity and remove items
                overlay_html += (
                    f"<li>"
                    f"{quantity_o} × {name_o} — {item_total_o:.2f} TND "
                    # Assign distinct classes for each cart action so they can be styled differently
                    f"<a href='/update_cart?product_id={item['product_id']}&action=increase&lang={lang}&open_cart=1' class='cart-action cart-action-increase'>➕</a> "
                    f"<a href='/update_cart?product_id={item['product_id']}&action=decrease&lang={lang}&open_cart=1' class='cart-action cart-action-decrease'>➖</a> "
                    f"<a href='/update_cart?product_id={item['product_id']}&action=remove&lang={lang}&open_cart=1' class='cart-action cart-action-remove'>🗑️</a>"
                    f"</li>"
                )
            conn_o.close()
            overlay_html += "</ul>"
            overlay_html += f"<p class='total'><strong>{translate('total', lang)}:</strong> {total_amount_overlay:.2f} TND</p>"
            overlay_html += f"<a href='/cart?lang={lang}' class='checkout-button'>{translate('checkout_button', lang)}</a>"
            overlay_html += "</div>"

        context = {
            'lang': lang,
            'site_title': translate('site_title', lang),
            'nav_home': translate('nav_home', lang),
            'nav_products': translate('nav_products', lang),
            'nav_cart': translate('nav_cart', lang),
            'nav_language': translate('nav_language', lang),
            'product_list_title': translate('product_list_title', lang),
            'products_html': products_html,
            'added_html': added_html,
            'cart_count': len(cart),
            'cart_sidebar_html': '',
            'cart_overlay_html': overlay_html,
            'search_placeholder': translate('search_placeholder', lang),
            'dir': 'rtl' if lang == 'ar' else 'ltr',
            # Footer translations
            'newsletter_signup': translate('newsletter_signup', lang),
            'email_placeholder': translate('email_placeholder', lang),
            'footer_category_title': translate('footer_category_title', lang),
            'footer_support_title': translate('footer_support_title', lang),
            'footer_info_title': translate('footer_info_title', lang),
            'cat_pizza': translate('cat_pizza', lang),
            'cat_sandwich': translate('cat_sandwich', lang),
            'cat_salad': translate('cat_salad', lang),
            'cat_dessert': translate('cat_dessert', lang),
            'support_faq': translate('support_faq', lang),
            'support_contact': translate('support_contact', lang),
            'support_delivery': translate('support_delivery', lang),
            'info_privacy': translate('info_privacy', lang),
            'info_terms': translate('info_terms', lang),
            'category_1': translate('category_1', lang),
            'category_2': translate('category_2', lang),
            'category_3': translate('category_3', lang),
            'newsletter_submit_icon': translate('newsletter_submit_icon', lang),
        }
        products_page = render_template('products.html', context)
        context['content'] = products_page
        html = render_template('base.html', context)
        self.send_response(200)
        session_manager.persist_cookie(self)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(html.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def handle_add_to_cart(self, session, params):
        lang = session['lang']
        product_id_list = params.get('product_id')
        if not product_id_list:
            return self.send_error(400, 'Missing product_id')
        try:
            product_id = int(product_id_list[0])
        except ValueError:
            return self.send_error(400, 'Invalid product_id')
        # Add product to cart (increment quantity if already present)
        cart = session.setdefault('cart', [])
        for item in cart:
            if item['product_id'] == product_id:
                item['quantity'] += 1
                break
        else:
            cart.append({'product_id': product_id, 'quantity': 1})
        # Redirect back to products page with flags indicating an item was added and the cart should open
        self.send_response(302)
        session_manager.persist_cookie(self)
        self.send_header('Location', f'/products?lang={lang}&added=1&open_cart=1')
        self.end_headers()

    def render_cart(self, session):
        lang = session['lang']
        cart = session.get('cart', [])
        if not cart:
            cart_html = f"<p>{translate('empty_cart', lang)}</p>"
            total_amount = 0.0
        else:
            # Query product details for each item
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            name_col = f'name_{lang}' if lang in ['fr', 'en', 'ar'] else 'name_fr'
            rows = []
            total_amount = 0.0
            for item in cart:
                cur.execute(f"SELECT {name_col}, price FROM product WHERE id = ?", (item['product_id'],))
                row = cur.fetchone()
                if row:
                    name, price = row
                    quantity = item['quantity']
                    item_total = price * quantity
                    total_amount += item_total
                    rows.append((name, quantity, price, item_total))
            conn.close()
            # Build HTML table rows
            row_html_list = []
            for name, quantity, price, item_total in rows:
                row_html_list.append(
                    f"<tr><td>{name}</td><td>{quantity}</td><td>{price:.2f} TND</td><td>{item_total:.2f} TND</td></tr>"
                )
            rows_html = "\n".join(row_html_list)
            cart_html = (
                "<table class='cart-table'>\n"
                f"<tr><th>{translate('product_name', lang)}</th><th>{translate('quantity', lang)}</th>"
                f"<th>{translate('price', lang)}</th><th>{translate('total', lang)}</th></tr>\n"
                f"{rows_html}\n"
                f"<tr><td colspan='3'><strong>{translate('total', lang)}</strong></td>"
                f"<td><strong>{total_amount:.2f} TND</strong></td></tr>\n"
                "</table>\n"
                f"<a class='button' href='/checkout?lang={lang}'>{translate('checkout_button', lang)}</a>"
            )
        context = {
            'lang': lang,
            'site_title': translate('site_title', lang),
            'nav_home': translate('nav_home', lang),
            'nav_products': translate('nav_products', lang),
            'nav_cart': translate('nav_cart', lang),
            'nav_language': translate('nav_language', lang),
            'cart_title': translate('cart_title', lang),
            'cart_content': cart_html,
            'cart_count': len(session.get('cart', [])),
            'search_placeholder': translate('search_placeholder', lang),
            'dir': 'rtl' if lang == 'ar' else 'ltr',
            # Footer translations
            'newsletter_signup': translate('newsletter_signup', lang),
            'email_placeholder': translate('email_placeholder', lang),
            'footer_category_title': translate('footer_category_title', lang),
            'footer_support_title': translate('footer_support_title', lang),
            'footer_info_title': translate('footer_info_title', lang),
            'cat_pizza': translate('cat_pizza', lang),
            'cat_sandwich': translate('cat_sandwich', lang),
            'cat_salad': translate('cat_salad', lang),
            'cat_dessert': translate('cat_dessert', lang),
            'support_faq': translate('support_faq', lang),
            'support_contact': translate('support_contact', lang),
            'support_delivery': translate('support_delivery', lang),
            'info_privacy': translate('info_privacy', lang),
            'info_terms': translate('info_terms', lang),
            'category_1': translate('category_1', lang),
            'category_2': translate('category_2', lang),
            'category_3': translate('category_3', lang),
            'newsletter_submit_icon': translate('newsletter_submit_icon', lang),
        }

        context.update({
            'visa_icon': VISA_ICON_B64,
            'mastercard_icon': MASTERCARD_ICON_B64,
            'amex_icon': AMEX_ICON_B64,
        })
        cart_page = render_template('cart.html', context)
        context['content'] = cart_page
        html = render_template('base.html', context)
        self.send_response(200)
        session_manager.persist_cookie(self)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(html.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def render_product_detail(self, session, params):
        """Render a single product detail page.

        Expects a 'product_id' query parameter. Displays the product's
        image, name, full description and price along with an "add to
        cart" button. Provides a link back to the product listing.
        """
        lang = session['lang']
        product_id_list = params.get('product_id')
        if not product_id_list:
            return self.send_error(400, 'Missing product_id')
        try:
            product_id = int(product_id_list[0])
        except ValueError:
            return self.send_error(400, 'Invalid product_id')
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        name_col = f'name_{lang}' if lang in ['fr', 'en', 'ar'] else 'name_fr'
        desc_col = f'description_{lang}' if lang in ['fr', 'en', 'ar'] else 'description_fr'
        cur.execute(f"SELECT {name_col}, {desc_col}, price, image_filename FROM product WHERE id = ?", (product_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return self.send_error(404, 'Product not found')
        name, description, price, image_filename = row
        context = {
            'lang': lang,
            'site_title': translate('site_title', lang),
            'nav_home': translate('nav_home', lang),
            'nav_products': translate('nav_products', lang),
            'nav_cart': translate('nav_cart', lang),
            'nav_language': translate('nav_language', lang),
            'cart_count': len(session.get('cart', [])),
            # Product specific context
            'product_id': product_id,
            'product_name': name,
            'product_description': description,
            'product_price': f"{price:.2f}",
            'image_filename': image_filename,
            'price_label': translate('price', lang),
            'add_to_cart': translate('add_to_cart', lang),
            'back_to_products': translate('back_to_products', lang),
            'search_placeholder': translate('search_placeholder', lang),
            'dir': 'rtl' if lang == 'ar' else 'ltr',
            # Footer translations
            'newsletter_signup': translate('newsletter_signup', lang),
            'email_placeholder': translate('email_placeholder', lang),
            'footer_category_title': translate('footer_category_title', lang),
            'footer_support_title': translate('footer_support_title', lang),
            'footer_info_title': translate('footer_info_title', lang),
            'cat_pizza': translate('cat_pizza', lang),
            'cat_sandwich': translate('cat_sandwich', lang),
            'cat_salad': translate('cat_salad', lang),
            'cat_dessert': translate('cat_dessert', lang),
            'support_faq': translate('support_faq', lang),
            'support_contact': translate('support_contact', lang),
            'support_delivery': translate('support_delivery', lang),
            'info_privacy': translate('info_privacy', lang),
            'info_terms': translate('info_terms', lang),
            'category_1': translate('category_1', lang),
            'category_2': translate('category_2', lang),
            'category_3': translate('category_3', lang),
            'newsletter_submit_icon': translate('newsletter_submit_icon', lang),
        }
        detail_html = render_template('product_detail.html', context)
        context['content'] = detail_html
        html = render_template('base.html', context)
        self.send_response(200)
        session_manager.persist_cookie(self)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(html.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def handle_update_cart(self, session, params):
        """Handle modifications to items in the cart.

        Supports three actions: ``increase`` (increment quantity), ``decrease`` (decrement quantity) and
        ``remove`` (remove the item completely). If quantity reaches zero, the item is removed.
        Redirects back to the products page and reopens the cart overlay.
        """
        lang = session['lang']
        product_id_list = params.get('product_id')
        action_list = params.get('action')
        if not product_id_list or not action_list:
            return self.send_error(400, 'Missing parameters')
        try:
            product_id = int(product_id_list[0])
        except ValueError:
            return self.send_error(400, 'Invalid product_id')
        action = action_list[0]
        cart = session.get('cart', [])
        # Find the cart item
        for i, item in enumerate(cart):
            if item['product_id'] == product_id:
                if action == 'increase':
                    item['quantity'] += 1
                elif action == 'decrease':
                    item['quantity'] -= 1
                    if item['quantity'] <= 0:
                        cart.pop(i)
                elif action == 'remove':
                    cart.pop(i)
                break
        # If the cart becomes empty, remove it from the session
        if not cart:
            session.pop('cart', None)
        # Redirect back to products page, keep cart overlay open if cart is not empty
        self.send_response(302)
        session_manager.persist_cookie(self)
        if cart:
            self.send_header('Location', f'/products?lang={lang}&open_cart=1')
        else:
            self.send_header('Location', f'/products?lang={lang}')
        self.end_headers()

    def render_checkout(self, session):
        lang = session['lang']
        cart = session.get('cart', [])
        # If cart is empty, redirect to cart page
        if not cart:
            self.send_response(302)
            session_manager.persist_cookie(self)
            self.send_header('Location', f'/cart?lang={lang}')
            self.end_headers()
            return
        # Build order summary similar to cart table but without quantity editing
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        name_col = f'name_{lang}' if lang in ['fr', 'en', 'ar'] else 'name_fr'
        rows_html_list = []
        total_amount = 0.0
        for item in cart:
            cur.execute(f"SELECT {name_col}, price FROM product WHERE id = ?", (item['product_id'],))
            row = cur.fetchone()
            if row:
                name, price = row
                quantity = item['quantity']
                item_total = price * quantity
                total_amount += item_total
                rows_html_list.append(
                    f"<tr><td>{name}</td><td>{quantity}</td><td>{price:.2f} TND</td><td>{item_total:.2f} TND</td></tr>"
                )
        conn.close()
        rows_html = "\n".join(rows_html_list)
        summary_html = (
            "<table class='cart-table'>\n"
            f"<tr><th>{translate('product_name', lang)}</th><th>{translate('quantity', lang)}</th>"
            f"<th>{translate('price', lang)}</th><th>{translate('total', lang)}</th></tr>\n"
            f"{rows_html}\n"
            f"<tr><td colspan='3'><strong>{translate('total', lang)}</strong></td>"
            f"<td><strong>{total_amount:.2f} TND</strong></td></tr>\n"
            "</table>"
        )
        # Save total in session for later use
        session['checkout_total'] = total_amount
        context = {
            'lang': lang,
            'site_title': translate('site_title', lang),
            'nav_home': translate('nav_home', lang),
            'nav_products': translate('nav_products', lang),
            'nav_cart': translate('nav_cart', lang),
            'nav_language': translate('nav_language', lang),
            'checkout_title': translate('checkout_title', lang),
            'order_summary': summary_html,
            'name_label': translate('name_label', lang),
            'address_label': translate('address_label', lang),
            'card_number_label': translate('card_number_label', lang),
            'place_order_button': translate('place_order_button', lang),
            'email_label': translate('email_label', lang),
            'phone_label': translate('phone_label', lang),
            'payment_method_label': translate('payment_method_label', lang),
            'payment_option_card': translate('payment_option_card', lang),
            'payment_option_cash': translate('payment_option_cash', lang),
            'payment_api_label': translate('payment_api_label', lang),
            'cart_count': len(session.get('cart', [])),
            'search_placeholder': translate('search_placeholder', lang),
            'dir': 'rtl' if lang == 'ar' else 'ltr',
            # Footer translations
            'newsletter_signup': translate('newsletter_signup', lang),
            'email_placeholder': translate('email_placeholder', lang),
            'footer_category_title': translate('footer_category_title', lang),
            'footer_support_title': translate('footer_support_title', lang),
            'footer_info_title': translate('footer_info_title', lang),
            'cat_pizza': translate('cat_pizza', lang),
            'cat_sandwich': translate('cat_sandwich', lang),
            'cat_salad': translate('cat_salad', lang),
            'cat_dessert': translate('cat_dessert', lang),
            'support_faq': translate('support_faq', lang),
            'support_contact': translate('support_contact', lang),
            'support_delivery': translate('support_delivery', lang),
            'info_privacy': translate('info_privacy', lang),
            'info_terms': translate('info_terms', lang),
            'category_1': translate('category_1', lang),
            'category_2': translate('category_2', lang),
            'category_3': translate('category_3', lang),
            'newsletter_submit_icon': translate('newsletter_submit_icon', lang),
        }

        context.update({
            'visa_icon': VISA_ICON_B64,
            'mastercard_icon': MASTERCARD_ICON_B64,
            'amex_icon': AMEX_ICON_B64,
        })
        checkout_page = render_template('checkout.html', context)
        context['content'] = checkout_page
        html = render_template('base.html', context)
        self.send_response(200)
        session_manager.persist_cookie(self)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(html.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def handle_checkout_post(self):
        # Determine language from session (we need session but we can't call get_session again because this call resets cookie? We'll parse existing session id)
        session = session_manager.get_session(self)
        lang = session['lang']
        # Read POST body
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        params = urllib.parse.parse_qs(post_data)
        name = params.get('name', [''])[0].strip()
        email = params.get('email', [''])[0].strip()
        phone = params.get('phone', [''])[0].strip()
        address = params.get('address', [''])[0].strip()
        payment_method = params.get('payment_method', [''])[0].strip()
        # Card number may be provided by an external payment API. We no longer require
        # a card_number field in the form, but we still parse it if present.
        card_number = params.get('card_number', [''])[0].strip()
        # Validate required fields
        # Name, phone, address and payment_method are required. Email is optional.
        if not name or not phone or not address or not payment_method:
            return self.send_error(400, 'Missing required fields')
        # We no longer enforce a card number when paying by card. The payment form
        # should be handled by a separate payment API integrated in the checkout page.
        # Get total from session; ensure cart exists
        cart = session.get('cart', [])
        total_amount = session.get('checkout_total', 0.0)
        if not cart:
            return self.send_error(400, 'Cart is empty')
        # Save order to database
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO orders (customer_name, customer_address, card_number, total, customer_phone, payment_method, customer_email) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, address, card_number if payment_method == 'card' else '', total_amount, phone, payment_method, email),
        )
        order_id = cur.lastrowid
        # Save items
        for item in cart:
            cur.execute(
                "SELECT price FROM product WHERE id = ?", (item['product_id'],)
            )
            price_row = cur.fetchone()
            if not price_row:
                continue
            price = price_row[0]
            cur.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                (order_id, item['product_id'], item['quantity'], price),
            )
        conn.commit()
        conn.close()
        # Save order details to CSV file for vendor
        try:
            csv_path = os.path.join(BASE_DIR, 'orders.csv')
            # Compose items description as a string: "ProductName x Quantity; ..."
            conn2 = sqlite3.connect(DB_PATH)
            cur2 = conn2.cursor()
            item_descriptions = []
            for item in cart:
                cur2.execute("SELECT name_fr FROM product WHERE id = ?", (item['product_id'],))
                row = cur2.fetchone()
                prod_name = row[0] if row else f'ID{item["product_id"]}'
                item_descriptions.append(f"{prod_name} x {item['quantity']}")
            conn2.close()
            items_str = '; '.join(item_descriptions)
            new_file = not os.path.exists(csv_path)
            with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                if new_file:
                    writer.writerow([
                        'timestamp', 'name', 'email', 'phone', 'address', 'payment_method', 'card_number', 'items', 'total'
                    ])
                writer.writerow([
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    name,
                    email,
                    phone,
                    address,
                    payment_method,
                    card_number if payment_method == 'card' else '',
                    items_str,
                    f"{total_amount:.2f}"
                ])
        except Exception as e:
            # Log but don't interrupt the flow
            print(f"Failed to write CSV: {e}")
        # Send confirmation email to customer and vendor if SMTP configuration is provided
        try:
            send_order_email(
                customer_email=email,
                customer_name=name,
                vendor_email=os.environ.get('VENDOR_EMAIL'),
                order_items=cart,
                total=total_amount,
                payment_method=payment_method,
                card_number=card_number if payment_method == 'card' else '',
                phone=phone,
                address=address,
                lang=lang
            )
        except Exception as e:
            print(f"Email sending failed: {e}")
        # Clear cart in session
        session['cart'] = []
        session['checkout_total'] = 0.0
        session['last_order_total'] = total_amount
        # Redirect to confirmation page
        self.send_response(303)  # 303 See Other for POST redirect
        session_manager.persist_cookie(self)
        self.send_header('Location', f'/confirmation?lang={lang}')
        self.end_headers()

    def render_confirmation(self, session):
        lang = session['lang']
        last_total = session.get('last_order_total', 0.0)
        context = {
            'lang': lang,
            'site_title': translate('site_title', lang),
            'nav_home': translate('nav_home', lang),
            'nav_products': translate('nav_products', lang),
            'nav_cart': translate('nav_cart', lang),
            'nav_language': translate('nav_language', lang),
            'order_confirmation_title': translate('order_confirmation_title', lang),
            'order_success_message': translate('order_success_message', lang),
            'total_label': translate('total', lang),
            'order_total': f"{last_total:.2f} TND",
            'back_home': translate('back_home', lang),
            'cart_count': len(session.get('cart', [])),
            'search_placeholder': translate('search_placeholder', lang),
            'dir': 'rtl' if lang == 'ar' else 'ltr',
            # Footer translations
            'newsletter_signup': translate('newsletter_signup', lang),
            'email_placeholder': translate('email_placeholder', lang),
            'footer_category_title': translate('footer_category_title', lang),
            'footer_support_title': translate('footer_support_title', lang),
            'footer_info_title': translate('footer_info_title', lang),
            'cat_pizza': translate('cat_pizza', lang),
            'cat_sandwich': translate('cat_sandwich', lang),
            'cat_salad': translate('cat_salad', lang),
            'cat_dessert': translate('cat_dessert', lang),
            'support_faq': translate('support_faq', lang),
            'support_contact': translate('support_contact', lang),
            'support_delivery': translate('support_delivery', lang),
            'info_privacy': translate('info_privacy', lang),
            'info_terms': translate('info_terms', lang),
            'category_1': translate('category_1', lang),
            'category_2': translate('category_2', lang),
            'category_3': translate('category_3', lang),
            'newsletter_submit_icon': translate('newsletter_submit_icon', lang),
        }

        context.update({
            'visa_icon': VISA_ICON_B64,
            'mastercard_icon': MASTERCARD_ICON_B64,
            'amex_icon': AMEX_ICON_B64,
        })
        confirm_page = render_template('confirmation.html', context)
        context['content'] = confirm_page
        html = render_template('base.html', context)
        self.send_response(200)
        session_manager.persist_cookie(self)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(html.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    # Override log_message to reduce console noise
    def log_message(self, format, *args):
        # Uncomment the next line to enable server logs
        # super().log_message(format, *args)
        pass


# Email configuration. These values can be overridden by environment variables.
SMTP_SERVER = os.environ.get('SMTP_SERVER')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587')) if os.environ.get('SMTP_PORT') else None
SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL') or SMTP_USERNAME


def send_order_email(customer_email: str, customer_name: str, vendor_email: str, order_items: list, total: float,
                     payment_method: str, card_number: str, phone: str, address: str, lang: str) -> None:
    """Send an order confirmation email to the customer and a copy to the vendor.

    This function uses SMTP credentials defined in environment variables:
    ``SMTP_SERVER``, ``SMTP_PORT``, ``SMTP_USERNAME``, ``SMTP_PASSWORD`` and ``SENDER_EMAIL``.
    If any of these are not provided or if ``customer_email`` is empty, the function returns silently.

    :param customer_email: recipient's email address
    :param customer_name: recipient's name
    :param vendor_email: vendor's email address (can be None)
    :param order_items: list of cart items, each with ``product_id`` and ``quantity``
    :param total: total amount of the order
    :param payment_method: 'card' or 'cash'
    :param card_number: card number provided (may be empty if cash)
    :param phone: customer's phone number
    :param address: customer's shipping address
    :param lang: language code for email content
    """
    if not customer_email or not SMTP_SERVER or not SMTP_USERNAME or not SMTP_PASSWORD or not SENDER_EMAIL:
        # Insufficient information to send email
        return
    # Fetch product names for email summary
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    name_col = f'name_{lang}' if lang in ['fr', 'en', 'ar'] else 'name_fr'
    lines = []
    for item in order_items:
        cur.execute(f"SELECT {name_col}, price FROM product WHERE id = ?", (item['product_id'],))
        row = cur.fetchone()
        if row:
            name, price = row
            quantity = item['quantity']
            item_total = price * quantity
            lines.append(f"- {name} x {quantity}: {item_total:.2f} TND")
    conn.close()
    items_block = "\n".join(lines)
    # Compose subject and body using translations
    subject = translate('email_subject', lang)
    body_intro = translate('email_body_intro', lang).format(name=customer_name)
    body_total = translate('email_body_total', lang).format(total=f"{total:.2f}")
    body_thanks = translate('email_body_thanks', lang)
    payment_info = f"\nPayment method: {payment_method}\n"
    if payment_method == 'card':
        # Mask card number except last 4 digits
        masked = '*' * (len(card_number) - 4) + card_number[-4:] if card_number else ''
        payment_info += f"Card: {masked}\n"
    else:
        payment_info += "Payable on delivery\n"
    contact_info = f"Phone: {phone}\nAddress: {address}\n"
    body = (f"{body_intro}\n\n"
            f"Items:\n{items_block}\n\n"
            f"{body_total}\n"
            f"{payment_info}"
            f"{contact_info}"
            f"{body_thanks}")
    # Construct RFC822 email
    from_addr = SENDER_EMAIL
    to_addrs = [customer_email]
    if vendor_email:
        to_addrs.append(vendor_email)
    message = f"From: {from_addr}\r\nTo: {', '.join(to_addrs)}\r\nSubject: {subject}\r\n\r\n{body}"
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(from_addr, to_addrs, message.encode('utf-8'))
    except Exception as e:
        # Fail silently; raising would interrupt order placement
        print(f"SMTP error: {e}")


def run_server(port: int = 8000):
    """Initialize database and start the HTTP server."""
    init_db()
    address = ('', port)
    httpd = http.server.HTTPServer(address, DeliveryRequestHandler)
    print(f"Serving delivery site on http://localhost:{port}")
    httpd.serve_forever()


if __name__ == '__main__':
    run_server()