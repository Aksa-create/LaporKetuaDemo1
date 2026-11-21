
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
