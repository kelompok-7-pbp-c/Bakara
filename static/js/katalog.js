/**
 * Escape karakter HTML untuk mencegah XSS dari data JSON.
 * @param {string} str
 * @returns {string}
 */
function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/**
 * Debounce: tunda eksekusi fungsi selama `delay` ms setelah pemanggilan terakhir.
 * @param {Function} fn
 * @param {number} delay
 */
function debounce(fn, delay) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

// Render Kartu Barang 

/**
 * Render satu kartu barang dari data JSON.
 * Fallback foto menggunakan placeholder abu-abu netral minimalis (tanpa emoji).
 * @param {Object} b
 * @returns {string}
 */
function renderKartuBarang(b) {
  const fotoHtml = b.foto_url
    ? `<img src="${escapeHtml(b.foto_url)}" alt="${escapeHtml(b.nama)}" loading="lazy">`
    : `<div class="card-img-placeholder" aria-hidden="true">
         <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="placeholder-icon">
           <rect width="18" height="18" x="3" y="3" rx="2" ry="2"/>
           <circle cx="9" cy="9" r="2"/>
           <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/>
         </svg>
       </div>`;

  const statusBadge = b.status !== 'tersedia'
    ? `<span class="badge badge-status badge-status-${escapeHtml(b.status)}">
         ${escapeHtml(b.status)}
       </span>`
    : '';

  return `
    <a href="${escapeHtml(b.detail_url)}" class="barang-card" aria-label="${escapeHtml(b.nama)}">
      <div class="card-img-wrap">
        ${fotoHtml}
        <div class="card-badges">
          <span class="badge badge-${escapeHtml(b.jenis)}">${escapeHtml(b.jenis_label)}</span>
          ${statusBadge}
        </div>
      </div>
      <div class="card-body">
        <span class="card-kategori">${escapeHtml(b.kategori)}</span>
        <h3 class="card-nama">${escapeHtml(b.nama)}</h3>
        <span class="card-kondisi">${escapeHtml(b.kondisi)}</span>
        <div class="card-footer">
          <span class="card-harga">${escapeHtml(b.harga_display)}</span>
          <span class="card-penjual">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
            ${escapeHtml(b.penjual.username)}
          </span>
        </div>
      </div>
    </a>`;
}

// Fetch & Render Grid (AJAX) 

/**
 * Ambil parameter filter saat ini dari elemen DOM.
 * @returns {Object}
 */
function getCurrentFilterParams() {
  return {
    q: document.getElementById('search-input')?.value.trim() || '',
    kategori: document.getElementById('filter-kategori')?.value || '',
    jenis: document.getElementById('filter-jenis')?.value || '',
    sort: document.getElementById('sort-select')?.value || '-dibuat_pada',
  };
}

/**
 * Panggil endpoint API katalog_json secara asinkron dan perbarui container #barang-grid.
 * @param {Object} params
 */
async function fetchBarang(params = null) {
  const grid = document.getElementById('barang-grid');
  if (!grid) return;

  const filterParams = params || getCurrentFilterParams();
  const endpoint = window.KATALOG_JSON_URL || '/katalog/api/list/';
  const url = new URL(endpoint, window.location.origin);

  Object.entries(filterParams).forEach(([k, v]) => {
    if (v) url.searchParams.set(k, v);
  });

  try {
    grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1"><p>Memuat daftar barang…</p></div>';
    const res = await fetch(url.toString(), {
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const barangList = Array.isArray(data) ? data : (data.barang || []);

    if (barangList.length === 0) {
      grid.innerHTML = `
        <div class="empty-state" style="grid-column:1/-1">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="empty-state-svg" style="margin: 0 auto 12px; color: var(--color-secondary);">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
          <h2>Barang tidak ditemukan</h2>
          <p>Coba ubah kata kunci atau bersihkan filter pencarianmu.</p>
          <button type="button" class="btn btn-ghost" style="margin-top:16px" onclick="document.getElementById('btn-reset-filter').click()">
            Reset Filter
          </button>
        </div>`;
    } else {
      grid.innerHTML = barangList.map(renderKartuBarang).join('');
    }

    // Perbarui jumlah barang di meta bar
    const counter = document.querySelector('.katalog-count strong');
    if (counter) counter.textContent = Array.isArray(data) ? data.length : (data.total || barangList.length);

    // Perbarui URL browser tanpa reload halaman
    if (window.history.replaceState) {
      const searchParams = new URLSearchParams();
      if (filterParams.q) searchParams.set('q', filterParams.q);
      if (filterParams.kategori) searchParams.set('kategori', filterParams.kategori);
      if (filterParams.jenis) searchParams.set('jenis', filterParams.jenis);
      if (filterParams.sort && filterParams.sort !== '-dibuat_pada') {
        searchParams.set('sort', filterParams.sort);
      }
      const newQuery = searchParams.toString();
      const newPath = newQuery ? `${window.location.pathname}?${newQuery}` : window.location.pathname;
      window.history.replaceState({}, '', newPath);
    }
  } catch (err) {
    console.error('[katalog.js] fetchBarang error:', err);
    grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1"><p>Gagal memuat data. Silakan muat ulang halaman.</p></div>';
  }
}

// Live Search, Dropdown Filter, & Reset 

function initToolbarControls() {
  const searchInput = document.getElementById('search-input');
  const filterForm = document.getElementById('katalog-filter-form');
  const resetBtn = document.getElementById('btn-reset-filter');

  // Live search dengan debounce 300ms pada event 'input'
  if (searchInput) {
    const debouncedSearch = debounce(() => {
      fetchBarang(getCurrentFilterParams());
    }, 300);

    searchInput.addEventListener('input', debouncedSearch);
  }

  // Filter dropdowns: Kategori, Jenis, Sorting memicu pembaruan instan pada event 'change'
  ['filter-kategori', 'filter-jenis', 'sort-select'].forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('change', () => {
        fetchBarang(getCurrentFilterParams());
      });
    }
  });

  // Cegah submit form default (menggunakan asinkronus fetch)
  if (filterForm) {
    filterForm.addEventListener('submit', (e) => {
      e.preventDefault();
      fetchBarang(getCurrentFilterParams());
    });
  }

  // Tombol Reset Filter: kembalikan semua filter ke kondisi awal dan refresh via AJAX
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      if (searchInput) searchInput.value = '';

      const filterKategori = document.getElementById('filter-kategori');
      if (filterKategori) filterKategori.value = '';

      const filterJenis = document.getElementById('filter-jenis');
      if (filterJenis) filterJenis.value = '';

      const sortSelect = document.getElementById('sort-select');
      if (sortSelect) sortSelect.value = '-dibuat_pada';

      fetchBarang({ q: '', kategori: '', jenis: '', sort: '-dibuat_pada' });
    });
  }
}

