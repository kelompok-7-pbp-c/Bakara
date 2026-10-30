from django.test import TestCase
from django.urls import reverse

class BantuanPageTests(TestCase):
    def test_halaman_bantuan_menggunakan_template_yang_benar(self):
        response = self.client.get(reverse('main:show_bantuan'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bantuan.html')

    def test_halaman_bantuan_menampilkan_faq_dan_tautan_footer(self):
        response = self.client.get(reverse('main:show_bantuan'))

        self.assertContains(response, 'Pusat Bantuan Bakara')
        self.assertContains(response, 'Minat &amp; Kontak')
        self.assertContains(response, 'Pilih &amp; Proses')
        self.assertContains(response, 'mailto:james.adi@ui.ac.id')
        self.assertContains(response, reverse('main:show_bantuan'))