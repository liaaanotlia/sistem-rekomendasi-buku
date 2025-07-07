import streamlit as st
import pandas as pd
from PIL import Image
import Levenshtein
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# --- Fungsi-fungsi Pembantu ---

def cari_gambar_dari_id(id_buku, folder="gambar"):
    for ext in ['jpg', 'jpeg', 'png']:
        path = os.path.join(folder, f"{id_buku}.{ext}")
        if os.path.exists(path):
            return path
    return None

def hitung_kemiripan_levenshtein(a, b):
    # Pastikan input adalah string sebelum diolah
    if not isinstance(a, str) or not isinstance(b, str):
        return 0
    if not a or not b:
        return 0
    return (1 - Levenshtein.distance(a.lower(), b.lower()) / max(len(a), len(b))) * 100

# --- Load Data ---
df = pd.read_excel("Data Buku.xlsx", engine='openpyxl')

# Preprocessing: Isi NaN dengan string kosong sebelum TF-IDF atau Levenshtein
df['Judul'].fillna('', inplace=True)
df['Sinopsis/Deskripsi'].fillna('', inplace=True)
df['Penulis'].fillna('', inplace=True)

# --- Implementasi Content-Based Filtering (TF-IDF pada Sinopsis) ---

tfidf_vectorizer = TfidfVectorizer()
tfidf_matrix = tfidf_vectorizer.fit_transform(df['Sinopsis/Deskripsi'])

# --- Setup UI Streamlit ---
st.set_page_config(page_title="Rekomendasi Buku", layout="wide")
st.title("📚 Sistem Rekomendasi Buku")

# Selectbox untuk memilih buku favorit
judul_pilihan = st.selectbox("📘 Pilih buku favorit Anda:", df['Judul'].unique())

if judul_pilihan:
    # Ambil data buku yang dipilih
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

    # --- Hitung Skor Kemiripan ---

    # 1. Skor Kemiripan Sinopsis (menggunakan Cosine Similarity dari TF-IDF)
    idx_buku_pilihan = df[df['ID'] == data_pilihan['ID']].index[0]
    cosine_skor = cosine_similarity(tfidf_matrix[idx_buku_pilihan:idx_buku_pilihan+1], tfidf_matrix).flatten()
    df['Skor_Sinopsis_TFIDF'] = cosine_skor * 100

    # 2. Skor Kemiripan Judul (menggunakan Levenshtein Distance)
    df['Skor_Judul_Levenshtein'] = df['Judul'].apply(lambda x: hitung_kemiripan_levenshtein(x, data_pilihan['Judul']))

    # 3. Skor Kemiripan Penulis (menggunakan Levenshtein Distance)
    df['Skor_Penulis_Levenshtein'] = df['Penulis'].apply(lambda x: hitung_kemiripan_levenshtein(x, data_pilihan['Penulis']))

    # 4. Gabungkan Ketiga Skor (dengan bobot)
    bobot_sinopsis = 0.6
    bobot_judul = 0.2
    bobot_penulis = 0.2

    df['Skor_Total'] = (df['Skor_Sinopsis_TFIDF'] * bobot_sinopsis) + \
                       (df['Skor_Judul_Levenshtein'] * bobot_judul) + \
                       (df['Skor_Penulis_Levenshtein'] * bobot_penulis)

    # Ambil 5 rekomendasi tertinggi, kecuali buku itu sendiri
    df_rekomendasi = df[df['ID'] != data_pilihan['ID']].sort_values(by='Skor_Total', ascending=False).head(5)

    st.subheader("📚 Rekomendasi Buku Serupa:")
    if not df_rekomendasi.empty:
        # Buat 5 kolom untuk menampilkan 5 rekomendasi secara horizontal
        cols_rekomendasi = st.columns(5) # Membuat 5 kolom dengan lebar yang sama

        for i, (index, row) in enumerate(df_rekomendasi.iterrows()):
            with cols_rekomendasi[i]: # Masukkan konten untuk setiap buku ke kolom yang sesuai
                gambar = cari_gambar_dari_id(row['ID'])
                if gambar:
                    st.image(Image.open(gambar), width=120) # Ukuran gambar bisa disesuaikan
                else:
                    st.warning("Gambar tidak ditemukan.")

                st.markdown(f"""
    **{row['Judul']}**
    💯 Skor: {round(row['Skor_Total'], 2)}%
    """)
                # Kita bisa tambahkan expander untuk detail lebih lanjut di sini
                with st.expander("📝 Detail"):
                    st.markdown(f"""
    **Penulis:** {row['Penulis']}  \n
    **Penerbit:** {row['Penerbit']}  \n
    **Tanggal Terbit:** {row['Tanggal Terbit']}  \n
    **Halaman:** {row['Halaman']}  \n
    **ISBN:** {row['ISBN']}  \n
    ---
    **Skor Detail:** \n
    Sinopsis : {round(row['Skor_Sinopsis_TFIDF'], 2)}%  \n
    Judul : {round(row['Skor_Judul_Levenshtein'], 2)}%  \n
    Penulis : {round(row['Skor_Penulis_Levenshtein'], 2)}%
    """)
                    st.write(row['Sinopsis/Deskripsi'])
    else:
        st.info("Tidak ada rekomendasi yang ditemukan untuk buku ini.")
