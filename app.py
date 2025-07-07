import streamlit as st
import pandas as pd
from PIL import Image
import Levenshtein
import os

# Fungsi cari gambar dari ID
def cari_gambar_dari_id(id_buku, folder="gambar"):
    ekstensi_mungkin = ['jpg', 'jpeg', 'png']
    for ext in ekstensi_mungkin:
        path = os.path.join(folder, f"{id_buku}.{ext}")
        if os.path.exists(path):
            return path
    return None

# ===== MULAI APLIKASI =====
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

# Bersihkan baris kosong
df = df.dropna(subset=['Judul'])

# ===== FITUR SEARCH (TYPING) =====
st.subheader("🔍 Cari Buku (Toleran Typo)")

query = st.text_input("Ketik sebagian atau seluruh judul buku:")

if query:
    df['Skor_Search'] = df['Judul'].apply(lambda x: Levenshtein.distance(str(x).lower(), query.lower()))
    df_hasil_search = df.sort_values(by='Skor_Search').head(5)

    st.markdown("#### Hasil Pencarian Mirip:")
    for _, row in df_hasil_search.iterrows():
        if st.button(f"📘 {row['Judul']}"):
            st.session_state['judul_terpilih'] = row['Judul']
            st.rerun()
else:
    st.info("Ketik judul buku untuk mencari yang mirip.")

st.markdown("---")

# ===== SELECTBOX (FALLBACK) =====
judul_default = st.session_state.get("judul_terpilih", df['Judul'].iloc[0])
if judul_default in df['Judul'].values:
    idx_default = df['Judul'].tolist().index(judul_default)
else:
    idx_default = 0  # fallback aman

judul_pilihan = st.selectbox("Atau pilih buku secara manual:", df['Judul'], index=idx_default)

# ===== TAMPILKAN DETAIL & REKOMENDASI =====
if judul_pilihan:
    data_dipilih = df[df['Judul'] == judul_pilihan].iloc[0]

    st.subheader("📘 Detail Buku yang Dipilih:")
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

    # REKOMENDASI
    df_pilihan = df[df['Judul'] != judul_pilihan].copy()
    df_pilihan['Skor'] = df_pilihan['Judul'].apply(
        lambda x: Levenshtein.distance(str(x).lower(), judul_pilihan.lower())
    )
    df_rekomendasi = df_pilihan.sort_values(by='Skor').head(3)

    st.subheader("📖 Rekomendasi Buku Serupa:")
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
            st.markdown(f"**Penulis:** {row['Penulis']}  \n"
                        f"**Penerbit:** {row['Penerbit']}  \n"
                        f"**Tanggal Terbit:** {row['Tanggal Terbit']}  \n"
                        f"**Halaman:** {row['Halaman']}  \n"
                        f"**ISBN:** {row['ISBN']}")
            with st.expander("📝 Sinopsis"):
                st.write(row['Sinopsis/Deskripsi'])
        st.markdown("---")
