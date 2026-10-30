# Rancangan Aplikasi Kelompok 7 PBP C

## 1. Nama Aplikasi
**Bakara**

## 2. Anggota Kelompok
- Faatir Wibowo Rachmad - 2506595146
- Kesya Clara Dania - 2506656892
- Nurul Zakyah Ovi - 2506617582
- James Adi Putra - 2506624644
- Darrel Rifathir Arwa - 2506536420

## 3. Deskripsi Aplikasi
Bakara adalah platform berbagi barang khusus mahasiswa Universitas Indonesia yang memungkinkan mahasiswa untuk membeli, meminjam, atau mendonasikan barang yang sudah tidak digunakan kepada mahasiswa lain di lingkungan UI, baik antar kating (kakak tingkat) maupun deting (adik tingkat).

Ide ini terutama ditujukan untuk mahasiswa baru dan mahasiswa perantauan yang sering membutuhkan berbagai barang ketika pertama kali tinggal di kos/asrama dan memulai perkuliahan di UI. Misalnya, seorang maba membutuhkan hanger, lampu belajar, rice cooker, buku kuliah, kalkulator, kabel, alat makan, ataupun perlengkapan kos. Daripada langsung membeli barang baru, ia dapat mencari barang tersebut di Bakara dan mendapatkannya dari kating yang sudah tidak membutuhkannya.

### Value Proposition (VP) Questions
**A. What are the purposes/visions of this website?**
Membangun ekosistem berbagi dan penggunaan kembali barang di lingkungan UI, agar mahasiswa bisa memenuhi kebutuhan tanpa harus selalu membeli barang baru.

**B. What problems will this website solve?**
- Mahasiswa (terutama maba/anak kos baru) terpaksa beli barang baru padahal barang serupa sudah ada di sekitar mereka.
- Banyak barang kating yang masih layak pakai tapi menganggur/tidak terpakai.
- Barang tak terpakai berpotensi jadi sampah padahal masih punya nilai guna.
- Sulit menemukan sesama mahasiswa UI yang butuh/punya barang tertentu karena info tersebar di banyak platform (grup chat, IG story, twitter, dll).

**C. Whom will this website help?**
- Utama: Mahasiswa baru/deting UI yang butuh perlengkapan kuliah & kos.
- Kedua: Kating/mahasiswa senior yang ingin menyalurkan barang tak terpakai.
- Tambahan: Organisasi/fakultas UI untuk kegiatan donasi atau reuse jika memungkinkan.

**D. How will this website help them?**
Menyediakan satu platform untuk mencari, membeli, meminjam, atau mendonasikan barang antar mahasiswa UI lengkap dengan pencarian by kategori/lokasi, chat langsung dengan pemilik barang, dan sistem rating/review, sehingga proses reuse jadi lebih mudah dan terpusat dibanding hanya lewat grup chat atau story.

## 4. Perbandingan dengan Aplikasi Serupa

Bakara memiliki fokus yang berbeda dibanding platform jual-beli umum maupun platform reuse khusus kampus yang sudah ada (di luar maupun di dalam negeri):

| Platform | Fokus | Perbedaan Bakara |
|---|---|---|
| Carousell | Jual-beli barang bekas, skala umum | Bakara fokus pada komunitas mahasiswa UI, bukan sekadar jual-beli |
| OLX | Marketplace barang bekas, skala umum | Bakara punya konsep gratis, tukar, pinjam, dan jual murah |
| Facebook Marketplace | Jual-beli lokal, skala umum | Bakara lebih spesifik untuk kebutuhan mahasiswa/kampus UI |
| ReSwap (University of Southern California, California) | Marketplace khusus mahasiswa untuk beli, jual, tukar, dan sewa barang per kategori (pakaian, kebutuhan harian, hunian, carpool) | Bakara berfokus khusus pada sirkulasi barang kebutuhan kuliah & kos, dengan penekanan pada kebutuhan maba/deting |
| Swapp (Cornell University, New York) | Marketplace jual-beli barang preloved khusus mahasiswa, untuk mengurangi sampah saat peak moving season | Bakara menambahkan opsi donasi & pinjam, tidak hanya jual-beli |
| BaranginAja (UNESA, Surabaya) | Jual-beli barang bekas antar mahasiswa se-kampus dengan sistem komisi platform | Bakara tidak berorientasi profit/komisi, lebih menekankan sirkulasi & berbagi antar kating-deting |
| Loak.in (Undika, Surabaya) | Jual-beli barang bekas terhubung ke tukang loak via peta | Bakara menyasar sirkulasi barang antar sesama mahasiswa, bukan ke pengepul barang bekas |

