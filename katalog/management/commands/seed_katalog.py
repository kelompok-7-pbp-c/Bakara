import io
import urllib.request
import requests
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from PIL import Image

from katalog.models import Barang

User = get_user_model()

# Pemetaan kategori DummyJSON ke kategori model Barang Bakara
CATEGORY_MAP = {
    # Elektronik
    'laptops': Barang.ELEKTRONIK,
    'smartphones': Barang.ELEKTRONIK,
    'tablets': Barang.ELEKTRONIK,
    'mobile-accessories': Barang.ELEKTRONIK,
    # Furnitur
    'furniture': Barang.FURNITUR,
    'home-decoration': Barang.FURNITUR,
    # Pakaian & Aksesoris
    'mens-shirts': Barang.PAKAIAN,
    'mens-shoes': Barang.PAKAIAN,
    'mens-watches': Barang.PAKAIAN,
    'womens-bags': Barang.PAKAIAN,
    'womens-dresses': Barang.PAKAIAN,
    'womens-jewellery': Barang.PAKAIAN,
    'womens-shoes': Barang.PAKAIAN,
    'womens-watches': Barang.PAKAIAN,
    'tops': Barang.PAKAIAN,
    # Olahraga
    'sports-accessories': Barang.OLAHRAGA,
    # Kebutuhan Kos
    'kitchen-accessories': Barang.KEBUTUHAN_KOS,
    'groceries': Barang.KEBUTUHAN_KOS,
    'skin-care': Barang.KEBUTUHAN_KOS,
    'beauty': Barang.KEBUTUHAN_KOS,
}


def generate_fallback_image(seed_id):
    """Membuat dummy image valid jika unduhan thumbnail gagal."""
    buf = io.BytesIO()
    # Warna latar Navy / Warm Gold khas Bakara
    color = (30, 58, 95) if seed_id % 2 == 0 else (245, 166, 35)
    img = Image.new('RGB', (400, 400), color=color)
    img.save(buf, format='JPEG')
    return ContentFile(buf.getvalue(), name=f'dummyjson_fallback_{seed_id}.jpg')


def generate_offline_fallback_products(count=50):
    """Fallback 50 produk DummyJSON jika API offline/terisolasi sandbox."""
    fallback_items = [
        ("Essence Mascara Lash Princess", "beauty", 9.99),
        ("Eyeshadow Palette with Mirror", "beauty", 19.99),
        ("Powder Canister", "beauty", 14.99),
        ("Red Lipstick", "beauty", 12.99),
        ("Red Nail Polish", "beauty", 8.99),
        ("Calvin Klein CK One", "fragrances", 49.99),
        ("Chanel Coco Mademoiselle", "fragrances", 129.99),
        ("Dior J'adore", "fragrances", 89.99),
        ("Dolce Shine Eau de Parfum", "fragrances", 69.99),
        ("Gucci Bloom Eau de Parfum", "fragrances", 79.99),
        ("Annibale Colombo Bed", "furniture", 1899.99),
        ("Annibale Colombo Sofa", "furniture", 2499.99),
        ("Bedside Table African Cherry", "furniture", 299.99),
        ("Knoll Saarinen Executive Chair", "furniture", 499.99),
        ("Wooden Bathroom Sink With Mirror", "furniture", 799.99),
        ("Apple", "groceries", 1.99),
        ("Beef Steak", "groceries", 12.99),
        ("Cat Food", "groceries", 8.99),
        ("Chicken Meat", "groceries", 9.99),
        ("Cooking Oil", "groceries", 4.99),
        ("Cucumber", "groceries", 1.49),
        ("Dog Food", "groceries", 10.99),
        ("Eggs", "groceries", 2.99),
        ("Fish Steak", "groceries", 14.99),
        ("Green Bell Pepper", "groceries", 1.29),
        ("Green Chili Pepper", "groceries", 0.99),
        ("Honey Jar", "groceries", 6.99),
        ("Ice Cream", "groceries", 5.49),
        ("Juice", "groceries", 3.99),
        ("Kiwi", "groceries", 2.49),
        ("Lemon", "groceries", 0.79),
        ("Milk", "groceries", 3.49),
        ("Mulberry", "groceries", 4.99),
        ("Nescafe Coffee", "groceries", 7.99),
        ("Potatoes", "groceries", 2.29),
        ("Protein Powder", "groceries", 19.99),
        ("Red Onions", "groceries", 1.99),
        ("Rice", "groceries", 5.99),
        ("Soft Drinks", "groceries", 1.99),
        ("Strawberry", "groceries", 3.99),
        ("Tissue Paper Box", "groceries", 2.49),
        ("Water Bottle", "groceries", 1.49),
        ("Plant Pot", "home-decoration", 14.99),
        ("Table Lamp", "home-decoration", 24.99),
        ("Bamboo Spatula", "kitchen-accessories", 7.99),
        ("Black Aluminum Cup", "kitchen-accessories", 5.99),
        ("Black Whisk", "kitchen-accessories", 9.99),
        ("Boxed Blender", "kitchen-accessories", 39.99),
        ("Carbon Steel Knife", "kitchen-accessories", 29.99),
        ("Chopping Board", "kitchen-accessories", 12.99),
    ]
    products = []
    for idx, (title, category, price) in enumerate(fallback_items[:count], start=1):
        products.append({
            'id': idx,
            'title': title,
            'description': f'{title} dalam kondisi prima dan siap digunakan oleh mahasiswa UI.',
            'category': category,
            'price': price,
            'thumbnail': f'https://dummyjson.com/image/400x400/282828?text={title.replace(" ", "+")}',
        })
    return products


