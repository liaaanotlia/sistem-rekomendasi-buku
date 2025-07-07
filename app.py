import streamlit as st
import pandas as pd
from PIL import Image
import Levenshtein
import os

def cari_gambar_dari_id(id_buku, folder="gambar"):
    for ext in ['jpg', 'jpeg', 'png']:
        path = os.path.join(folder, f"{id_buku}.{ext}")
        if os.path.exists(path):
            return path
    return None

def hitung_kemiripan(a, b):
    if not a or not b:
        return 0
    return (1 - Levenshtein.distance(a.lower(), b.lower()) / max(len(a), len(b))) * 100

# Load data
df = pd.read_excel("Data Buku.xlsx", engine='openpyxl')
df.dropna(subset=['Judul', 'Sinopsis/Deskripsi'], inplace=True)

# Setup UI
st.set_page_config(page_title="Rekomendasi Buku", layout="wide")
st.title("📚 Sistem Rekomendasi Buku (Levenshtein Judul + Sinopsis)")

judul_pilihan = st.selectbox("📘 Pilih buku favorit:", df['Judul'])

if judul_pilihan:
    data_pilihan = df[df['Judul'] == judul_pilihan].iloc[0]

    st.subheader("📖 Detail Buku yang Dipilih:")
    col1, col2 = st.columns([1, 3])
    with col1:
        gambar = cari_gambar_dari_id(data_pilihan['ID'])
        if gambar:
            st.image(Image.open(gambar), width=150)
        else:
            st.warning("Gambar tidak ditemukan.")
    with col2:
        st.markdown(f"**Judul:** {data_pilihan['Judul']}  \n"
                    f"**Penulis:** {data_pilihan['Penulis']}  \n"
                    f"**Penerbit:** {data_pilihan['Penerbit']}  \n"
                    f"**Tanggal Terbit:** {data_pilihan['Tanggal Terbit']}  \n"
                    f"**Halaman:** {data_pilihan['Halaman']}  \n"
                    f"**ISBN:** {data_pilihan['ISBN']}")
        with st.expander("📝 Sinopsis"):
            st.write(data_pilihan['Sinopsis/Deskripsi'])

    st.markdown("---")

    # Hitung skor kemiripan
    sinopsis_pilihan = data_pilihan['Sinopsis/Deskripsi']
    judul_pilihan = data_pilihan['Judul']

    df['Skor_Judul'] = df['Judul'].apply(lambda x: hitung_kemiripan(x, judul_pilihan))
    df['Skor_Sinopsis'] = df['Sinopsis/Deskripsi'].apply(lambda x: hitung_kemiripan(x, sinopsis_pilihan))
    df['Skor_Total'] = (df['Skor_Judul'] + df['Skor_Sinopsis']) / 2

    # Ambil rekomendasi tertinggi, kecuali buku itu sendiri
    df_rekomendasi = df[df['ID'] != data_pilihan['ID']].sort_values(by='Skor_Total', ascending=False).head(3)

    st.subheader("📚 Rekomendasi Buku Serupa:")
    for _, row in df_rekomendasi.iterrows():
        col1, col2 = st.columns([1, 3])
        with col1:
            gambar = cari_gambar_dari_id(row['ID'])
            if gambar:
                st.image(Image.open(gambar), width=150)
            else:
                st.warning("Gambar tidak ditemukan.")
        with col2:
            st.markdown(f"""
### {row['Judul']}
💯 **Skor Kesamaan Total:** {round(row['Skor_Total'], 2)}%  
➡️ (Judul: {round(row['Skor_Judul'], 2)}% | Sinopsis: {round(row['Skor_Sinopsis'], 2)}%)

**Penulis:** {row['Penulis']}  
**Penerbit:** {row['Penerbit']}  
**Tanggal Terbit:** {row['Tanggal Terbit']}  
**Halaman:** {row['Halaman']}  
**ISBN:** {row['ISBN']}
""")
            with st.expander("📝 Sinopsis"):
                st.write(row['Sinopsis/Deskripsi'])
        st.markdown("---")
