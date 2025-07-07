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
    if not isinstance(a, str) or not isinstance(b, str):
        return 0 # Handle non-string values
    if not a or not b:
        return 0
    return (1 - Levenshtein.distance(a.lower(), b.lower()) / max(len(a), len(b))) * 100

# --- Load Data ---
df = pd.read_excel("Data Buku.xlsx", engine='openpyxl')

# Preprocessing: Isi NaN di 'Sinopsis/Deskripsi' dengan string kosong sebelum TF-IDF
# Ini penting agar TF-IDF tidak error dan Levenshtein tidak error
df['Judul'].fillna('', inplace=True)
df['Sinopsis/Deskripsi'].fillna('', inplace=True)

# --- Implementasi Content-Based Filtering (TF-IDF pada Sinopsis) ---

# Inisialisasi TfidfVectorizer
# stop_words='english' bisa digunakan jika teksnya berbahasa inggris dan ingin menghilangkan kata umum
tfidf_vectorizer = TfidfVectorizer()

# Fit dan transform sinopsis untuk mendapatkan matriks TF-IDF
tfidf_matrix = tfidf_vectorizer.fit_transform(df['Sinopsis/Deskripsi'])

# --- Setup UI Streamlit ---
st.set_page_config(page_title="Rekomendasi Buku", layout="wide")
st.title("📚 Sistem Rekomendasi Buku (CBF TF-IDF Sinopsis + Levenshtein Judul)")

# Selectbox untuk memilih buku favorit
judul_pilihan = st.selectbox("📘 Pilih buku favorit Anda:", df['Judul'].unique()) # .unique() untuk menghindari duplikasi di selectbox

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
    df['Skor_Sinopsis_TFIDF'] = cosine_skor * 100 # Konversi ke persentase

    # 2. Skor Kemiripan Judul (menggunakan Levenshtein Distance)
    df['Skor_Judul_Levenshtein'] = df['Judul'].apply(lambda x: hitung_kemiripan_levenshtein(x, data_pilihan['Judul']))

    # 3. Gabungkan Kedua Skor (dengan bobot, Anda bisa menyesuaikan bobot ini)
    # Contoh: Sinopsis (TF-IDF) 70%, Judul (Levenshtein) 30%
    # Anda bisa eksperimen dengan bobot ini (misalnya 0.5, 0.5 atau 0.8, 0.2)
    bobot_sinopsis = 0.7
    bobot_judul = 0.3
    df['Skor_Total'] = (df['Skor_Sinopsis_TFIDF'] * bobot_sinopsis) + \
                       (df['Skor_Judul_Levenshtein'] * bobot_judul)

    # Ambil rekomendasi tertinggi, kecuali buku itu sendiri
    # Pastikan buku yang dipilih tidak muncul di rekomendasi
    df_rekomendasi = df[df['ID'] != data_pilihan['ID']].sort_values(by='Skor_Total', ascending=False).head(3)

    st.subheader("📚 Rekomendasi Buku Serupa:")
    if not df_rekomendasi.empty:
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
    ➡️ (Sinopsis (TF-IDF): {round(row['Skor_Sinopsis_TFIDF'], 2)}% | Judul (Levenshtein): {round(row['Skor_Judul_Levenshtein'], 2)}%)

    **Penulis:** {row['Penulis']}
    **Penerbit:** {row['Penerbit']}
    **Tanggal Terbit:** {row['Tanggal Terbit']}
    **Halaman:** {row['Halaman']}
    **ISBN:** {row['ISBN']}
    """)
                with st.expander("📝 Sinopsis"):
                    st.write(row['Sinopsis/Deskripsi'])
            st.markdown("---")
    else:
        st.info("Tidak ada rekomendasi yang ditemukan untuk buku ini.")
