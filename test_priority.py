
from app.services.ai_service import recommend_priority

test_cases = [
    {
        "judul": "Jalan retak kecil",
        "kategori": "Jalan Rusak",
        "urgensi": "Rendah",
        "deskripsi": "Jalan mengalami retakan kecil dan masih bisa dilewati.",
        "expected": "Rendah"
    },
    {
        "judul": "Sampah menumpuk",
        "kategori": "Sampah Menumpuk",
        "urgensi": "Sedang",
        "deskripsi": "Sampah menumpuk di dekat tempat pembuangan warga.",
        "expected": "Sedang"
    },
    {
        "judul": "Lampu jalan mati",
        "kategori": "Lampu Jalan Mati",
        "urgensi": "Tinggi",
        "deskripsi": "Lampu jalan sudah mati selama beberapa malam.",
        "expected": "Tinggi"
    },
    {
        "judul": "Orang mencurigakan",
        "kategori": "Keamanan Lingkungan",
        "urgensi": "Sedang",
        "deskripsi": "Ada orang tidak dikenal mondar-mandir di lingkungan.",
        "expected": "Tinggi"
    },
    {
        "judul": "Pohon miring",
        "kategori": "Pohon Tumbang",
        "urgensi": "Sedang",
        "deskripsi": "Pohon di pinggir jalan terlihat semakin miring.",
        "expected": "Tinggi"
    },
    {
        "judul": "Pohon tumbang menimpa rumah",
        "kategori": "Pohon Tumbang",
        "urgensi": "Sedang",
        "deskripsi": "Pohon tumbang menimpa rumah warga dan membahayakan penghuni.",
        "expected": "Darurat"
    },
    {
        "judul": "Jalan berlubang membahayakan",
        "kategori": "Jalan Rusak",
        "urgensi": "Rendah",
        "deskripsi": "Jalan berlubang membahayakan pengendara yang melintas.",
        "expected": "Tinggi"
    },
    {
        "judul": "Banjir di lingkungan",
        "kategori": "Keamanan Lingkungan",
        "urgensi": "Tinggi",
        "deskripsi": "Banjir masuk ke rumah warga dan beberapa orang terjebak.",
        "expected": "Darurat"
    },
    {
        "judul": "Lampu taman mati",
        "kategori": "Lampu Jalan Mati",
        "urgensi": "Rendah",
        "deskripsi": "Lampu taman tidak menyala sejak kemarin.",
        "expected": "Rendah"
    }
]

print("\n=== PENGUJIAN AI RECOMMENDATION PRIORITY ===")

passed = 0

for i, case in enumerate(test_cases, start=1):
    result = recommend_priority(
        case["kategori"],
        case["urgensi"],
        case["deskripsi"]
    )

    status = "SESUAI" if result == case["expected"] else "TIDAK SESUAI"

    if result == case["expected"]:
        passed += 1

    print(f"\nPengujian {i}: {case['judul']}")
    print(f"Kategori          : {case['kategori']}")
    print(f"Urgensi pengguna  : {case['urgensi']}")
    print(f"Prioritas AI      : {result}")
    print(f"Target            : {case['expected']}")
    print(f"Hasil             : {status}")

print("\n==========================================")
print(f"Total pengujian : {len(test_cases)}")
print(f"Berhasil        : {passed}")
print(f"Tidak sesuai    : {len(test_cases) - passed}")
print(f"Persentase      : {passed / len(test_cases) * 100:.2f}%")
print("==========================================")
