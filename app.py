import streamlit as st
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="CPNS Recommender", layout="wide")

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path):
        st.error(f"File tidak ditemukan: {file_path}")
        st.stop()

    df = pd.read_csv(file_path)

    # numeric conversion
    df["gaji_min"] = pd.to_numeric(df.get("gaji_min"), errors="coerce")
    df["gaji_max"] = pd.to_numeric(df.get("gaji_max"), errors="coerce")
    df["jumlah_formasi"] = pd.to_numeric(df.get("jumlah_formasi"), errors="coerce")
    df["jumlah_ms"] = pd.to_numeric(df.get("jumlah_ms"), errors="coerce")

    # feature engineering
    df["avg_gaji"] = (df["gaji_min"] + df["gaji_max"]) / 2

    # 🔥 CLEAN OUTLIER GAJI
    df = df[df["avg_gaji"] <= 20000000]

    df["rasio_persaingan"] = df["jumlah_ms"] / df["jumlah_formasi"]
    df["rasio_persaingan"] = df["rasio_persaingan"].replace([np.inf, -np.inf], np.nan)

    # extract provinsi
    def extract_provinsi(x):
        x = str(x).upper()
        if "JAWA BARAT" in x:
            return "Jawa Barat"
        elif "DKI JAKARTA" in x:
            return "DKI Jakarta"
        elif "BANTEN" in x:
            return "Banten"
        else:
            return "Lainnya"

    df["provinsi"] = df["lokasi_nm"].apply(extract_provinsi)

    return df.dropna(subset=["avg_gaji", "rasio_persaingan"])


# =========================
# SELECT DATA
# =========================
st.sidebar.title("📚 Pilih Jurusan")

jurusan = st.sidebar.selectbox(
    "Jurusan",
    [
        "SLTA/SMA",
        "Sistem Informasi",
        "Teknik Informatika",
        "Teknik Elektro",
        "Ilmu Komunikasi",
        "Akuntansi"
    ]
)

if jurusan == "SLTA/SMA":
    df = load_data("data/slta.csv")

elif jurusan == "Sistem Informasi":
    df = load_data("data/sistem_informasi.csv")

elif jurusan == "Teknik Informatika":
    df = load_data("data/teknik_informatika.csv")

elif jurusan == "Teknik Elektro":
    df = load_data("data/teknik_elektro.csv")

elif jurusan == "Ilmu Komunikasi":
    df = load_data("data/ilmu_komunikasi.csv")

else:
    df = load_data("data/akuntansi.csv")


# =========================
# HEADER
# =========================
st.title("🎯 Rekomendasi Formasi CPNS")
st.caption(f"Jurusan: {jurusan} | Optimasi peluang lolos + gaji")

# =========================
# SIDEBAR FILTER
# =========================
st.sidebar.header("⚙️ Filter & Strategi")

mode = st.sidebar.selectbox(
    "Mode Strategi",
    ["Aman (Jabar/Banten)", "High Salary (>9jt)", "Custom"]
)

provinsi = st.sidebar.multiselect(
    "Lokasi",
    options=sorted(df["provinsi"].unique()),
    default=["Jawa Barat"]
)

min_gaji = st.sidebar.slider(
    "Minimum Gaji",
    int(df["avg_gaji"].min()),
    int(df["avg_gaji"].max()),
    int(df["avg_gaji"].median())
)

max_rasio = st.sidebar.slider(
    "Maks Persaingan",
    1, 200, 30
)

instansi = st.sidebar.text_input("Filter Instansi (opsional)")

# 🎯 Preferensi
st.sidebar.subheader("⚖️ Preferensi")
weight_gaji = st.sidebar.slider("Prioritas Gaji", 0.0, 1.0, 0.5)
weight_rasio = 1 - weight_gaji

# =========================
# FILTERING
# =========================
filtered = df.copy()

if mode == "Aman (Jabar/Banten)":
    filtered = filtered[
        (filtered["provinsi"].isin(["Jawa Barat", "Banten"])) &
        (filtered["avg_gaji"].between(6000000, 8000000)) &
        (filtered["rasio_persaingan"] < 30)
    ]

