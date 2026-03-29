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

    df["gaji_min"] = pd.to_numeric(df.get("gaji_min"), errors="coerce")
    df["gaji_max"] = pd.to_numeric(df.get("gaji_max"), errors="coerce")
    df["jumlah_formasi"] = pd.to_numeric(df.get("jumlah_formasi"), errors="coerce")
    df["jumlah_ms"] = pd.to_numeric(df.get("jumlah_ms"), errors="coerce")

    df["avg_gaji"] = (df["gaji_min"] + df["gaji_max"]) / 2

    # filter outlier
    df = df[df["avg_gaji"] <= 20000000]

    df["rasio_persaingan"] = df["jumlah_ms"] / df["jumlah_formasi"]
    df["rasio_persaingan"] = df["rasio_persaingan"].replace([np.inf, -np.inf], np.nan)

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

file_map = {
    "SLTA/SMA": "data/slta.csv",
    "Sistem Informasi": "data/sistem_informasi.csv",
    "Teknik Informatika": "data/teknik_informatika.csv",
    "Teknik Elektro": "data/teknik_elektro.csv",
    "Ilmu Komunikasi": "data/ilmu_komunikasi.csv",
    "Akuntansi": "data/akuntansi.csv"
}

df = load_data(file_map[jurusan])

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

max_rasio = st.sidebar.slider("Maks Persaingan", 1, 200, 30)

instansi = st.sidebar.text_input("Filter Instansi (opsional)")

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

# fallback
if filtered.empty:
    st.warning("⚠️ Tidak ada data sesuai filter. Menampilkan rekomendasi umum.")
    filtered = df.copy()
    filtered = filtered[filtered["rasio_persaingan"] < 100]

# =========================
# SCORING
# =========================
filtered["score"] = (
    (filtered["avg_gaji"] / filtered["avg_gaji"].max()) * weight_gaji +
    ((1 / (filtered["rasio_persaingan"] + 1)) * weight_rasio)
)

filtered["score_pct"] = filtered["score"] * 100
result = filtered.sort_values("score", ascending=False)

# =========================
# HELPER
# =========================
def format_gaji(row):
    return f"Rp {row['gaji_min']/1e6:.1f}–{row['gaji_max']/1e6:.1f} jt"

def label_persaingan(x):
    if x < 10:
        return "Sepi 🟢"
    elif x < 30:
        return "Sedang 🟡"
    else:
        return "Ketat 🔴"

# =========================
# 📊 INSIGHT TABLE
# =========================
st.subheader("📊 Insight Formasi")

insight_df = pd.concat([
    df.sort_values("avg_gaji", ascending=False).head(1).assign(Kategori="💰 Gaji Tertinggi"),
    df.sort_values("avg_gaji").head(1).assign(Kategori="💸 Gaji Terendah"),
    df.sort_values("jumlah_ms", ascending=False).head(1).assign(Kategori="🔥 Pendaftar Terbanyak"),
    df.sort_values("jumlah_ms").head(1).assign(Kategori="🧊 Pendaftar Tersedikit")
])

insight_df["Gaji"] = insight_df.apply(format_gaji, axis=1)

insight_df = insight_df[[
    "Kategori", "ins_nm", "jabatan_nm", "provinsi", "Gaji", "jumlah_formasi", "jumlah_ms"
]].rename(columns={
    "ins_nm": "Instansi",
    "jabatan_nm": "Jabatan",
    "provinsi": "Lokasi",
    "jumlah_formasi": "Formasi",
    "jumlah_ms": "Pendaftar"
})

st.dataframe(insight_df, width="stretch")

# =========================
# 🏆 TOP 3 EASIEST
# =========================
st.subheader("🏆 Peluang Terbaik (Saingan Rendah)")

easiest = filtered.sort_values("rasio_persaingan").head(3)
easiest["Gaji"] = easiest.apply(format_gaji, axis=1)

st.dataframe(easiest[[
    "ins_nm", "jabatan_nm", "provinsi", "Gaji", "jumlah_formasi", "jumlah_ms", "rasio_persaingan"
]].rename(columns={
    "ins_nm": "Instansi",
    "jabatan_nm": "Jabatan",
    "provinsi": "Lokasi",
    "jumlah_formasi": "Formasi",
    "jumlah_ms": "Pendaftar",
    "rasio_persaingan": "Rasio"
}), width="stretch")

# =========================
# 💎 HIDDEN GEM
# =========================
st.subheader("💎 Hidden Gem (Gaji Lumayan + Sepi)")

hidden = filtered[
    (filtered["avg_gaji"] > filtered["avg_gaji"].median()) &
    (filtered["rasio_persaingan"] < filtered["rasio_persaingan"].median())
].head(5)

hidden["Gaji"] = hidden.apply(format_gaji, axis=1)

st.dataframe(hidden[[
    "ins_nm", "jabatan_nm", "provinsi", "Gaji", "jumlah_formasi", "jumlah_ms"
]].rename(columns={
    "ins_nm": "Instansi",
    "jabatan_nm": "Jabatan",
    "provinsi": "Lokasi",
    "jumlah_formasi": "Formasi",
    "jumlah_ms": "Pendaftar"
}), width="stretch")

# =========================
# 🏆 REKOMENDASI
# =========================
st.subheader("🏆 Rekomendasi Terbaik")

display_df = result.copy()
display_df["Gaji"] = display_df.apply(format_gaji, axis=1)
display_df["Persaingan"] = display_df["rasio_persaingan"].apply(label_persaingan)
display_df["Skor (%)"] = display_df["score_pct"].apply(lambda x: f"{x:.1f}%")

display_df = display_df[[
    "ins_nm", "jabatan_nm", "provinsi", "Gaji",
    "jumlah_formasi", "jumlah_ms", "Persaingan", "Skor (%)"
]].rename(columns={
    "ins_nm": "Instansi",
    "jabatan_nm": "Jabatan",
    "provinsi": "Lokasi",
    "jumlah_formasi": "Formasi",
    "jumlah_ms": "Pendaftar"
})

top_n = st.slider("Jumlah hasil", 5, 50, 20)
st.dataframe(display_df.head(top_n), width="stretch")

# =========================
# METRICS
# =========================
st.subheader("📊 Insight")

col1, col2, col3 = st.columns(3)

col1.metric("Jumlah Kandidat", len(filtered))
col2.metric("Rata-rata Gaji", f"Rp {int(filtered['avg_gaji'].mean()):,}")
col3.metric("Rata-rata Persaingan", round(filtered["rasio_persaingan"].mean(), 2))

# =========================
# CHART
# =========================
st.subheader("📈 Gaji vs Persaingan")
st.scatter_chart(filtered[["avg_gaji", "rasio_persaingan"]])

# =========================
# DOWNLOAD
# =========================
csv = result.to_csv(index=False).encode("utf-8")
st.download_button("📥 Download Hasil", csv, "cpns_recommendation.csv", "text/csv")

# =========================
# FOOTER
# =========================
st.caption("Built with ❤️ using SSCASN 2024 data by Zekri 🚀")
