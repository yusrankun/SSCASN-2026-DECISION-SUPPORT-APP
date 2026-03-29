import streamlit as st
import pandas as pd
import numpy as np
import os

st.set_page_config(
    page_title="CPNS Recommender",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@media (max-width: 768px) {
    .block-container {
        padding: 1rem;
    }
}
</style>
""", unsafe_allow_html=True)

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
        "Akuntansi",
        "Teknologi Laboratorium Medis",
        "Administrasi Kesehatan"
    ]
)

file_map = {
    "SLTA/SMA": "data/slta.csv",
    "Sistem Informasi": "data/sistem_informasi.csv",
    "Teknik Informatika": "data/teknik_informatika.csv",
    "Teknik Elektro": "data/teknik_elektro.csv",
    "Ilmu Komunikasi": "data/ilmu_komunikasi.csv",
    "Akuntansi": "data/akuntansi.csv",
    "Teknologi Laboratorium Medis": "data/teknologi_laboratorium_medis.csv",
    "Administrasi Kesehatan": "data/administrasi_kesehatan.csv"
}

df = load_data(file_map[jurusan])

# =========================
# HEADER
# =========================
st.title("🎯 Rekomendasi Formasi CPNS")
st.caption(f"Jurusan: {jurusan} | Optimasi peluang lolos + gaji")

# =========================
# SIDEBAR
# =========================
st.sidebar.header("⚙️ Filter & Strategi")

mode = st.sidebar.selectbox(
    "Mode Strategi",
    ["Aman (Jabar/Banten/Jakarta)", "High Salary (>9jt)", "Custom"]
)

options_prov = sorted(df["provinsi"].dropna().unique())

default_prov = ["Jawa Barat"] if "Jawa Barat" in options_prov else options_prov[:1]

provinsi = st.sidebar.multiselect(
    "Lokasi",
    options=options_prov,
    default=default_prov
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
# FILTER
# =========================
filtered = df.copy()

# ✅ GLOBAL FILTER (SELALU JALAN)
filtered = filtered[filtered["provinsi"].isin(provinsi)]

# =========================
# MODE FILTER
# =========================
if "Aman" in mode:
    filtered = filtered[
        (filtered["avg_gaji"].between(6000000, 8000000)) &
        (filtered["rasio_persaingan"] < 30)
    ]

elif "High Salary" in mode:
    filtered = filtered[
        (filtered["avg_gaji"] > 9000000) &
        (filtered["rasio_persaingan"] < 30)
    ]

else:
    filtered = filtered[
        (filtered["avg_gaji"] >= min_gaji) &
        (filtered["rasio_persaingan"] <= max_rasio)
    ]

if instansi:
    filtered = filtered[
        filtered["ins_nm"].str.contains(instansi, case=False, na=False)
    ]

if filtered.empty:
    st.warning("⚠️ Tidak ada data sesuai filter. Menampilkan rekomendasi umum.")
    filtered = df.copy()
    filtered = filtered[filtered["rasio_persaingan"] < 100]

# =========================
# SCORING + CHANCE
# =========================

# Base score (gaji + persaingan)
filtered["score"] = (
    (filtered["avg_gaji"] / filtered["avg_gaji"].max()) * weight_gaji +
    ((1 / (filtered["rasio_persaingan"] + 1)) * weight_rasio)
)

# =========================
# CHANCE (FIXED)
# =========================
filtered["chance"] = np.where(
    filtered["jumlah_ms"] == 0,
    1,  # auto lolos kalau belum ada pelamar
    filtered["jumlah_formasi"] / (filtered["jumlah_ms"] + 1)
)

# Batasi max 100%
filtered["chance"] = filtered["chance"].clip(0, 1)

filtered["chance_pct"] = filtered["chance"] * 100

# =========================
# TAMBAHAN FACTOR
# =========================

# Semakin banyak formasi, semakin bagus
filtered["formasi_score"] = (
    filtered["jumlah_formasi"] / filtered["jumlah_formasi"].max()
)

# Penalti kalau pelamar terlalu banyak
filtered["penalty"] = np.log1p(filtered["jumlah_ms"])

# =========================
# FINAL SCORE
# =========================
filtered["final_score"] = (
    filtered["score"] * 0.5 +
    filtered["chance"] * 0.3 +
    filtered["formasi_score"] * 0.2
)

# Apply penalty
filtered["final_score"] = filtered["final_score"] / (1 + 0.1 * filtered["penalty"])

# =========================
# FINAL OUTPUT
# =========================
filtered["score_pct"] = filtered["final_score"] * 100

result = filtered.sort_values("final_score", ascending=False)

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

def label_score(x):
    if x > 70:
        return f"{x:.1f}% 🟢"
    elif x > 50:
        return f"{x:.1f}% 🟡"
    else:
        return f"{x:.1f}% 🔴"

def label_chance(x):
    if x > 10:
        return f"{x:.2f}% 🟢"
    elif x > 3:
        return f"{x:.2f}% 🟡"
    else:
        return f"{x:.2f}% 🔴"

def to_title_case(text):
    return str(text).title()

# =========================
# 🏆 BEST PICK 
# =========================
top1 = result.iloc[0]

def soft_color(value):
    if value > 70:
        return "#22c55e"   # soft green
    elif value > 50:
        return "#eab308"   # soft yellow
    else:
        return "#ef4444"   # soft red

st.markdown("### 🏆 Best Pick Saat Ini")

st.markdown(f"""
<div style="
    background: linear-gradient(145deg, #0f172a, #111827);
    padding:24px;
    border-radius:14px;
    border:1px solid #1f2937;
    box-shadow: 0 4px 20px rgba(0,0,0,0.25);
">

<div style="display:grid; grid-template-columns: 1fr; gap:20px;">

<div>
<p style="color:#9ca3af; font-size:13px;">Instansi</p>
<p style="font-size:17px;">{top1['ins_nm']}</p>
</div>

<div>
<p style="color:#9ca3af; font-size:13px;">Jabatan</p>
<p style="font-size:17px;">{to_title_case(top1['jabatan_nm'])}</p>
</div>

<div>
<p style="color:#9ca3af; font-size:13px;">Lokasi</p>
<p style="font-size:17px;">{top1['provinsi']}</p>
</div>

<div>
<p style="color:#9ca3af; font-size:13px;">Gaji</p>
<p style="font-size:17px;">
Rp {top1['gaji_min']/1e6:.1f}–{top1['gaji_max']/1e6:.1f} jt
</p>
</div>

<div>
<p style="color:#9ca3af; font-size:13px;">Formasi vs Pelamar</p>
<p style="font-size:17px;">
{int(top1['jumlah_formasi'])} / {int(top1['jumlah_ms'])}
</p>
</div>

<div>
<p style="color:#9ca3af; font-size:13px;">Estimasi</p>
<p style="font-size:17px; font-weight:600; color:{soft_color(top1['chance_pct'])};">
{top1['chance_pct']:.2f}%
</p>
</div>

</div>

<hr style="margin:18px 0; border-color:#1f2937;">

<p style="color:#9ca3af; font-size:13px;">Skor Rekomendasi</p>
<p style="font-size:17px; font-weight:600; color:{soft_color(top1['score_pct'])};">
{top1['score_pct']:.1f}%
</p>

</div>
""", unsafe_allow_html=True)

# =========================
# INSIGHT TABLE
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

st.dataframe(display_df.head(top_n), use_container_width=True)

# =========================
# REKOMENDASI
# =========================
st.subheader("🏆 Rekomendasi Terbaik")

display_df = result.copy()
display_df["jabatan_nm"] = display_df["jabatan_nm"].apply(lambda x: str(x).title())
display_df["Gaji"] = display_df.apply(format_gaji, axis=1)
display_df["Persaingan"] = display_df["rasio_persaingan"].apply(label_persaingan)
display_df["Estimasi (%)"] = display_df["chance_pct"].apply(label_chance)
display_df["Skor (%)"] = display_df["score_pct"].apply(label_score)

display_df = display_df[[
    "ins_nm", "jabatan_nm", "provinsi", "Gaji",
    "jumlah_formasi", "jumlah_ms",
    "Persaingan", "Estimasi (%)", "Skor (%)"
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
