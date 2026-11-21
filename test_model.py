
import os
import joblib

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "ml_models",
    "report_classifier.joblib"
)

# Memuat model dan vectorizer
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model tidak ditemukan: {MODEL_PATH}")

bundle = joblib.load(MODEL_PATH)
model = bundle["model"]
vectorizer = bundle["vectorizer"]


def test_prediction(title, description):
    text = f"{title} {description}"
    matrix = vectorizer.transform([text])

    prediction = model.predict(matrix)[0]

    print("\n" + "=" * 55)
    print("JUDUL       :", title)
    print("DESKRIPSI   :", description)
    print("-" * 55)
    print("HASIL PREDIKSI:", prediction)

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(matrix)[0]
        classes = model.classes_

        ranked = sorted(
            zip(classes, probabilities),
            key=lambda item: item[1],
            reverse=True
        )

        print("\nTOP 3 KATEGORI:")
        for category, probability in ranked[:3]:
            print(f"{category:40} {probability * 100:.2f}%")

    print("=" * 55)


# Contoh laporan baru untuk pengujian
test_cases = [
    (
        "Jalan berlubang di depan gang",
        "Jalan depan gang rumah saya berlubang besar "
        "dan beberapa pengendara hampir jatuh."
    ),
    (
        "Orang mencurigakan di sekitar pos ronda",
        "Tadi malam ada orang tidak dikenal mondar-mandir "
        "di sekitar pos ronda."
    ),
    (
        "Kursi taman rusak",
        "Kursi taman RW patah dan sudah tidak bisa digunakan."
    ),
    (
        "Bau menyengat di lingkungan warga",
        "Ada bau menyengat yang berasal dari belakang rumah warga."
    ),
    (
        "Gangguan aliran air bersih",
        "Air bersih di rumah warga tidak mengalir sejak pagi."
    ),

    (
        "Barang tertinggal",
        "Ada tas yang tertinggal di dekat balai warga dan belum "
        "diketahui siapa pemiliknya."
    ),

    (
        "Air got mampet",
        "Got depan rumah penuh lumpur dan sampah sampai airnya tidak bisa mengalir."
    ),
    (
        "Ada kabel listrik menjuntai",
        "Kabel listrik terlihat menjuntai rendah di dekat jalan dan membahayakan warga."
    ),
    (
        "Motor warga hilang",
        "Sepeda motor milik warga hilang saat diparkir di depan rumah."
    ),
    (
        "Atap balai warga bocor",
        "Ketika hujan turun, air masuk melalui atap balai warga yang bocor."
    ),
    (
        "Ada kucing liar",
        "Beberapa kucing liar masuk ke lingkungan permukiman dan mengacak-acak barang warga."
    ),
    (
        "Aktivitas pembangunan berisik",
        "Pekerjaan pembangunan rumah di lingkungan warga menimbulkan suara bising sejak pagi."
    ),
    (
        "Aspal jalan mengelupas",
        "Permukaan jalan di depan rumah mulai terkelupas dan membentuk lubang kecil."
    ),
    (
        "Puing bekas kebakaran",
        "Sisa material bangunan dan puing masih berserakan setelah terjadi kebakaran."
    )

]

print("\n=== PENGUJIAN MODEL AI LAPORKETUA ===")

for title, description in test_cases:
    test_prediction(title, description)

print("\n=== PENGUJIAN SELESAI ===")
