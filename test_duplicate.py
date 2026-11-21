
from types import SimpleNamespace

from app.services.ai_service import find_duplicate_candidates


def make_report(title, description, category, rt, lat, lng):
    return SimpleNamespace(
        title=title,
        description=description,
        category=SimpleNamespace(name=category),
        rt_number=rt,
        latitude=lat,
        longitude=lng
    )


# Laporan pembanding yang sudah tersimpan
existing = [
    make_report(
        "Jalan berlubang di Gang Melati",
        "Jalan depan rumah RT 02 berlubang besar dan membahayakan pengendara.",
        "Jalan Rusak",
        "02",
        -6.152000,
        106.800000
    )
]


test_cases = [
    {
        "name": "Laporan benar-benar sama",
        "category": "Jalan Rusak",
        "rt": "02",
        "lat": -6.152000,
        "lng": 106.800000,
        "title": "Jalan berlubang di Gang Melati",
        "description": "Jalan depan rumah RT 02 berlubang besar dan membahayakan pengendara."
    },
    {
        "name": "Kalimat berbeda, masalah sama",
        "category": "Jalan Rusak",
        "rt": "02",
        "lat": -6.152010,
        "lng": 106.800010,
        "title": "Lubang besar di jalan Gang Melati",
        "description": "Pengendara kesulitan melintas karena aspal di depan rumah warga RT 02 rusak dan berlubang."
    },
    {
        "name": "Masalah berbeda, kategori sama",
        "category": "Jalan Rusak",
        "rt": "02",
        "lat": -6.152010,
        "lng": 106.800010,
        "title": "Aspal jalan retak",
        "description": "Permukaan aspal mulai retak dan mengelupas di beberapa bagian."
    },
    {
        "name": "Masalah sama, lokasi berbeda",
        "category": "Jalan Rusak",
        "rt": "02",
        "lat": -6.154000,
        "lng": 106.802000,
        "title": "Jalan berlubang di Gang Kenanga",
        "description": "Jalan di depan rumah RT 02 berlubang besar dan membahayakan pengendara."
    },
    {
        "name": "Kategori berbeda",
        "category": "Lainnya",
        "rt": "02",
        "lat": -6.152000,
        "lng": 106.800000,
        "title": "Jalan berlubang di Gang Melati",
        "description": "Jalan depan rumah RT 02 berlubang besar dan membahayakan pengendara."
    },
    {
        "name": "Lokasi sama, masalah berbeda",
        "category": "Jalan Rusak",
        "rt": "02",
        "lat": -6.152000,
        "lng": 106.800000,
        "title": "Aspal jalan retak dan mengelupas",
        "description": "Permukaan aspal mengalami retakan kecil dan mulai mengelupas di beberapa bagian."
    },
    {
        "name": "Lokasi sama, kalimat berbeda, masalah sama",
        "category": "Jalan Rusak",
        "rt": "02",
        "lat": -6.152000,
        "lng": 106.800000,
        "title": "Kerusakan jalan di depan rumah warga",
        "description": "Terdapat lubang pada permukaan jalan yang dapat membahayakan pengendara sepeda motor."
    },
    {
        "name": "Masalah sama, jarak sekitar 50 meter",
        "category": "Jalan Rusak",
        "rt": "02",
        "lat": -6.151550,
        "lng": 106.800000,
        "title": "Jalan berlubang di Gang Melati",
        "description": "Jalan depan rumah RT 02 berlubang besar dan membahayakan pengendara."
    },
    {
        "name": "Masalah sama, jarak sekitar 100 meter",
        "category": "Jalan Rusak",
        "rt": "02",
        "lat": -6.151100,
        "lng": 106.800000,
        "title": "Jalan berlubang di Gang Melati",
        "description": "Jalan depan rumah RT 02 berlubang besar dan membahayakan pengendara."
    },
    {
        "name": "RT berbeda, koordinat sama",
        "category": "Jalan Rusak",
        "rt": "05",
        "lat": -6.152000,
        "lng": 106.800000,
        "title": "Jalan berlubang di Gang Melati",
        "description": "Jalan depan rumah RT 02 berlubang besar dan membahayakan pengendara."
    }
]


print("\n=== PENGUJIAN DUPLICATE DETECTION ===")

passed = 0

for i, case in enumerate(test_cases, start=1):

    results = find_duplicate_candidates(
        case["title"],
        case["description"],
        case["category"],
        existing,
        rt_number=case["rt"],
        latitude=case["lat"],
        longitude=case["lng"]
    )

    print("\n" + "=" * 55)
    print(f"Pengujian {i}: {case['name']}")

    if results:
        print("Hasil: KANDIDAT DUPLIKAT DITEMUKAN")

        for report, score in results:
            print(f"Skor kemiripan teks: {score * 100:.2f}%")
            print(f"Laporan pembanding: {report.title}")
    else:
        print("Hasil: TIDAK ADA KANDIDAT DUPLIKAT")

    # Target hasil berdasarkan skenario
    expected_duplicate = i in {1, 2, 7, 8}

    actual_duplicate = bool(results)

    if actual_duplicate == expected_duplicate:
        print("Evaluasi: SESUAI TARGET")
        passed += 1
    else:
        print("Evaluasi: BELUM SESUAI TARGET")


print("\n" + "=" * 55)
print("=== RINGKASAN PENGUJIAN ===")
print(f"Total pengujian : {len(test_cases)}")
print(f"Sesuai target   : {passed}")
print(f"Tidak sesuai    : {len(test_cases) - passed}")
print(f"Kesesuaian      : {passed / len(test_cases) * 100:.2f}%")
print("=== PENGUJIAN SELESAI ===")