elif mode == "High Salary (>9jt)":
    filtered = filtered[
        (filtered["avg_gaji"] > 9000000) &
        (filtered["rasio_persaingan"] < 30)
    ]

else:
    filtered = filtered[
        (filtered["provinsi"].isin(provinsi)) &
        (filtered["avg_gaji"] >= min_gaji) &
        (filtered["rasio_persaingan"] <= max_rasio)
    ]

if instansi:
    filtered = filtered[
        filtered["ins_nm"].str.contains(instansi, case=False, na=False)
    ]

# =========================
# HANDLE EMPTY (SMART)
# =========================
if filtered.empty:
    st.warning("⚠️ Tidak ada data yang sesuai filter. Menampilkan rekomendasi umum.")

    filtered = df.copy()
    filtered = filtered[filtered["rasio_persaingan"] < 100]

    st.info("💡 Tips: Kurangi filter atau turunkan minimum gaji untuk hasil lebih banyak.")

# =========================
# SCORING
# =========================
filtered["score"] = (
    (filtered["avg_gaji"] / filtered["avg_gaji"].max()) * weight_gaji +
    ((1 / (filtered["rasio_persaingan"] + 1)) * weight_rasio)
)

# 🔥 UBAH KE PERSENTASE
filtered["score_pct"] = filtered["score"] * 100

result = filtered.sort_values("score", ascending=False)

# =========================
# DISPLAY
# =========================
display_df = result[[
    "ins_nm",
    "jabatan_nm",
    "provinsi",
    "avg_gaji",
    "rasio_persaingan",
    "score_pct"
]].rename(columns={
    "ins_nm": "Instansi",
    "jabatan_nm": "Jabatan",
    "provinsi": "Lokasi",
    "avg_gaji": "Rata-rata Gaji",
    "rasio_persaingan": "Tingkat Persaingan",
    "score_pct": "Skor Rekomendasi (%)"
})

# format gaji
display_df["Rata-rata Gaji"] = display_df["Rata-rata Gaji"].apply(
    lambda x: f"Rp {x:,.0f}"
)

# label persaingan
def label_persaingan(x):
    if x < 10:
        return "Sepi 🟢"
    elif x < 30:
        return "Sedang 🟡"
    else:
        return "Ketat 🔴"

display_df["Tingkat Persaingan"] = display_df["Tingkat Persaingan"].apply(label_persaingan)

# format persen
display_df["Skor Rekomendasi (%)"] = display_df["Skor Rekomendasi (%)"].apply(
    lambda x: f"{x:.1f}%"
)

# =========================
# OUTPUT
# =========================
st.subheader("🏆 Rekomendasi Terbaik")

top_n = st.slider("Jumlah hasil", 5, 50, 20)

st.dataframe(display_df.head(top_n), width="stretch")

# =========================
# METRICS (SAFE)
# =========================
st.subheader("📊 Insight")

col1, col2, col3 = st.columns(3)

avg_gaji = filtered["avg_gaji"].mean()
if pd.isna(avg_gaji):
    avg_gaji = 0

avg_rasio = filtered["rasio_persaingan"].mean()
if pd.isna(avg_rasio):
    avg_rasio = 0

col1.metric("Jumlah Kandidat", len(filtered))
col2.metric("Rata-rata Gaji", f"Rp {int(avg_gaji):,}")
col3.metric("Rata-rata Persaingan", round(avg_rasio, 2))

# =========================
# CHART
# =========================
st.subheader("📈 Gaji vs Persaingan")

st.scatter_chart(filtered[["avg_gaji", "rasio_persaingan"]])

# =========================
# DOWNLOAD
# =========================
csv = result.to_csv(index=False).encode("utf-8")

st.download_button(
    "📥 Download Hasil",
    csv,
    "cpns_recommendation.csv",
    "text/csv"
)

# =========================
# FOOTER
# =========================
st.caption("Built with ❤️ using SSCASN 2024 data by Zekri 🚀")
