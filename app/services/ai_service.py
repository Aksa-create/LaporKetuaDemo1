
"""Safe AI helpers. The app remains usable when no trained model exists."""

import os
import math
import logging
from functools import lru_cache

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.pipeline import FeatureUnion
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory


logger = logging.getLogger(__name__)

# Inisialisasi stemmer bahasa Indonesia
stemmer_factory = StemmerFactory()
stemmer = stemmer_factory.create_stemmer()

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "ml_models",
    "report_classifier.joblib"
)


@lru_cache(maxsize=1)
def load_ai_model():
    """
    Memuat model AI satu kali dan menyimpan hasilnya dalam cache.
    Model tidak perlu dimuat ulang setiap ada laporan baru.
    """

    if not os.path.isfile(MODEL_PATH):
        logger.warning("File model AI tidak ditemukan: %s", MODEL_PATH)
        return None

    try:
        bundle = joblib.load(MODEL_PATH)

        if not isinstance(bundle, dict):
            raise ValueError("Format bundle model AI tidak valid.")

        if "model" not in bundle or "vectorizer" not in bundle:
            raise ValueError(
                "Bundle model AI tidak memiliki model atau vectorizer."
            )

        logger.info("Model AI berhasil dimuat.")
        return bundle["model"], bundle["vectorizer"]

    except Exception:
        logger.exception("Gagal memuat model AI.")
        return None




