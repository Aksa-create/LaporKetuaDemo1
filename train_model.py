"""
Audit dan training model klasifikasi LaporKetua.

Jalankan dari root project:
    python train_model.py

Metode:
- Audit validasi struktur dataset.
- Membandingkan random split biasa dengan group-based split.
- Group dibuat dari kategori + jenis masalah pada kolom scenario
  (teks sebelum tanda titik koma pertama).
- Validation dan test group tidak muncul di training.
- Setelah evaluasi, model produksi dilatih ulang menggunakan seluruh data.

Input:
    dataset/dataset_sintetis_laporketua_1800_bersih.csv

Output:
    ml_models/report_classifier.joblib
    ml_models/training_report.json
    ml_models/confusion_matrix_group_test.png
"""

import json
import re
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split, StratifiedGroupKFold


ROOT_DIR = Path(__file__).resolve().parent
DATASET_PATH = ROOT_DIR / "dataset" / "dataset_sintetis_laporketua_1800_bersih.csv"
MODEL_DIR = ROOT_DIR / "ml_models"
MODEL_PATH = MODEL_DIR / "report_classifier.joblib"
REPORT_PATH = MODEL_DIR / "training_report.json"
CONFUSION_MATRIX_PATH = MODEL_DIR / "confusion_matrix_group_test.png"

EXPECTED_COLUMNS = {
    "sample_id", "title", "description", "category",
    "language_style", "scenario", "source_type",
}
EXPECTED_CATEGORIES = {
    "Jalan Rusak",
    "Sampah Menumpuk",
    "Lampu Jalan Mati",
    "Saluran Air Tersumbat",
    "Pohon Tumbang",
    "Fasilitas Umum Rusak",
    "Keamanan Lingkungan",
    "Pasca Kebakaran / Penanganan Puing",
    "Lainnya",
}
RANDOM_STATE = 42


def stop(message):
    print(f"\n[ERROR] {message}")
    sys.exit(1)


def load_dataset():
    if not DATASET_PATH.exists():
        stop(f"Dataset tidak ditemukan: {DATASET_PATH}")

    try:
        df = pd.read_csv(
            DATASET_PATH, sep=None, engine="python", encoding="utf-8-sig"
        )
    except Exception as exc:
        stop(f"Gagal membaca CSV: {exc}")

    df.columns = df.columns.astype(str).str.strip()
    missing = EXPECTED_COLUMNS - set(df.columns)
    if missing:
        stop(f"Kolom wajib tidak ditemukan: {', '.join(sorted(missing))}")

    for column in EXPECTED_COLUMNS:
        df[column] = df[column].fillna("").astype(str).str.strip()

    if len(df) != 1800:
        stop(f"Jumlah data harus 1.800, ditemukan {len(df)}.")
    if df["sample_id"].eq("").any() or df["sample_id"].duplicated().any():
        stop("sample_id kosong atau tidak unik.")
    if df[["title", "description", "category", "scenario"]].eq("").any().any():
        stop("Ada title, description, category, atau scenario yang kosong.")
    if set(df["category"]) != EXPECTED_CATEGORIES:
        stop(
            "Label kategori tidak sesuai.\n"
            f"Hilang: {sorted(EXPECTED_CATEGORIES - set(df['category']))}\n"
            f"Tidak dikenal: {sorted(set(df['category']) - EXPECTED_CATEGORIES)}"
        )

    counts = df["category"].value_counts()
    if not (counts == 200).all():
        stop(f"Jumlah per kategori harus 200:\n{counts}")
    if not df["language_style"].isin(["formal", "sehari-hari"]).all():
        stop("language_style harus 'formal' atau 'sehari-hari'.")
    if not df["source_type"].eq("synthetic").all():
        stop("Semua source_type dataset ini harus 'synthetic'.")

    broken = (
        df["title"].str.contains(r"<built-in method|0x[0-9a-fA-F]+", na=False)
        | df["description"].str.contains(
            r"<built-in method|0x[0-9a-fA-F]+", na=False
        )
    )
    if broken.any():
        stop(f"Ditemukan {int(broken.sum())} baris mengandung teks error Python.")

    normalized = (
        df["title"].str.lower().str.replace(r"\s+", " ", regex=True)
        + " "
        + df["description"].str.lower().str.replace(r"\s+", " ", regex=True)
    )
    duplicates = int(normalized.duplicated().sum())
    if duplicates:
        stop(f"Ditemukan {duplicates} pasangan title+description identik.")

    return df


def build_text(df):
    return (df["title"] + " " + df["description"]).str.strip()


