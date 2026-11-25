import numpy as np
import pandas as pd

# Simulasi aktivitas lari/sepeda selama 30 menit (1800 detik), direkam tiap 1 detik
np.random.seed(42)
waktu = np.arange(0, 1801, 1)  # 0 sampai 1800 detik

# Buat profil kecepatan dasar (meter/detik)
# Bervariasi antara 2.5 m/s (lambat saat menanjak) sampai 4.2 m/s (cepat saat turun/datar)
kecepatan_dasar = 3.2 + 0.6 * np.sin(waktu / 200) - 0.5 * np.sin(waktu / 100)

# Hitung jarak kumulatif (meter) dari kecepatan dasar
jarak = np.cumsum(kecepatan_dasar)
jarak[0] = 0.0

# Buat profil elevasi (meter di atas permukaan laut) berdasarkan jarak
# Mulai dari 100 mdpl, ada tanjakan curam di tengah rute, lalu turun lagi
elevasi_bersih = (
    100
    + 40 * np.sin(jarak / 1200)
    + 25 * np.exp(-((jarak - 2800) ** 2) / (2 * 400**2))
)

# Tambahkan sedikit noise GPS acak (+/- 0.3 meter) agar realistis
noise_gps = np.random.normal(0, 0.3, size=len(waktu))
elevasi_gps = elevasi_bersih + noise_gps

# Simpan ke dalam tabel DataFrame dan ekspor ke CSV
df = pd.DataFrame({
    "waktu_detik": waktu,
    "jarak_meter": np.round(jarak, 2),
    "elevasi_meter": np.round(elevasi_gps, 2)
})

df.to_csv("rute_dummy.csv", index=False)
print("Berhasil! File 'rute_dummy.csv' telah dibuat.")
print(f"Total baris data : {len(df)}")
print(f"Total jarak      : {df['jarak_meter'].iloc[-1] / 1000:.2f} km")
print("\n5 data pertama:")
print(df.head())