def keyword_fallback(title, description):
    text = f"{title or ''} {description or ''}".lower()

    # Normalisasi sederhana
    text = text.replace("-", " ")
    text = text.replace("/", " ")
    text = " ".join(text.split())

    rules = {

        # =====================================================
        # 1. LAMPU JALAN MATI / RUSAK
        # =====================================================
        "Lampu Jalan Mati": [
            # Lampu jalan
            "lampu jalan mati",
            "lampu jalan padam",
            "lampu jalan rusak",
            "lampu jalan tidak menyala",
            "lampu jalan tidak hidup",
            "lampu jalan tidak berfungsi",
            "lampu jalan redup",
            "lampu jalan berkedip",
            "lampu jalan kelap kelip",
            "lampu jalan mati total",
            "lampu jalan putus",

            # PJU
            "lampu pju mati",
            "lampu pju padam",
            "lampu pju rusak",
            "pju mati",
            "pju padam",
            "pju rusak",
            "pju tidak menyala",
            "pju tidak berfungsi",
            "penerangan pju mati",

            # Penerangan lingkungan
            "penerangan jalan mati",
            "penerangan jalan padam",
            "penerangan jalan rusak",
            "penerangan jalan tidak menyala",
            "penerangan jalan tidak berfungsi",
            "penerangan gang mati",
            "penerangan gang padam",
            "penerangan lingkungan mati",
            "penerangan lingkungan padam",

            # Variasi bahasa warga
            "lampu mati",
            "lampu padam",
            "lampu rusak",
            "lampu tidak menyala",
            "lampu tidak hidup",
            "lampu tidak berfungsi",
            "lampu kurang terang",
            "lampu redup",
            "lampu berkedip",
            "lampu kelap kelip",
            "lampu kedip kedip",
            "lampu sering mati",
            "lampu mati total",
            "lampu malam mati",
            "lampu gang mati",
            "lampu gang padam",
            "lampu lorong mati",
            "lampu lorong padam",
            "lampu taman mati",
            "lampu taman padam",
            "tiang lampu mati",
            "tiang penerangan mati",
            "jalan gelap",
            "gang gelap",
            "lorong gelap",
            "jalan tidak terang",
            "gang tidak terang"
        ],

        # =====================================================
        # 2. KEAMANAN LINGKUNGAN
        # =====================================================
        "Keamanan Lingkungan": [

            # Hewan liar / hewan berbahaya
            "ular masuk rumah",
            "uler masuk rumah",
            "ular masuk",
            "uler masuk",
            "ular di rumah",
            "uler di jalan",
            "ular di gang",
            "ular di halaman",
            "ular di selokan",
            "ular di plafon",
            "ular di atap",
            "ular di kamar",
            "ular di dapur",
            "ular ditemukan",
            "ular berkeliaran",
            "ular berbisa",
            "ular besar",
            "ular muncul",
            "ular melintas",
            "ular dekat rumah",
            "ular dekat warga",
            "ular di lingkungan",
            "uler ditemukan",
            "uler berkeliaran",
            "uler berbisa",
            "uler besar",
            "uler muncul",
            "uler melintas",

            "biawak masuk rumah",
            "biawak berkeliaran",
            "biawak masuk",
            "biawak",
            "buaya masuk",
            "buaya berkeliaran",
            "buaya",
            "monyet masuk rumah",
            "monyet berkeliaran",
            "monyet",
            "kera berkeliaran",
            "kera",
            "musang masuk",
            "musang",
            "hewan liar masuk rumah",
            "binatang liar masuk rumah",
            "hewan liar",
            "binatang liar",
            "satwa liar",
            "hewan berbahaya",
            "binatang berbahaya",
            "hewan masuk rumah",
            "binatang masuk rumah",
            "hewan berkeliaran",
            "binatang berkeliaran",
            "hewan menyerang warga",
            "hewan menggigit warga",
            "hewan agresif",
            "hewan lepas",
            "hewan kabur",
            "hewan peliharaan lepas",
            "hewan terlantar",
            "anjing liar",
            "anjing galak",
            "anjing menyerang",
            "anjing menggigit",
            "anjing berkeliaran",
            "anjing lepas",
            "kucing liar",
            "kucing berkeliaran",
            "tikus besar",
            "lebah masuk",
            "tawon masuk",
            "tawon menyerang",
            "sarang tawon",
            "sarang lebah",
            "sarang serangga berbahaya",

            # Tawuran / perkelahian / keributan
            "tawuran antar warga",
            "tawuran antar pelajar",
            "tawuran antar kelompok",
            "tawuran antar kampung",
            "tawuran antar gang",
            "tawuran pelajar",
            "tawuran remaja",
            "tawuran warga",
            "tawuran kelompok",
            "tawuran di jalan",
            "tawuran malam",
            "tawuran",
            "tauran",
            "perkelahian warga",
            "perkelahian antar warga",
            "perkelahian kelompok",
            "perkelahian",
            "berkelahi",
            "berantem warga",
            "berantem kelompok",
            "anak anak berantem",
            "anak berantem",
            "warga berantem",
            "warga berkelahi",
            "orang berantem",
            "orang berkelahi",
            "saling pukul",
            "pukul pukulan",
            "baku hantam",
            "adu fisik",
            "keributan antar warga",
            "keributan warga",
            "keributan kelompok",
            "keributan di jalan",
            "keributan malam",
            "keributan",
            "ribut ribut",
            "warga ribut",
            "orang ribut",
            "ribut",
            "cekcok antar warga",
            "cekcok",
            "adu mulut",
            "pertengkaran",
            "pertikaian",
            "konflik antar warga",
            "konflik warga",
            "gangguan ketertiban",
            "gangguan keamanan",
            "gangguan kamtibmas",

            # Pencurian / kehilangan
            "pencurian kendaraan",
            "pencurian motor",
            "pencurian mobil",
            "pencurian sepeda",
            "pencurian helm",
            "pencurian hp",
            "pencurian handphone",
            "pencurian barang",
            "pencurian rumah",
            "pencurian kabel",
            "pencurian",
            "motor dicuri",
            "mobil dicuri",
            "sepeda dicuri",
            "helm dicuri",
            "hp dicuri",
            "barang dicuri",
            "motor digondol",
            "mobil digondol",
            "kendaraan digondol",
            "barang digondol",
            "motor hilang",
            "mobil hilang",
            "kendaraan hilang",
            "sepeda hilang",
            "helm hilang",
            "hp hilang",
            "handphone hilang",
            "ponsel hilang",
            "dompet hilang",
            "uang hilang",
            "barang hilang",
            "kehilangan motor",
            "kehilangan mobil",
            "kehilangan kendaraan",
            "kehilangan sepeda",
            "kehilangan helm",
            "kehilangan hp",
            "kehilangan barang",
            "rumah dibobol",
            "rumah kemalingan",
            "rumah dimasuki maling",
            "rumah disatroni",
            "rumah disusupi",
            "maling masuk rumah",
            "maling motor",
            "maling mobil",
            "maling kendaraan",
            "maling rumah",
            "maling",
            "kemalingan",
            "pencuri",
            "mencuri",
            "perampokan",
            "dirampok",
            "begal",
            "pembegalan",
            "copet",
            "jambret",
            "penjambretan",
            "curi",

            # Gangguan keamanan lainnya
            "orang mencurigakan",
            "sosok mencurigakan",
            "kelompok mencurigakan",
            "gerombolan mencurigakan",
            "aktivitas mencurigakan",
            "gangguan keamanan lingkungan",
            "gangguan keamanan warga",
            "gangguan ketertiban umum",
            "gangguan ketertiban warga",
            "gangguan keamanan",
            "vandalisme",
            "perusakan",
            "merusak fasilitas",
            "merusak lingkungan",
            "mengancam warga",
            "mengancam",
            "ancaman",
            "intimidasi",
            "penganiayaan",
            "kekerasan fisik",
            "kekerasan terhadap warga",
            "kekerasan",
            "orang mabuk",
            "pemabuk",
            "mabuk di jalan",
            "mabuk berkeliaran",
            "penyusup",
            "masuk tanpa izin",
            "orang masuk tanpa izin"
        ],

        # =====================================================
        # 3. JALAN RUSAK
        # =====================================================
        "Jalan Rusak": [
            # Lubang dan kerusakan aspal
            "jalan berlubang",
            "lubang jalan",
            "jalan bolong",
            "jalan rusak parah",
            "jalan rusak",
            "aspal berlubang",
            "aspal rusak",
            "aspal pecah",
            "aspal mengelupas",
            "aspal terkelupas",
            "jalan terkelupas",
            "jalan pecah",
            "jalan retak retak",
            "jalan retak",
            "jalan tidak rata",
            "jalan bergelombang",
            "jalan turun",
            "jalan amblas",
            "jalan ambles",
            "jalan longsor",
            "jalan terputus",
            "jalan tidak layak",
            "jalan sulit dilalui",
            "jalan susah dilalui",
            "akses jalan rusak",

            # Gang dan trotoar
            "gang berlubang",
            "gang rusak",
            "gang amblas",
            "gang ambles",
            "gang retak",
            "gang tidak rata",
            "trotoar berlubang",
            "trotoar pecah",
            "trotoar rusak",
            "trotoar amblas",
            "trotoar ambles",
            "trotoar retak",
            "trotoar tidak rata",

            # Paving
            "paving rusak",
            "paving pecah",
            "paving berlubang",
            "paving amblas",
            "paving ambles",
            "paving tidak rata",

            # Kondisi permukaan jalan
            "jalan licin",
            "jalan becek",
            "jalan berlumpur",
            "jalan berdebu",
            "permukaan jalan rusak",
            "permukaan jalan tidak rata",
            "jalan rusak akibat hujan",
            "jalan rusak akibat banjir",
            "jalan rusak akibat longsor"
        ],

        # =====================================================
        # 4. SAMPAH MENUMPUK
        # =====================================================
        "Sampah Menumpuk": [
            # Penumpukan
            "sampah menumpuk",
            "tumpukan sampah",
            "sampah numpuk",
            "sampah berserakan",
            "sampah meluap",
            "sampah banyak",
            "sampah menimbun",
            "sampah tertumpuk",
            "sampah menumpuk tinggi",
            "sampah menumpuk di jalan",
            "sampah menumpuk di gang",
            "sampah menumpuk di depan rumah",
            "sampah menumpuk di lingkungan",

            # Pengangkutan
            "sampah tidak diangkut",
            "sampah belum diangkut",
            "sampah telat diangkut",
            "sampah terlambat diangkut",
            "sampah tidak diambil",
            "sampah belum diambil",
            "sampah tidak dibersihkan",
            "sampah terlantar",
            "sampah menunggu diangkut",

            # Tempat sampah
            "tempat sampah penuh",
            "bak sampah penuh",
            "tong sampah penuh",
            "tps penuh",
            "tps meluap",
            "tempat sampah meluap",
            "bak sampah meluap",
            "tong sampah meluap",
            "tempat pembuangan sampah penuh",

            # Sampah dan bau
            "sampah bau",
            "bau sampah",
            "sampah busuk",
            "sampah menyengat",
            "sampah di jalan",
            "sampah di selokan",
            "sampah di got",
            "sampah di parit",
            "sampah di pinggir jalan",
            "sampah di depan rumah",
            "sampah di lingkungan",
            "sampah plastik",
            "sampah rumah tangga",
            "limbah rumah tangga",
            "buang sampah sembarangan",
            "membuang sampah sembarangan",
            "sampah dibuang sembarangan",
            "sampah liar",
            "sampah tidak terurus",

            # Sampah khusus
            "limbah padat",
            "limbah domestik",
            "limbah rumah",
            "sampah makanan",
            "sampah organik",
            "sampah anorganik",
            "sampah elektronik",
            "sampah kemasan",
            "sampah botol",
            "sampah kardus"
        ],

        # =====================================================
        # 5. SALURAN AIR TERSUMBAT
        # =====================================================
        "Saluran Air Tersumbat": [
            # Saluran tersumbat
            "saluran air tersumbat",
            "saluran tersumbat",
            "selokan tersumbat",
            "got tersumbat",
            "drainase tersumbat",
            "gorong gorong tersumbat",
            "parit tersumbat",
            "saluran air mampet",
            "saluran mampet",
            "selokan mampet",
            "got mampet",
            "drainase mampet",
            "gorong gorong mampet",
            "parit mampet",
            "saluran air buntu",
            "saluran buntu",
            "selokan buntu",
            "got buntu",
            "drainase buntu",
            "gorong gorong buntu",
            "parit buntu",

            # Air tidak mengalir
            "air tidak mengalir",
            "air sulit mengalir",
            "air tersendat",
            "aliran air tersendat",
            "aliran saluran tersendat",
            "saluran tidak mengalir",
            "selokan tidak mengalir",
            "got tidak mengalir",
            "drainase tidak mengalir",
            "air saluran tidak mengalir",

            # Saluran dipenuhi sampah
            "saluran penuh sampah",
            "selokan penuh sampah",
            "got penuh sampah",
            "parit penuh sampah",
            "drainase penuh sampah",
            "gorong gorong penuh sampah",
            "sumbatan saluran",
            "sampah menyumbat saluran",
            "sampah menyumbat selokan",
            "sampah menyumbat got",
            "sampah menyumbat parit",
            "sampah menyumbat drainase",
            "saluran tersumbat plastik",
            "selokan tersumbat plastik",
            "got tersumbat plastik",

            # Kondisi saluran
            "selokan kotor",
            "got kotor",
            "parit kotor",
            "drainase kotor",
            "saluran air kotor",
            "selokan penuh",
            "got penuh",
            "parit penuh",
            "saluran penuh",
            "gorong gorong penuh"
        ],

        # =====================================================
        # 6. POHON TUMBANG
        # =====================================================
        "Pohon Tumbang": [
            "pohon tumbang",
            "pohon roboh",
            "pohon ambruk",
            "pohon jatuh",
            "pohon hampir tumbang",
            "pohon mau tumbang",
            "pohon rawan tumbang",
            "pohon miring",
            "pohon condong",
            "pohon patah",
            "pohon besar tumbang",
            "pohon besar roboh",
            "pohon besar ambruk",
            "pohon menimpa rumah",
            "pohon menimpa kendaraan",
            "pohon menimpa jalan",
            "pohon menimpa warga",
            "pohon menutup jalan",
            "pohon menghalangi jalan",
            "pohon menghalangi akses",
            "pohon jatuh ke jalan",
            "pohon jatuh ke rumah",
            "pohon jatuh menimpa",
            "pohon tumbang ke jalan",
            "pohon tumbang ke rumah",
            "pohon tumbang menutup jalan",
            "batang pohon jatuh",
            "batang pohon patah",
            "dahan patah",
            "dahan jatuh",
            "ranting patah",
            "ranting jatuh",
            "cabang patah",
            "cabang jatuh",
            "ranting menimpa",
            "dahan menimpa",
            "pohon rusak akibat angin",
            "pohon tumbang akibat angin",
            "pohon roboh akibat angin",
            "pohon tumbang akibat hujan"
        ],

        # =====================================================
        # 7. FASILITAS UMUM RUSAK
        # =====================================================
        "Fasilitas Umum Rusak": [
            # Fasilitas umum
            "fasilitas umum rusak",
            "fasilitas rusak",
            "fasilitas tidak berfungsi",
            "fasilitas tidak bisa digunakan",
            "fasilitas tidak dapat digunakan",
            "fasilitas umum tidak berfungsi",
            "fasilitas umum tidak bisa digunakan",

            # Pos keamanan
            "pos ronda rusak",
            "poskamling rusak",
            "pos keamanan rusak",
            "pos ronda roboh",
            "poskamling roboh",

            # Pagar dan bangunan
            "pagar rusak",
            "pagar roboh",
            "pagar jebol",
            "pagar bolong",
            "pagar ambruk",
            "tembok roboh",
            "tembok retak",
            "tembok rusak",
            "dinding retak",
            "dinding rusak",
            "bangunan umum rusak",
            "gedung umum rusak",
            "bangunan roboh",
            "bangunan ambruk",
            "plafon rusak",
            "plafon roboh",
            "atap bocor",
            "atap rusak",
            "atap roboh",
            "atap ambruk",

            # Taman dan fasilitas olahraga
            "taman rusak",
            "taman tidak terawat",
            "lapangan rusak",
            "lapangan berlubang",
            "lapangan retak",
            "alat bermain rusak",
            "permainan rusak",
            "ayunan rusak",
            "perosotan rusak",
            "alat olahraga rusak",
            "bangku taman rusak",
            "bangku rusak",
            "kursi rusak",

            # Toilet dan air
            "toilet umum rusak",
            "wc umum rusak",
            "toilet rusak",
            "wc rusak",
            "kran rusak",
            "keran rusak",
            "pipa bocor",
            "pipa rusak",
            "pipa pecah",
            "hydrant rusak",

            # Jalan dan fasilitas pelengkap
            "halte rusak",
            "jembatan rusak",
            "jembatan retak",
            "jembatan ambruk",
            "jembatan roboh",
            "jembatan berlubang",
            "rambu jalan rusak",
            "rambu rusak",
            "cermin tikungan rusak",
            "cermin jalan rusak",
            "tiang rusak",
            "tiang roboh",
            "tiang ambruk",
            "papan informasi rusak",
            "papan petunjuk rusak",
            "papan nama rusak",
            "pintu fasilitas umum rusak"
        ],

        # =====================================================
        # 8. PASCA KEBAKARAN / PENANGANAN PUING
        # =====================================================
        "Pasca Kebakaran / Penanganan Puing": [
            "pasca kebakaran",
            "bekas kebakaran",
            "sisa kebakaran",
            "puing kebakaran",
            "abu kebakaran",
            "limbah kebakaran",
            "reruntuhan kebakaran",
            "sisa pembakaran rumah",
            "sisa pembakaran bangunan",
            "sisa pembakaran",
            "puing bekas kebakaran",
            "puing rumah terbakar",
            "puing bangunan terbakar",
            "puing bangunan",
            "rumah terbakar",
            "rumah kebakaran",
            "kebakaran rumah",
            "kebakaran gedung",
            "kebakaran toko",
            "kebakaran warung",
            "kebakaran kontrakan",
            "kebakaran kos",
            "kebakaran kost",
            "kebakaran kendaraan",
            "kebakaran motor",
            "kebakaran mobil",
            "kebakaran dapur",
            "kebakaran listrik",
            "kebakaran kabel",
            "kebakaran sampah",
            "terjadi kebakaran",
            "terkena kebakaran",
            "habis terbakar",
            "bangunan terbakar",
            "gedung terbakar",
            "warung terbakar",
            "toko terbakar",
            "kontrakan terbakar",
            "kos terbakar",
            "kost terbakar",
            "kendaraan terbakar",
            "motor terbakar",
            "mobil terbakar",
            "sisa arang kebakaran"
        ],

        # =====================================================
        # 9. LAINNYA
        # =====================================================
        "Lainnya": [
            # Kebisingan
            "gangguan suara",
            "suara bising",
            "suara berisik",
            "kebisingan",
            "berisik",
            "musik keras",
            "sound system keras",
            "speaker keras",
            "suara speaker keras",
            "suara musik keras",
            "suara mengganggu",
            "suara mengganggu warga",
            "suara kendaraan bising",
            "knalpot bising",
            "knalpot berisik",
            "knalpot racing",
            "suara mesin keras",
            "kebisingan lingkungan",
            "kebisingan malam",

            # Bau
            "bau menyengat",
            "bau tidak sedap",
            "bau busuk",
            "bau tidak enak",
            "bau menyiksa",
            "bau mengganggu",
            "bau lingkungan",
            "bau limbah",
            "bau got",
            "bau selokan",
            "bau bangkai",
            "bau kotoran",

            # Polusi dan asap
            "polusi udara",
            "asap tebal",
            "asap kendaraan",
            "asap pembakaran",
            "pembakaran sampah",
            "membakar sampah",
            "pembakaran liar",
            "polusi",
            "debu berlebihan",
            "debu mengganggu",
            "udara tercemar",

            # Parkir dan hambatan
            "parkir liar",
            "parkir sembarangan",
            "parkir mengganggu",
            "kendaraan menghalangi jalan",
            "kendaraan menghalangi akses",
            "kendaraan parkir sembarangan",
            "mobil parkir sembarangan",
            "motor parkir sembarangan",
            "pedagang menghalangi jalan",
            "pedagang menghalangi akses",
            "pedagang liar",
            "dagangan menghalangi jalan",
            "barang menghalangi jalan",
            "barang menghalangi akses",
            "akses jalan terhalang",
            "jalan terhalang",

            # Genangan / banjir
            "banjir di jalan",
            "banjir di gang",
            "banjir di rumah",
            "banjir masuk rumah",
            "rumah kebanjiran",
            "jalan kebanjiran",
            "gang kebanjiran",
            "genangan air",
            "air menggenang",
            "jalan tergenang",
            "gang tergenang",
            "rumah tergenang",
            "halaman tergenang",
            "genangan di jalan",
            "genangan di gang",
            "genangan di rumah",
            "genangan di halaman",
            "air masuk rumah",
            "air masuk jalan",
            "air meluap ke jalan",
            "air meluap ke rumah",
            "air meluap",
            "saluran meluap",
            "got meluap",
            "selokan meluap",
            "parit meluap",
            "drainase meluap",
            "banjir lokal",
            "banjir kecil",
            "banjir akibat hujan",
            "banjir setelah hujan",
            "terendam air",
            "jalan terendam",
            "rumah terendam",
            "lingkungan terendam",

            # Gangguan lingkungan lainnya
            "gangguan lingkungan",
            "masalah lingkungan",
            "gangguan warga",
            "masalah warga",
            "gangguan kenyamanan",
            "gangguan ketenangan",
            "gangguan ketenangan warga",
            "masalah sosial",
            "gangguan sosial",
            "lingkungan tidak nyaman",
            "lingkungan terganggu",
            "masalah lain"
        ]
    }

    for category, keywords in rules.items():
        if any(keyword.strip() in text for keyword in keywords):
            return category

    return None