def build_groups(df):
    # Kolom scenario saat ini berbentuk: "jenis masalah; lokasi; waktu".
    # Kelompok berdasarkan jenis masalah, bukan lokasi/waktu, agar variasi
    # lokasi untuk jenis masalah yang sama tidak bocor ke train dan test.
    issue_type = df["scenario"].str.split(";", n=1).str[0].str.strip().str.lower()
    if issue_type.eq("").any():
        stop("Ada scenario yang tidak memiliki jenis masalah.")
    return df["category"].str.strip() + " || " + issue_type


def make_model():
    return LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        random_state=RANDOM_STATE,
    )


def make_vectorizer():
    return TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        ngram_range=(1, 2),
        min_df=2,
        max_features=15000,
        sublinear_tf=True,
    )


def fit_and_evaluate(x_train, y_train, x_eval, y_eval, labels, name):
    vectorizer = make_vectorizer()
    train_matrix = vectorizer.fit_transform(x_train)
    model = make_model()
    model.fit(train_matrix, y_train)
    predictions = model.predict(vectorizer.transform(x_eval))

    metrics = {
        "accuracy": float(accuracy_score(y_eval, predictions)),
        "precision_macro": float(
            precision_score(y_eval, predictions, average="macro", zero_division=0)
        ),
        "recall_macro": float(
            recall_score(y_eval, predictions, average="macro", zero_division=0)
        ),
        "f1_macro": float(
            f1_score(y_eval, predictions, average="macro", zero_division=0)
        ),
        "classification_report": classification_report(
            y_eval, predictions, labels=labels, target_names=labels,
            output_dict=True, zero_division=0,
        ),
    }

    print(f"\n--- {name} ---")
    print(f"Accuracy : {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision_macro']:.4f} (macro)")
    print(f"Recall   : {metrics['recall_macro']:.4f} (macro)")
    print(f"F1-score : {metrics['f1_macro']:.4f} (macro)")
    print(classification_report(
        y_eval, predictions, labels=labels, target_names=labels,
        zero_division=0,
    ))
    return model, vectorizer, metrics, predictions


def random_split_indices(df):
    indices = pd.Series(df.index, index=df.index)
    train_idx, temp_idx = train_test_split(
        indices,
        test_size=0.30,
        random_state=RANDOM_STATE,
        stratify=df["category"],
    )
    val_idx, test_idx = train_test_split(
        temp_idx,
        test_size=0.50,
        random_state=RANDOM_STATE,
        stratify=df.loc[temp_idx, "category"],
    )
    return train_idx.to_numpy(), val_idx.to_numpy(), test_idx.to_numpy()


def grouped_split_indices(df, groups):
    # Tujuh fold menghasilkan kira-kira 71% train, 14% validation, 14% test.
    # Fold validation dan test dipisahkan berdasarkan grup jenis masalah.
    splitter = StratifiedGroupKFold(
        n_splits=7, shuffle=True, random_state=RANDOM_STATE
    )
    folds = list(splitter.split(df, df["category"], groups))
    train_idx = folds[2][1]
    val_idx = folds[0][1]
    test_idx = folds[1][1]

    train_groups = set(groups.iloc[train_idx])
    val_groups = set(groups.iloc[val_idx])
    test_groups = set(groups.iloc[test_idx])

    if train_groups & val_groups:
        stop("Group leakage ditemukan antara training dan validation.")
    if train_groups & test_groups:
        stop("Group leakage ditemukan antara training dan testing.")
    if val_groups & test_groups:
        stop("Group overlap ditemukan antara validation dan testing.")

    return train_idx, val_idx, test_idx


def split_summary(df, train_idx, val_idx, test_idx):
    return {
        "training": int(len(train_idx)),
        "validation": int(len(val_idx)),
        "testing": int(len(test_idx)),
        "category_counts": {
            "training": {
                k: int(v) for k, v in
                df.iloc[train_idx]["category"].value_counts().sort_index().items()
            },
            "validation": {
                k: int(v) for k, v in
                df.iloc[val_idx]["category"].value_counts().sort_index().items()
            },
            "testing": {
                k: int(v) for k, v in
                df.iloc[test_idx]["category"].value_counts().sort_index().items()
            },
        },
    }


