"""Safe AI helpers. The app remains usable when no trained model exists."""
import os
import joblib
import math
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.pipeline import FeatureUnion
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory


# Inisialisasi stemmer bahasa Indonesia
stemmer_factory = StemmerFactory()
stemmer = stemmer_factory.create_stemmer()

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ml_models", "report_classifier.joblib")


def classify_report(title, description):
    if os.path.exists(MODEL_PATH):
        try:
            bundle = joblib.load(MODEL_PATH)
            model, vectorizer = bundle["model"], bundle["vectorizer"]
            text = f"{title} {description}"
            matrix = vectorizer.transform([text])
            prediction = model.predict(matrix)[0]
            confidence = float(max(model.predict_proba(matrix)[0])) if hasattr(model, "predict_proba") else None
            return prediction, confidence, "model"
        except Exception:
            pass
    # No fabricated prediction: ask the administrator to review the category.
    return None, None, "model_belum_tersedia"



def recommend_priority(category, urgency, description):
    text = (description or "").lower()

    # Skor dasar berdasarkan urgensi yang dipilih warga
    score = {
        "Rendah": 1,
        "Sedang": 2,
        "Tinggi": 3
    }.get(urgency, 2)

    # Kategori yang memerlukan perhatian lebih
    if category in {"Pohon Tumbang", "Keamanan Lingkungan"}:
        score += 2

    # Indikasi bahaya dalam deskripsi laporan
    danger_keywords = [
        "membahayakan",
        "kecelakaan",
        "terjebak",
        "kebakaran",
        "banjir",
        "menimpa"
    ]

    if any(word in text for word in danger_keywords):
        score += 2

    # Penentuan prioritas
    if score >= 5:
        return "Darurat"
    if score >= 3:
        return "Tinggi"
    if score == 2:
        return "Sedang"

    return "Rendah"


def _calculate_distance_m(lat1, lon1, lat2, lon2):
    """Menghitung jarak dua koordinat menggunakan rumus Haversine."""
    earth_radius = 6371000

    lat1, lon1, lat2, lon2 = map(
        math.radians,
        [lat1, lon1, lat2, lon2]
    )

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius * c

def normalize_report_text(text):
    """
    Membersihkan dan melakukan stemming teks laporan bahasa Indonesia.
    """
    text = (text or "").lower()

    # Stemming kata bahasa Indonesia
    text = stemmer.stem(text)

    return text

def find_duplicate_candidates(
    title,
    description,
    category_name,
    existing_reports,
    rt_number=None,
    latitude=None,
    longitude=None,
    threshold=0.30,
    max_distance_m=75
):
    """
    Mencari laporan yang berpotensi duplikat berdasarkan:
    - Kategori yang sama
    - RT yang sama
    - Jarak koordinat maksimal 75 meter
    - Kemiripan teks judul dan deskripsi
    """

    if latitude is None or longitude is None or rt_number is None:
        return []

    candidates = []

    for report in existing_reports:
        if not report.category:
            continue

        if report.category.name != category_name:
            continue

        if report.rt_number != rt_number:
            continue

        if report.latitude is None or report.longitude is None:
            continue

        try:
            distance = _calculate_distance_m(
                latitude,
                longitude,
                report.latitude,
                report.longitude
            )
        except (TypeError, ValueError):
            continue

        if distance <= max_distance_m:
            candidates.append(report)

    if not candidates:
        return []

    corpus = [
        normalize_report_text(f"{title} {description}")
    ] + [
        normalize_report_text(
         f"{report.title} {report.description}"
        )
        for report in candidates
    ]

    try:
        vectorizer = FeatureUnion([
            (
                "word",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    max_features=3000,
                    sublinear_tf=True
                )
            ),
            (
                "char",
                TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=(3, 5),
                    max_features=5000,
                    sublinear_tf=True
                )
            )
        ])

        matrix = vectorizer.fit_transform(corpus)

        scores = cosine_similarity(
            matrix[0:1],
            matrix[1:]
        ).flatten()

    except ValueError:
        return []

    return [
        (candidates[i], float(score))
        for i, score in enumerate(scores)
        if score >= threshold
    ]