def calculate_rule_scores(title, description):
    """
    Menghitung skor kecocokan rules untuk seluruh kategori.
    Skor belum dinormalisasi.
    """

    text = f"{title or ''} {description or ''}".lower()

    rules = {
        "Lampu Jalan Mati": {
            "specific": [
                "lampu jalan mati",
                "lampu penerangan jalan mati",
                "lampu pju mati",
                "lampu jalan tidak menyala",
                "penerangan jalan tidak berfungsi",
            ],
            "medium": [
                "lampu jalan",
                "lampu pju",
                "penerangan jalan",
            ],
            "general": [
                "lampu mati",
                "lampu rusak",
            ],
        },

        "Keamanan Lingkungan": {
            "specific": [
                "pencurian motor",
                "motor dicuri",
                "motor hilang",
                "tawuran warga",
                "aksi tawuran",
                "orang mencurigakan",
                "ular masuk rumah",
                "uler masuk rumah",
                "biawak masuk rumah",
                "pencuri tertangkap",
                "kemalingan",
            ],
            "medium": [
                "pencurian",
                "mencuri",
                "tawuran",
                "tauran",
                "keributan",
                "perkelahian",
                "hewan liar",
                "ular",
                "uler",
                "biawak",
                "buaya",
                "maling",
                "kemalingan",
            ],
            "general": [
                "keamanan",
                "mencurigakan",
                "berkelahi",
            ],
        },

        "Jalan Rusak": {
            "specific": [
                "jalan berlubang",
                "jalan rusak parah",
                "aspal terkelupas",
                "jalan ambles",
                "jalan amblas",
                "lubang di jalan",
            ],
            "medium": [
                "jalan rusak",
                "aspal rusak",
                "jalan retak",
                "jalan bergelombang",
                "trotoar rusak",
            ],
            "general": [
                "berlubang",
                "ambles",
                "amblas",
            ],
        },

        "Sampah Menumpuk": {
            "specific": [
                "sampah menumpuk",
                "tumpukan sampah",
                "sampah tidak diangkut",
                "sampah berserakan",
                "tempat sampah penuh",
                "penumpukan sampah",
            ],
            "medium": [
                "sampah",
                "limbah rumah tangga",
                "sampah plastik",
                "sampah organik",
            ],
            "general": [
                "bau sampah",
                "sampah bau",
            ],
        },

        "Saluran Air Tersumbat": {
            "specific": [
                "selokan tersumbat",
                "saluran air tersumbat",
                "drainase tersumbat",
                "got tersumbat",
                "gorong gorong tersumbat",
                "saluran mampet",
                "selokan mampet",
            ],
            "medium": [
                "selokan",
                "saluran air",
                "drainase",
                "got",
                "gorong gorong",
            ],
            "general": [
                "mampet",
                "tersumbat",
            ],
        },

        "Pohon Tumbang": {
            "specific": [
                "pohon tumbang",
                "pohon roboh",
                "pohon jatuh",
                "pohon menimpa rumah",
                "pohon menimpa kendaraan",
            ],
            "medium": [
                "dahan pohon patah",
                "ranting pohon patah",
                "pohon miring",
            ],
            "general": [
                "ranting patah",
                "dahan patah",
            ],
        },

        "Fasilitas Umum Rusak": {
            "specific": [
                "fasilitas umum rusak",
                "kursi taman rusak",
                "bangku taman rusak",
                "halte rusak",
                "pos ronda rusak",
                "jembatan rusak",
                "pagar rusak",
                "fasilitas publik rusak",
            ],
            "medium": [
                "pos ronda",
                "halte",
                "jembatan",
                "pagar",
                "bangku taman",
                "fasilitas umum",
            ],
            "general": [
                "fasilitas rusak",
                "fasilitas publik",
            ],
        },

        "Pasca Kebakaran / Penanganan Puing": {
            "specific": [
                "bekas kebakaran",
                "puing kebakaran",
                "sisa kebakaran",
                "bangunan terbakar",
                "rumah terbakar",
                "puing bangunan",
                "sisa material kebakaran",
            ],
            "medium": [
                "kebakaran",
                "puing",
                "bekas terbakar",
                "sisa material",
            ],
            "general": [
                "arang",
                "material terbakar",
            ],
        },

        "Lainnya": {
            "specific": [
                "banjir di lingkungan",
                "genangan air di jalan",
                "air menggenangi jalan",
            ],
            "medium": [
                "banjir",
                "genangan",
                "air meluap",
            ],
            "general": [
                "masalah lingkungan",
            ],
        },
    }

    weights = {
        "specific": 5,
        "medium": 3,
        "general": 1,
    }

    scores = {}

    for category, keyword_groups in rules.items():

        category_score = 0

        for level, keywords in keyword_groups.items():

            weight = weights[level]

            matched_keywords = [
                keyword
                for keyword in keywords
                if keyword in text
            ]

            # Keyword yang sama tidak boleh dihitung berulang.
            category_score += len(set(matched_keywords)) * weight

        scores[category] = category_score

    return scores



