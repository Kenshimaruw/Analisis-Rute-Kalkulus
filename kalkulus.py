import numpy as np
import pandas as pd
import gpxpy

# --- LANGKAH 3: BACA & BERSIHKAN DATA (SMOOTHING) ---
def load_dan_bersihkan_data(filepath, window=15):
    df = pd.read_csv(filepath)
    df["elevasi_halus"] = df["elevasi_meter"].rolling(
        window=window, center=True, min_periods=1
    ).mean()
    return df

def baca_gpx(file_gpx, window=15):
    """Membaca file GPX dari Strava/Garmin menjadi DataFrame (waktu, jarak, elevasi)."""
    gpx = gpxpy.parse(file_gpx)
    
    waktu_list, jarak_list, elevasi_list = [], [], []
    jarak_kumulatif = 0.0
    waktu_awal = None
    titik_sebelumnya = None

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                if point.time is None:
                    continue
                if waktu_awal is None:
                    waktu_awal = point.time
                
                detik = (point.time - waktu_awal).total_seconds()
                
                if titik_sebelumnya is not None:
                    jarak_kumulatif += point.distance_2d(titik_sebelumnya)
                
                waktu_list.append(detik)
                jarak_list.append(jarak_kumulatif)
                elevasi_list.append(point.elevation if point.elevation is not None else 0.0)
                titik_sebelumnya = point

    df = pd.DataFrame({
        "waktu_detik": waktu_list,
        "jarak_meter": jarak_list,
        "elevasi_meter": elevasi_list
    })
    df["elevasi_halus"] = df["elevasi_meter"].rolling(
        window=window, center=True, min_periods=1
    ).mean()
    return df

# --- LANGKAH 4: TURUNAN NUMERIK (METODE BEDA HINGGA) ---
def turunan_manual(y, x):
    """Menghitung dy/dx secara manual menggunakan metode Beda Hingga (Finite Difference)."""
    n = len(x)
    dy_dx = np.zeros(n)
    
    for i in range(n - 1):
        dx = x[i + 1] - x[i]
        dy = y[i + 1] - y[i]
        dy_dx[i] = dy / dx if dx != 0 else 0.0
        
    dy_dx[-1] = dy_dx[-2]
    return dy_dx

# --- LANGKAH 5: INTEGRAL NUMERIK (ATURAN TRAPESIUM) ---
def integral_trapesium_manual(y, x):
    """Menghitung integral tentu dari y terhadap x menggunakan Aturan Trapesium."""
    total_luas = 0.0
    for i in range(len(x) - 1):
        lebar = x[i + 1] - x[i]
        tinggi_rata2 = (y[i] + y[i + 1]) / 2
        total_luas += tinggi_rata2 * lebar
    return total_luas

def hitung_elevation_gain(elevasi):
    """Menghitung total tanjakan (hanya menjumlahkan perubahan elevasi positif)."""
    total_naik = 0.0
    for i in range(len(elevasi) - 1):
        selisih = elevasi[i + 1] - elevasi[i]
        if selisih > 0:
            total_naik += selisih
    return total_naik

# --- FUNGSI UTAMA ANALISIS ---
def analisis_rute(df):
    t = df["waktu_detik"].values
    s = df["jarak_meter"].values
    h = df["elevasi_halus"].values

    v_ms = turunan_manual(s, t)
    df["kecepatan_kmj"] = v_ms * 3.6
    df["gradien_persen"] = turunan_manual(h, s) * 100
    df["percepatan_ms2"] = turunan_manual(v_ms, t)

    jarak_integral_manual = integral_trapesium_manual(v_ms, t)
    jarak_integral_numpy = np.trapezoid(v_ms, t)
    elev_gain = hitung_elevation_gain(h)

    ringkasan = {
        "jarak_asli_km": s[-1] / 1000,
        "jarak_integral_manual_km": jarak_integral_manual / 1000,
        "jarak_integral_numpy_km": jarak_integral_numpy / 1000,
        "kecepatan_rata2_kmj": df["kecepatan_kmj"].mean(),
        "kecepatan_maks_kmj": df["kecepatan_kmj"].max(),
        "tanjakan_tercuram_persen": df["gradien_persen"].max(),
        "turunan_tercuram_persen": df["gradien_persen"].min(),
        "total_elevation_gain_m": elev_gain,
    }
    return df, ringkasan

# --- TES JALANKAN DI TERMINAL ---
if __name__ == "__main__":
    data = load_dan_bersihkan_data("rute_dummy.csv")
    data_hasil, hasil = analisis_rute(data)

    print("=== HASIL ANALISIS KALKULUS RUTE ===")
    print(f"Total Jarak Asli (GPS)        : {hasil['jarak_asli_km']:.4f} km")
    print(f"Total Jarak (Integral Manual) : {hasil['jarak_integral_manual_km']:.4f} km")
    print(f"Total Jarak (Integral NumPy)  : {hasil['jarak_integral_numpy_km']:.4f} km")
    print("-" * 40)
    print(f"Kecepatan Rata-rata           : {hasil['kecepatan_rata2_kmj']:.2f} km/jam")
    print(f"Kecepatan Maksimum            : {hasil['kecepatan_maks_kmj']:.2f} km/jam")
    print(f"Tanjakan Tercuram             : {hasil['tanjakan_tercuram_persen']:.2f} %")
    print(f"Turunan Tercuram              : {hasil['turunan_tercuram_persen']:.2f} %")
    print(f"Total Elevation Gain          : {hasil['total_elevation_gain_m']:.2f} meter")