**Our Insight**: beberapa platform reuse *khusus kampus* (ReSwap, Swapp) sudah ditemukan di luar negeri, tetapi implementasinya di Indonesia masih sangat jarang, dan yang sudah ada (BaranginAja, Loak.in) masih murni berorientasi jual-beli tanpa elemen pinjam/donasi. Bakara mengisi gap ini dengan menggabungkan jual, pinjam, dan donasi dalam satu ekosistem berbasis komunitas UI.

## 5. Daftar Modul

| No | Modul | Entitas Utama | CRUD | PIC |
|---:|---|---|---|---|
| 1 | **Autentikasi & Profil Pengguna** | User | **Create:** Registrasi akun (email @ui.ac.id/upload KTM)<br>**Read:** Lihat profil sendiri/orang lain<br>**Update:** Edit profil, nomor WA, foto<br>**Delete:** Nonaktifkan akun | Kesya Clara Dania |
| 2 | **Katalog & Listing Barang** | Barang | **Create:** Upload barang baru<br>**Read:** Lihat detail barang, browse katalog<br>**Update:** Edit info barang (deskripsi, foto, status)<br>**Delete:** Hapus listing barang | Darrel Rifathirn Arwa |
| 3 | **Kontak & Minat** | Minat | **Create:** Tandai tertarik pada barang<br>**Read:** Lihat daftar yang tertarik untuk pemilik barang<br>**Update:** Tidak diperlukan, cukup create/delete<br>**Delete:** Batalkan tanda tertarik | Faatir Wibowo Rachmad |
| 4 | **Transaksi & Tracking Status** | Transaksi | **Create:** Mulai transaksi dari minat<br>**Read:** Lihat status & riwayat transaksi<br>**Update:** Ubah status (nego → selesai)<br>**Delete:** Batalkan transaksi | James Adi Putra |
| 5 | **Rating & Review** | Review | **Create:** Beri rating & ulasan setelah transaksi selesai<br>**Read:** Lihat rating/review di profil user<br>**Update:** Edit review sendiri<br>**Delete:** Hapus review sendiri | Nurul Zakiyah Ovi |

## 6. Sumber Public API / Mock API

| API | Kegunaan |
|---|---|
| **OpenStreetMap API** | Digunakan untuk kebutuhan lokasi, seperti lokasi kampus/fakultas UI, lokasi barang, dan titik pengambilan barang. |
| **DummyJSON API** | Digunakan sebagai mock API / data dummy untuk keperluan prototyping dan testing awal tampilan daftar barang, kategori, serta ulasan sebelum diintegrasikan penuh dengan backend. |
| **Open Library API** | Digunakan untuk mengambil metadata buku secara otomatis, seperti judul, penulis, dan sampul buku ketika pengguna mengunggah atau mencari buku kuliah preloved di platform. |
              

## 7. Jenis/Peran Pengguna Aplikasi (User Role & Target User)

### Mahasiswa (role utama)
Dapat melakukan:
- Mencari barang
- Mengunggah barang
- Mendonasikan, meminjamkan, atau menjual barang
- Melakukan request/pengajuan barang
- Memberikan review

**Target utama:** mahasiswa baru/deting dan mahasiswa perantauan yang sedang membutuhkan perlengkapan kuliah/kos.