def normalize_rule_scores(rule_scores):
    """
    Mengubah skor rules menjadi nilai 0 sampai 1.
    """

    total_score = sum(rule_scores.values())

    if total_score == 0:
        return {
            category: 0.0
            for category in rule_scores
        }

    return {
        category: score / total_score
        for category, score in rule_scores.items()
    }



def classify_report(title, description):
    print("=== DEBUG KLASIFIKASI ===")
    print("TITLE:", title)
    print("DESCRIPTION:", description)

    fallback_prediction = keyword_fallback(title, description)
    print("FALLBACK RESULT:", fallback_prediction)

    if fallback_prediction:
        print("RETURN FALLBACK:", fallback_prediction)
        return fallback_prediction, None, "keyword_fallback"

    bundle = load_ai_model()

    print("MODEL BUNDLE LOADED:", bundle is not None)

    if bundle is None:
        return None, None, "model_belum_tersedia"

    model, vectorizer = bundle
    text = f"{title or ''} {description or ''}"

    try:
        matrix = vectorizer.transform([text])
        prediction = model.predict(matrix)[0]

        confidence = None
        if hasattr(model, "predict_proba"):
            confidence = float(max(model.predict_proba(matrix)[0]))

        print("MODEL PREDICTION:", prediction)

        return prediction, confidence, "model"

    except Exception:
        logger.exception("Gagal melakukan prediksi kategori laporan.")
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
        logger.exception("Gagal menghitung kemiripan laporan.")
        return []

    return [
        (candidates[i], float(score))
        for i, score in enumerate(scores)
        if score >= threshold
    ]



