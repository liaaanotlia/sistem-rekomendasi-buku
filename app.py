import streamlit as st
import pandas as pd
from PIL import Image
import Levenshtein
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Fungsi cari gambar dari ID
def cari_gambar_dari_id(id_buku, folder="gambar"):
    ekstensi_mungkin = ['jpg', 'jpeg', 'png']
    for ext in ekstensi_mungkin:
        path = os.path.join(folder, f"{id_buku}.{ext}")
        if os.path.exists(path):
            return path
    return None

# === SETUP APLIKASI ===
st.set_page_config(page_title="Sistem Rekomendasi Buku", layout="wide")
st.title("📚 Sistem Rekomendasi Buku")

# Load Excel
try:
    df = pd.read_excel("Data Buku.xlsx", engine='openpyxl')
except Exception as e:
    st.error(f"Gagal membaca file 'Data Buku.xlsx': {e}")
    st.stop()

# Validasi kolom
kolom_wajib = {'ID', 'Judul', 'Penulis', 'Penerbit', 'Tanggal Terbit', 'ISBN', 'Halaman', 'Sinopsis/Deskripsi'}
if not kolom_wajib.issubset(set(df.columns)):
    st.error(f"Kolom Excel tidak lengkap. Harus ada: {', '.join(kolom_wajib)}")
    st.stop()

# Bersihkan data
df = df.dropna(subset=['Judul'])
df.reset_index(drop=True, inplace=True)

# Pilih judul
st.subheader("📘 Pilih Buku Favorit untuk Dicari Rekomendasi:")
judul_pilihan = st.selectbox("Pilih judul buku:", df['Judul'])

if judul_pilihan:
    data_dipilih = df[df['Judul'] == judul_pilihan].iloc[0]

    # ======== DETAIL BUKU DIPILIH ========
    st.subheader("📖 Detail Buku yang Dipilih:")
    col1, col2 = st.columns([1, 3])
    with col1:
        path_gambar = cari_gambar_dari_id(data_dipilih['ID'])
        if path_gambar:
            st.image(Image.open(path_gambar), width=150)
        else:
            st.warning("Gambar tidak ditemukan.")
    with col2:
        st.markdown(f"**Judul:** {data_dipilih['Judul']}  \n"
                    f"**Penulis:** {data_dipilih['Penulis']}  \n"
                    f"**Penerbit:** {data_dipilih['Penerbit']}  \n"
                    f"**Tanggal Terbit:** {data_dipilih['Tanggal Terbit']}  \n"
                    f"**Halaman:** {data_dipilih['Halaman']}  \n"
                    f"**ISBN:** {data_dipilih['ISBN']}")
        with st.expander("📝 Sinopsis"):
            st.write(data_dipilih['Sinopsis/Deskripsi'])

    st.markdown("---")

    # ======== KEMIRIPAN TF-IDF (CBF) ========
    df['konten'] = (
        df['Judul'].fillna('') + ' ' +
        df['Penulis'].fillna('') + ' ' +
        df['Penerbit'].fillna('') + ' ' +
        df['Sinopsis/Deskripsi'].fillna('')
    )

    tfidf = TfidfVectorizer(stop_words='indonesian')
    tfidf_matrix = tfidf.fit_transform(df['konten'])

    idx_pilihan = df[df['Judul'] == judul_pilihan].index[0]
    cosine_sim = cosine_similarity(tfidf_matrix[idx_pilihan], tfidf_matrix).flatten()
    df['Skor_CBF'] = cosine_sim * 100  # persen

    # ======== KEMIRIPAN LEVENSHTEIN JUDUL ========
    df['Skor_Levenshtein'] = df['Judul'].apply(
        lambda x: (1 - Levenshtein.distance(x.lower(), judul_pilihan.lower()) / max(len(x), len(judul_pilihan))) * 100
    )

    # Gabungkan dua skor
    df['Skor_Total'] = (df['Skor_CBF'] + df['Skor_Levenshtein']) / 2
    df_rekomendasi = df[df['Judul'] != judul_pilihan].copy()
    df_rekomendasi = df_rekomendasi.sort_values(by='Skor_Total', ascending=False).head(3)

    # ======== TAMPILKAN REKOMENDASI ========
    st.subheader("📚 Rekomendasi Buku Serupa:")
    for _, row in df_rekomendasi.iterrows():
        col1, col2 = st.columns([1, 3])
        with col1:
            path_gambar = cari_gambar_dari_id(row['ID'])
            if path_gambar:
                st.image(Image.open(path_gambar), width=150)
            else:
                st.warning("Gambar tidak ditemukan.")
        with col2:
            st.markdown(f"### {row['Judul']}")
            st.markdown(f"**Skor Kesamaan Total:** {round(row['Skor_Total'], 2)}%  \n"
                        f"**(CBF:** {round(row['Skor_CBF'], 2)}% | "
                        f"Judul:** {round(row['Skor_Levenshtein'], 2)}%)  \n"
                        f"**Penulis:** {row['Penulis']}  \n"
                        f"**Penerbit:** {row['Penerbit']}  \n"
                        f"**Tanggal Terbit:** {row['Tanggal Terbit']}  \n"
                        f"**Halaman:** {row['Halaman']}  \n"
                        f"**ISBN:** {row['ISBN']}")
            with st.expander("📝 Sinopsis"):
                st.write(row['Sinopsis/Deskripsi'])
        st.markdown("---")