### Admin
Dapat melakukan:
- Mengelola pengguna
- Menghapus postingan bermasalah
- Menangani laporan
- Mengelola kategori
- Memantau aktivitas platform

### Organisasi/Fakultas (role tambahan jika memungkinkan)
Dapat melakukan:
- Membuat program donasi
- Menyediakan barang
- Mengadakan kegiatan reuse di lingkungan UI

## 8. Tautan Deployment PWS
https://darrel-rifathir-bakara.pws.cs.ui.ac.id/

## 9. Tautan Desain Figma
https://www.figma.com/design/pU7PzvdlefcBJJkBS5NqQB/Untitled?node-id=2-4&t=QdZKyKytq6PMkH4r-1

## 10. AI Disclosure
Dokumentasi penggunaan asisten kecerdasan buatan (AI) oleh anggota tim dalam proses perancangan, pengembangan, dan pengujian aplikasi Bakara.

--- 

### James Adi Putra — Layout & Refactor
* **Tools yang Digunakan:** Claude (Anthropic) & DeepSeek
* **Bagian yang Dibantu AI:**
  * Merancang dan menyusun struktur `urls.py` untuk modul transaksi mengikuti konvensi penamaan RESTful berbahasa Indonesia (`buat/`, `ubah-status/`, `batalkan/`, `api/list/`) serta penjelasan penempatan parameter UUID (`ubah-status/<uuid:transaksi_id>/`).
  * Mereview dan merefaktorisasi struktur berkas `transaksi.html` agar mematuhi standar *template* Django dengan memisahkan penataan CSS ke dalam folder `static`.
  * Menjelaskan fungsi logika perenderan tombol aksi dinamis `buildActionButtonsHtml()` dan relevansinya terhadap alur transaksi pengguna.
  * Menulis ulang kode HTML halaman antarmuka transaksi.
  * Memberikan penjelasan strategi refaktorisasi struktur komponen pada antarmuka *layout*.
  * Memetakan implementasi materi tutorial ke dalam arsitektur kebutuhan proyek Bakara.
  * Menyusun daftar bagian berkas yang perlu disesuaikan beserta hierarki tata letak visualnya.
* **Keterbatasan AI & Perbaikan Manual:** Rekomendasi tata letak dan struktur antarmuka dari AI disaring dan disesuaikan kembali secara manual agar tetap konsisten dengan sistem token desain (`style.css`) bersama kelompok.
---

### Darrel Rifathir Arwa — Modul Katalog
* **Tools yang Digunakan:** Gemini 3.8 Flash & Claude 3.5 Sonnet / Opus
* **Bagian yang Dibantu AI:**
  * Penelusuran masalah intersepsi *event click* pada modal formulir AJAX ("Upload Barang Cepat") agar tidak memicu pengalihan halaman penuh (*browser redirect*).
  * Formulasi validasi berkas pada `BarangForm` (pembatasan ukuran berkas gambar maksimal 5 MB dan verifikasi integritas biner via Pillow).
  * Proteksi privasi informasi kontak WhatsApp penjual pada halaman detail barang bagi pengguna yang belum terotentikasi.
  * Penyusunan pesan *commit* atomik sesuai konvensi *Conventional Commits* dan panduan alur kerja Git (`git stash` & sinkronisasi *branch*).
* **Keterbatasan AI & Perbaikan Manual:**
  * *Kesalahan Struktur Template:* AI berasumsi bahwa *template* induk memiliki blok `{% block script %}`. Karena blok tersebut tidak ada di `base.html`, skrip dipindahkan manual ke dalam `{% block content %}` dengan parameter *cache-busting* (`?v=1.1`).
  * *Selektor Elemen Terbatas:* Rekomendasi selektor ID tunggal dari AI tidak menangkap tombol unggah di banner bawah; dirombak manual menggunakan *class* bersama (`.btn-open-modal-tambah`) dan fungsi global *window scope*.
  * *Hak Akses Terlalu Restriktif:* AI sempat mengunci tampilan barang orang lain hanya untuk aksi hapus moderator; diperbaiki manual agar hak moderasi staf dapat berjalan berdampingan dengan alur pembeli biasa.