def classify_with_ml_probabilities(title, description):
    """
    Mengambil probabilitas prediksi ML untuk seluruh kategori.
    Menggunakan model dan vectorizer yang sudah ada.
    """

    bundle = load_ai_model()

    if bundle is None:
        return None

    model, vectorizer = bundle

    text = f"{title or ''} {description or ''}"

    try:
        matrix = vectorizer.transform([text])

        # Model harus mendukung probabilitas
        if not hasattr(model, "predict_proba"):
            return None

        probabilities = model.predict_proba(matrix)[0]

        # Menghubungkan probabilitas dengan nama kategori
        classes = model.classes_

        results = {
            str(category): float(probability)
            for category, probability in zip(classes, probabilities)
        }

        return results

    except Exception:
        logger.exception("Gagal mengambil probabilitas ML.")
        return None



def hybrid_classification(title, description, ml_weight=0.65, rule_weight=0.35):
    """
    Menggabungkan probabilitas ML dan skor rules yang dinormalisasi.

    Returns:
        dict berisi kategori teratas, skor hybrid, dan seluruh skor.
    """

    # 1. Hitung skor rules
    raw_rule_scores = calculate_rule_scores(title, description)

    normalized_rule_scores = normalize_rule_scores(raw_rule_scores)

    # 2. Ambil probabilitas ML
    ml_scores = classify_with_ml_probabilities(title, description)

    if ml_scores is None:
        return {
            "status": "ml_unavailable",
            "category": None,
            "hybrid_score": None,
            "scores": {},
            "ml_scores": None,
            "rule_scores": normalized_rule_scores,
        }

    # 3. Gabungkan seluruh kategori dari ML dan rules
    all_categories = set(ml_scores) | set(normalized_rule_scores)

    hybrid_scores = {}

    # 4. Hitung Hybrid Score
    for category in all_categories:

        ml_score = ml_scores.get(category, 0.0)
        rule_score = normalized_rule_scores.get(category, 0.0)

        hybrid_score = (
            ml_weight * ml_score
            + rule_weight * rule_score
        )

        hybrid_scores[category] = hybrid_score

    # 5. Urutkan dari skor terbesar ke terkecil
    ranked_scores = sorted(
        hybrid_scores.items(),
        key=lambda item: item[1],
        reverse=True
    )

    # 6. Ambil kategori terbaik
    if ranked_scores:
        best_category, best_score = ranked_scores[0]
    else:
        best_category, best_score = None, None

    return {
        "status": "hybrid",
        "category": best_category,
        "hybrid_score": best_score,
        "scores": hybrid_scores,
        "ranked_scores": ranked_scores,
        "ml_scores": ml_scores,
        "rule_scores": normalized_rule_scores,
        "raw_rule_scores": raw_rule_scores,
        "weights": {
            "ml": ml_weight,
            "rules": rule_weight,
        },
    }