class Command(BaseCommand):
    help = 'Mengambil 50 produk dari DummyJSON API dan memasukkannya ke database katalog Bakara.'

    def handle(self, *args, **options):
        self.stdout.write('Memulai seeding data katalog dari DummyJSON API...')

        # 1. Pastikan akun penjual default/admin tersedia
        penjual = User.objects.filter(is_staff=True).first() or User.objects.first()
        if not penjual:
            penjual, created = User.objects.get_or_create(
                username='admin_bakara',
                defaults={
                    'email': 'admin@bakara.ui.ac.id',
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            if created:
                penjual.set_password('admin123')
                penjual.save()
            self.stdout.write(f'Menggunakan akun penjual baru: {penjual.username}')
        else:
            self.stdout.write(f'Menggunakan akun penjual terdaftar: {penjual.username}')

        # 2. Ambil minimal 50 data produk dari DummyJSON API
        products = []
        api_url = 'https://dummyjson.com/products?limit=50'
        try:
            resp = requests.get(api_url, timeout=10)
            if resp.status_code == 200:
                products = resp.json().get('products', [])
                self.stdout.write(f'Berhasil mengambil {len(products)} produk dari DummyJSON API secara online.')
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f'Koneksi langsung ke DummyJSON API terkendala ({e}). Menggunakan dataset produk DummyJSON cadangan...'
            ))

        if len(products) < 50:
            products = generate_offline_fallback_products(50)

        # 3. Looping dan simpan produk ke model Barang
        created_count = 0
        skipped_count = 0

        for item in products:
            raw_nama = item.get('title', 'Produk Tanpa Nama')
            nama = (raw_nama[:117] + '...') if len(raw_nama) > 120 else raw_nama

            # Pencegahan duplikasi data jika script dijalankan berulang
            if Barang.objects.filter(nama=nama).exists():
                skipped_count += 1
                continue

            deskripsi = item.get('description', '')
            raw_kategori = item.get('category', '').lower()
            kategori = CATEGORY_MAP.get(raw_kategori, Barang.LAINNYA)

            # Konversi harga USD ke estimasi IDR (Rp)
            usd_price = float(item.get('price', 10.0))
            harga_idr = max(10000, int(round(usd_price * 15000)))

            # Unduh thumbnail atau gunakan fallback image
            thumbnail_url = item.get('thumbnail')
            image_content = None

            if thumbnail_url:
                try:
                    img_resp = requests.get(thumbnail_url, timeout=5)
                    if img_resp.status_code == 200 and img_resp.content:
                        image_content = ContentFile(
                            img_resp.content,
                            name=f"dummyjson_{item.get('id', created_count + 1)}.jpg"
                        )
                except Exception:
                    image_content = None

            if not image_content:
                image_content = generate_fallback_image(item.get('id', created_count + 1))

            # Simpan data ke model Barang
            barang = Barang(
                penjual=penjual,
                nama=nama,
                deskripsi=deskripsi,
                kategori=kategori,
                jenis=Barang.JUAL,
                kondisi=Barang.BAIK,
                status=Barang.TERSEDIA,
                harga=harga_idr,
                lokasi='Asrama UI Depok',
            )
            barang.foto.save(image_content.name, image_content, save=True)
            created_count += 1

        total_katalog = Barang.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'Seeding selesai! Berhasil menambahkan {created_count} barang baru '
            f'({skipped_count} dilewati karena sudah ada). Total barang di katalog: {total_katalog}.'
        ))
