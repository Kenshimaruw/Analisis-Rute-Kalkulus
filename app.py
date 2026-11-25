import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from kalkulus import load_dan_bersihkan_data, baca_gpx, analisis_rute

# Konfigurasi halaman web
st.set_page_config(page_title="Analisis Rute Kalkulus", layout="wide")

st.title("🏃‍♂️🚴 Analisis Elevasi & Kecepatan Rute (Turunan & Integral)")
st.markdown(
    "Aplikasi ini menerapkan **Turunan Numerik (Beda Hingga)** untuk menghitung kecepatan & gradien tanjakan, "
    "serta **Integral Numerik (Aturan Trapesium)** untuk menghitung total jarak dan *elevation gain*."
)

# --- SIDEBAR: INPUT DATA & PENGATURAN ---
st.sidebar.header("⚙️ Pengaturan Data")
uploaded_file = st.sidebar.file_uploader("Upload file rute (CSV atau GPX)", type=["csv", "gpx"])
window_smooth = st.sidebar.slider("Tingkat Smoothing GPS (Moving Average)", 1, 50, 15)

if uploaded_file is not None:
    if uploaded_file.name.endswith(".gpx"):
        df_raw = baca_gpx(uploaded_file, window=window_smooth)
        st.sidebar.success(f"Menggunakan file GPX: {uploaded_file.name}")
    else:
        df_raw = pd.read_csv(uploaded_file)
        df_raw["elevasi_halus"] = df_raw["elevasi_meter"].rolling(
            window=window_smooth, center=True, min_periods=1
        ).mean()
        st.sidebar.success(f"Menggunakan file CSV: {uploaded_file.name}")
else:
    df_raw = load_dan_bersihkan_data("rute_dummy.csv", window=window_smooth)
    st.sidebar.info("Menggunakan data bawaan: rute_dummy.csv")

# Jalankan perhitungan kalkulus dari kalkulus.py
df, hasil = analisis_rute(df_raw)

# --- BAGIAN 1: RINGKASAN METRIK (INTEGRAL & TURUNAN) ---
st.subheader("📊 Ringkasan Hasil Perhitungan")
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Jarak (Integral)", f"{hasil['jarak_integral_manual_km']:.2f} km")
col2.metric("Kecepatan Rata-rata", f"{hasil['kecepatan_rata2_kmj']:.2f} km/jam")
col3.metric("Total Elevation Gain", f"{hasil['total_elevation_gain_m']:.1f} m")
col4.metric("Tanjakan Tercuram", f"{hasil['tanjakan_tercuram_persen']:.2f} %")

# Tabel Validasi Akurasi Integral
with st.expander("🔍 Lihat Validasi Akurasi Integral (Manual vs GPS vs NumPy)"):
    error_persen = abs(hasil["jarak_asli_km"] - hasil["jarak_integral_manual_km"]) / hasil["jarak_asli_km"] * 100
    st.write(f"- **Total Jarak Asli (GPS):** `{hasil['jarak_asli_km']:.4f} km`")
    st.write(f"- **Integral Trapesium (Manual):** `{hasil['jarak_integral_manual_km']:.4f} km`")
    st.write(f"- **Integral Trapesium (NumPy):** `{hasil['jarak_integral_numpy_km']:.4f} km`")
    st.write(f"- **Persentase Error:** `{error_persen:.4f} %`")

# --- BAGIAN 2: VISUALISASI 3 GRAFIK ---
st.subheader("📈 Grafik Analisis Kalkulus")

jarak_km = df["jarak_meter"] / 1000
waktu_menit = df["waktu_detik"] / 60

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 10), dpi=100)
plt.subplots_adjust(hspace=0.45)

# Grafik 1: Profil Elevasi
ax1.plot(jarak_km, df["elevasi_meter"], color="lightgray", label="Elevasi GPS Asli (Noise)", linewidth=1)
ax1.plot(jarak_km, df["elevasi_halus"], color="#1f77b4", label="Elevasi Halus (Smoothed)", linewidth=2)
ax1.fill_between(jarak_km, df["elevasi_halus"], df["elevasi_halus"].min(), color="#1f77b4", alpha=0.15)
ax1.set_title("1. Profil Elevasi terhadap Jarak")
ax1.set_xlabel("Jarak (km)")
ax1.set_ylabel("Elevasi (mdpl)")
ax1.legend()
ax1.grid(True, linestyle="--", alpha=0.5)

# Grafik 2: Kecepatan
ax2.plot(waktu_menit, df["kecepatan_kmj"], color="#2ca02c", linewidth=2)
ax2.fill_between(waktu_menit, df["kecepatan_kmj"], 0, color="#2ca02c", alpha=0.15)
ax2.set_title("2. Kecepatan Sesaat v(t) = ds/dt (Luas di bawah kurva = Total Jarak)")
ax2.set_xlabel("Waktu (menit)")
ax2.set_ylabel("Kecepatan (km/jam)")
ax2.grid(True, linestyle="--", alpha=0.5)

# Grafik 3: Kemiringan / Gradien
gradien = df["gradien_persen"]
ax3.plot(jarak_km, gradien, color="black", linewidth=1)
ax3.fill_between(jarak_km, gradien, 0, where=(gradien >= 0), color="#d62728", alpha=0.4, label="Tanjakan (+)")
ax3.fill_between(jarak_km, gradien, 0, where=(gradien < 0), color="#17becf", alpha=0.4, label="Turunan (-)")
ax3.axhline(0, color="black", linewidth=0.8, linestyle="--")
ax3.set_title("3. Gradien Kemiringan Jalan (dh/ds × 100%)")
ax3.set_xlabel("Jarak (km)")
ax3.set_ylabel("Kemiringan (%)")
ax3.legend()
ax3.grid(True, linestyle="--", alpha=0.5)

st.pyplot(fig)

# --- BAGIAN 3: TABEL DATA MENTAH ---
with st.expander("📋 Lihat Tabel Data Hasil Perhitungan (10 baris pertama)"):
    st.dataframe(df[["waktu_detik", "jarak_meter", "elevasi_halus", "kecepatan_kmj", "gradien_persen", "percepatan_ms2"]].head(10))