def display_hybrid_result(title, description, result):
    print("\n" + "=" * 65)
    print("              HASIL PENGUJIAN HYBRID CLASSIFICATION")
    print("=" * 65)

    print("\n[ INPUT LAPORAN ]")
    print(f"Judul       : {title}")
    print(f"Deskripsi   : {description}")

    print("\n[ HASIL KLASIFIKASI ]")
    print(f"Status      : {result['status']}")
    print(f"Kategori    : {result['category']}")
    print(f"Hybrid Score: {result['hybrid_score']:.6f}")

    print("\n[ BOBOT METODE ]")
    print(f"Machine Learning : {result['weights']['ml']:.0%}")
    print(f"Rule-Based      : {result['weights']['rules']:.0%}")

    print("\n[ RANKING HYBRID SCORE ]")
    print("-" * 65)
    print(f"{'Rank':<6}{'Kategori':<45}{'Score':>14}")
    print("-" * 65)

    for rank, (category, score) in enumerate(result["ranked_scores"], 1):
        print(f"{rank:<6}{category:<45}{score:>14.6f}")

    print("-" * 65)

    print("\n[ DETAIL SKOR ML DAN RULES ]")
    print("-" * 90)
    print(f"{'Kategori':<45}{'ML Score':>15}{'Rule Score':>15}")
    print("-" * 90)

    for category, hybrid_score in result["ranked_scores"]:
        ml_score = result["ml_scores"].get(category, 0)
        rule_score = result["rule_scores"].get(category, 0)

        print(
            f"{category:<45}"
            f"{ml_score:>15.6f}"
            f"{rule_score:>15.6f}"
        )

    print("-" * 90)
    print("=" * 65)
    print("                    PENGUJIAN SELESAI")
    print("=" * 65)