def main():
    print("=== AUDIT DAN TRAINING AI LAPORKETUA ===")
    df = load_dataset()
    print(f"[OK] Dataset valid: {len(df)} baris, 9 kategori, 200/kategori.")

    texts = build_text(df)
    y = df["category"]
    groups = build_groups(df)
    labels = sorted(EXPECTED_CATEGORIES)

    print(f"[INFO] Jumlah grup jenis masalah: {groups.nunique()}")
    print("[INFO] Membandingkan random split dengan group-based split.")

    # A. Random split: pembanding dengan eksperimen sebelumnya.
    r_train, r_val, r_test = random_split_indices(df)
    _, _, random_val_metrics, _ = fit_and_evaluate(
        texts.iloc[r_train], y.iloc[r_train],
        texts.iloc[r_val], y.iloc[r_val],
        labels, "RANDOM SPLIT - VALIDATION",
    )
    _, _, random_test_metrics, _ = fit_and_evaluate(
        texts.iloc[r_train], y.iloc[r_train],
        texts.iloc[r_test], y.iloc[r_test],
        labels, "RANDOM SPLIT - TEST",
    )

    # B. Group split: jenis masalah di validation/test tidak dilatih.
    g_train, g_val, g_test = grouped_split_indices(df, groups)
    group_model, group_vectorizer, group_val_metrics, _ = fit_and_evaluate(
        texts.iloc[g_train], y.iloc[g_train],
        texts.iloc[g_val], y.iloc[g_val],
        labels, "GROUP SPLIT - VALIDATION",
    )
    group_model, group_vectorizer, group_test_metrics, group_test_predictions = fit_and_evaluate(
        texts.iloc[g_train], y.iloc[g_train],
        texts.iloc[g_test], y.iloc[g_test],
        labels, "GROUP SPLIT - TEST",
    )

    # Buat confusion matrix untuk hasil group test.
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    matrix = confusion_matrix(
        y.iloc[g_test], group_test_predictions, labels=labels
    )
    fig, ax = plt.subplots(figsize=(13, 10))
    ConfusionMatrixDisplay(
        confusion_matrix=matrix, display_labels=labels
    ).plot(ax=ax, xticks_rotation=45, cmap="Blues", colorbar=False)
    ax.set_title("Confusion Matrix - LaporKetua (Group Test)")
    fig.tight_layout()
    fig.savefig(CONFUSION_MATRIX_PATH, dpi=160, bbox_inches="tight")
    plt.close(fig)

    # Model produksi: setelah evaluasi selesai, latih ulang dengan seluruh
    # dataset sintetis agar model aplikasi memanfaatkan semua data tersedia.
    production_vectorizer = make_vectorizer()
    all_matrix = production_vectorizer.fit_transform(texts)
    production_model = make_model()
    production_model.fit(all_matrix, y)

    bundle = {
        "model": production_model,
        "vectorizer": production_vectorizer,
        "classes": labels,
        "model_version": "laporketua-tfidf-logreg-v2",
        "training_samples": int(len(df)),
        "training_source": "synthetic",
    }
    joblib.dump(bundle, MODEL_PATH)

    report = {
        "dataset_file": str(DATASET_PATH.relative_to(ROOT_DIR)),
        "total_samples": int(len(df)),
        "category_counts": {
            k: int(v) for k, v in df["category"].value_counts().sort_index().items()
        },
        "grouping_method": (
            "category + scenario issue type (text before first semicolon)"
        ),
        "unique_groups": int(groups.nunique()),
        "random_split": {
            "split": split_summary(df, r_train, r_val, r_test),
            "validation_metrics": random_val_metrics,
            "test_metrics": random_test_metrics,
        },
        "group_split": {
            "split": split_summary(df, g_train, g_val, g_test),
            "group_overlap": {
                "train_validation": 0,
                "train_test": 0,
                "validation_test": 0,
            },
            "validation_metrics": group_val_metrics,
            "test_metrics": group_test_metrics,
        },
        "production_model": {
            "file": str(MODEL_PATH.relative_to(ROOT_DIR)),
            "training_samples": int(len(df)),
            "note": (
                "Model produksi dilatih ulang dengan seluruh 1.800 data setelah "
                "evaluasi. Skor evaluasi berasal dari model yang dilatih hanya "
                "pada bagian training di masing-masing split."
            ),
        },
        "caution": (
            "Seluruh data bersifat sintetis. Group split menguji generalisasi "
            "pada jenis masalah scenario yang ditahan dari training, tetapi "
            "belum menggantikan pengujian dengan laporan warga nyata."
        ),
    }
    with REPORT_PATH.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2, default=float)

    print("\n=== SELESAI ===")
    print(f"Model produksi       : {MODEL_PATH}")
    print(f"Laporan audit        : {REPORT_PATH}")
    print(f"Confusion matrix     : {CONFUSION_MATRIX_PATH}")
    print("\nCatatan: gunakan hasil GROUP SPLIT sebagai pemeriksaan yang lebih ketat.")
    print("Tetap uji dengan laporan nyata yang sudah dianonimkan sebelum produksi.")


if __name__ == "__main__":
    main()