// Modal Upload Barang (AJAX) 
window.openTambahBarangModal = function(e) {
  if (e) {
    e.preventDefault();
    e.stopPropagation();
  }
  const modal = document.getElementById('modal-tambah-barang');
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    const errBox = document.getElementById('ajax-form-errors');
    if (errBox) errBox.innerHTML = '';
    const firstInput = modal.querySelector('#ajax-nama');
    if (firstInput) firstInput.focus();
    return false;
  }
  return true;
};

function initTambahBarangModal() {
  const modal = document.getElementById('modal-tambah-barang');
  const closeBtn = document.getElementById('btn-close-modal-tambah');
  const form = document.getElementById('form-tambah-barang-ajax');
  const errBox = document.getElementById('ajax-form-errors');

  if (!modal || !form) return;

  // Tangkap klik pada semua tombol pemicu modal (toolbar maupun CTA bar)
  const openButtons = document.querySelectorAll('#btn-open-modal-tambah, .btn-open-modal-tambah');
  openButtons.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      modal.style.display = 'flex';
      document.body.style.overflow = 'hidden';
    });
  });

  // Tutup modal
  const closeModal = () => {
    modal.style.display = 'none';
    document.body.style.overflow = '';
    form.reset();
    if (errBox) errBox.innerHTML = '';
  };

  if (closeBtn) closeBtn.addEventListener('click', closeModal);
  modal.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });

  // Submit via fetch()
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (errBox) errBox.innerHTML = '';

    const submitBtn = form.querySelector('[type="submit"]');
    const originalText = submitBtn.textContent;

    // Validasi sisi klien: berkas foto wajib dipilih
    const fotoInput = form.querySelector('input[type="file"][name="foto"]');
    if (!fotoInput || !fotoInput.files || fotoInput.files.length === 0) {
      if (errBox) {
        errBox.innerHTML = '<ul class="ajax-error-list"><li><strong>Foto:</strong> Foto barang wajib diunggah.</li></ul>';
      }
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = 'Mengunggah…';

    try {
      const formData = new FormData(form);
      const res = await fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': formData.get('csrfmiddlewaretoken') },
      });

      if (res.status === 201) {
        closeModal();
        // Muat ulang daftar barang via AJAX
        await fetchBarang(getCurrentFilterParams());
        showNotification('Barang berhasil diunggah!', 'success');
      } else {
        const data = await res.json();
        if (errBox && data.errors) {
          const msgs = Object.entries(data.errors)
            .flatMap(([field, errs]) => errs.map((err) => `<li><strong>${escapeHtml(field)}:</strong> ${escapeHtml(err)}</li>`))
            .join('');
          errBox.innerHTML = `<ul class="ajax-error-list">${msgs}</ul>`;
        } else {
          errBox.innerHTML = '<p class="form-error">Periksa kembali isian formulir Anda.</p>';
        }
      }
    } catch (err) {
      console.error('[katalog.js] submit error:', err);
      if (errBox) errBox.innerHTML = '<p class="form-error">Terjadi kesalahan pada server. Coba lagi.</p>';
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = originalText;
    }
  });
}

// Notification Toast 

function showNotification(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);

  requestAnimationFrame(() => toast.classList.add('toast-show'));
  setTimeout(() => {
    toast.classList.remove('toast-show');
    setTimeout(() => toast.remove(), 400);
  }, 3000);
}

//  Initialization 
document.addEventListener('DOMContentLoaded', () => {
  initToolbarControls();
  initTambahBarangModal();
});
