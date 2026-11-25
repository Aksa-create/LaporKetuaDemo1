
let deferredInstallPrompt = null;

const installButton = document.getElementById('installBtn');
const installedStatus = document.getElementById('installedStatus');

// Memeriksa apakah aplikasi sudah terpasang
function isAppInstalled() {
    return (
        window.matchMedia('(display-mode: standalone)').matches ||
        window.navigator.standalone === true
    );
}

// Memperbarui tampilan tombol
function updateInstallUI() {
    if (!installButton || !installedStatus) return;

    if (isAppInstalled()) {
        installButton.hidden = true;
        installedStatus.hidden = false;
    } else {
        installButton.hidden = false;
        installedStatus.hidden = true;
    }
}

// Browser menyediakan prompt instalasi
window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault();

    deferredInstallPrompt = event;

    updateInstallUI();
});

// Tombol Install Aplikasi
if (installButton) {
    installButton.addEventListener('click', async () => {

        // Jika browser mendukung prompt instalasi
        if (deferredInstallPrompt) {
            deferredInstallPrompt.prompt();

            const result = await deferredInstallPrompt.userChoice;

            if (result.outcome === 'accepted') {
                deferredInstallPrompt = null;
            }

            return;
        }

        // Petunjuk instalasi manual untuk browser tanpa prompt
        const isIOS =
            /iPad|iPhone|iPod/.test(navigator.userAgent) ||
            (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);

        if (isIOS) {
            alert(
                'Untuk memasang LaporKetua di iPhone:\n\n' +
                '1. Buka menu Share (Bagikan) di Safari.\n' +
                '2. Pilih Add to Home Screen (Tambah ke Layar Utama).\n' +
                '3. Tekan Add (Tambah).'
            );
        } else {
            alert(
                'Untuk memasang LaporKetua:\n\n' +
                '1. Buka menu browser (ikon tiga titik).\n' +
                '2. Cari opsi Install App atau Tambahkan ke layar utama.\n' +
                '3. Ikuti petunjuk instalasi.'
            );
        }
    });
}

// Instalasi berhasil
window.addEventListener('appinstalled', () => {
    deferredInstallPrompt = null;
    updateInstallUI();
});

// Periksa status saat halaman dibuka
updateInstallUI();

// Registrasi Service Worker
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker
            .register('/service-worker.js')
            .then((registration) => {
                console.log(
                    'Service Worker berhasil:',
                    registration.scope
                );
            })
            .catch((error) => {
                console.warn('Service Worker gagal:', error);
            });
    });
}



/* ==========================================
   SCROLL REVEAL - LAPORKETUA
   Berlaku untuk warga, petugas, dan admin
========================================== */

document.addEventListener('DOMContentLoaded', () => {

    // Hormati pengaturan reduced motion perangkat
    const reduceMotion = window.matchMedia(
        '(prefers-reduced-motion: reduce)'
    ).matches;

    if (reduceMotion) return;

    // Elemen UI yang akan dianimasikan
    const revealSelectors = [
        '.page-heading',
        '.dashboard-banner',
        '.petugas-topline',
        '.petugas-hero',
        '.stat-card',
        '.stat-card-modern',
        '.quick-card',
        '.quick-link',
        '.feature-card',
        '.chart-card',
        '.detail-card',
        '.form-panel',
        '.card-table',
        '.report-row',
        '.notification-row',
        '.install-hint',
        '.cta-strip',
        '.empty-state',
        '.ai-note',
        '.ai-note-modern',
        '.area-info-card',

        // Landing Page LaporKetua V2
        '.lk-hero-copy',
        '.lk-hero-visual',
        '.lk-location-mini',
        '.lk-install-banner',
        '.lk-section-heading',
        '.lk-feature-card',
        '.lk-process-card',
        '.lk-category-item',
        '.lk-final-section',

    ];

    const elements = document.querySelectorAll(
        `main ${revealSelectors.join(', main ')}`
    );

    // Jika browser tidak mendukung IntersectionObserver
    if (!('IntersectionObserver' in window)) return;

    // Hindari animasi bertumpuk pada elemen bersarang
    const revealElements = Array.from(elements).filter((element) => {
        return !element.parentElement.closest('.reveal-item');
    });

    // Pasang class dan urutan animasi
    const siblingCounters = new Map();

    revealElements.forEach((element) => {
        const parent = element.parentElement;
        const count = siblingCounters.get(parent) || 0;

        element.classList.add('reveal-item');
        element.style.setProperty(
            '--reveal-delay',
            `${Math.min(count * 90, 270)}ms`
        );

        siblingCounters.set(parent, count + 1);
    });

    // Amati elemen ketika masuk area layar
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.10,
        rootMargin: '0px 0px -35px 0px'
    });

    revealElements.forEach((element) => {
        observer.observe(element);
    });

});