---

### Kesya Clara Dania — Modul Autentikasi & Profil
* **Tools yang Digunakan:** Claude (Claude Code)
* **Bagian yang Dibantu AI:**
  * Perumusan logika validasi email civitas akademik (`@ui.ac.id`), normalisasi nomor WhatsApp, dan sanitasi parameter `next` untuk mencegah celah *open redirect*.
  * Penyusunan kerangka pengujian *unit test* (model, form, view, dan *mocking* respon SSO UI) hingga mencapai 100% *code coverage*.
  * Penyesuaian skrip pengujian otomatis setelah proses penggabungan (*merge*) dengan *branch main* terbaru.
* **Keterbatasan AI & Perbaikan Manual:** Meninjau dan memverifikasi ulang setiap kode rekomendasi agar sesuai dengan model kustom *User UUID* dan *Profile signals*, serta menguji langsung alur autentikasi dan validasi hak akses secara mandiri.

---

### Faatir Wibowo Rachmad — Modul Minat
* **Tools yang Digunakan:** ChatGPT
* **Bagian yang Dibantu AI:**
  * Eksplorasi konsep dan pemetaan logika dasar alur penandaan serta pembatalan minat barang.
  * Saran awal struktur alur data untuk menampilkan daftar barang yang diminati serta daftar peminat dari listing pribadi.
  * Pemahaman alur transisi data saat minat disetujui dan dialihkan menjadi transaksi resmi.
* **Keterbatasan AI & Perbaikan Manual:** Saran logika awal dari AI disesuaikan dan ditulis ulang secara manual agar cocok dengan arsitektur model database Bakara serta memastikan aturan otorisasi antar-pengguna berjalan aman.

---

### Nurul Zakyah Ovi — Modul Review & Rating
* **Tools yang Digunakan:** Claude 3.5 Sonnet / Opus, ChatGPT (GPT-4o), & Gemini 3.1 Pro
* **Strategi Prompting:** *Targeted contextual troubleshooting* bergantian lintas model (Claude untuk bedah logika basis data dan kasus rumit, ChatGPT untuk sintaks spesifik dan alur asinkron, serta Gemini untuk validasi galat pengujian akhir dan laporan).
* **Bagian yang Dibantu AI:**
  * Formulasi logika proteksi backend pada fungsi `create_review` agar penjual tidak dapat mengulas transaksinya sendiri.
  * Penyusunan struktur serialisasi `JsonResponse` bertingkat untuk kebutuhan data tab dinamis di JavaScript.
  * Panduan penulisan asersi kode status HTTP (seperti 403 Forbidden) pada *unit tests* serta penyelesaian konflik penggabungan berkas pengujian.
* **Keterbatasan AI & Perbaikan Manual:**
  * *Celah Otorisasi Sisi Frontend:* Rekomendasi awal AI hanya mengandalkan penyembunyian elemen tombol di HTML peramban; diperbaiki manual dengan menyematkan validasi server-side tegas (`transaksi.penjual == request.user`) pada fungsi view Django agar endpoint aman dari tembakan HTTP langsung.
  * *Inkonsistensi Skema Data JSON (KeyError):* Skrip pengujian otomatis rujukan AI mengasumsikan atribut gambar yang tidak ada di model; diperbaiki manual dengan merestrukturisasi kamus view dan menyelaraskan parameter asersi uji sesuai skema aktual.
  * *Konflik Berkas Pengujian (Merge Conflicts):* Terjadi bentrok kode pada `tests.py` akibat perbedaan konfigurasi basis data uji dari anggota lain; ditangani dengan peninjauan manual baris demi baris (*manual diff*) hingga seluruh rangkaian tes modul ulasan lolos dengan cakupan di atas 95%.
