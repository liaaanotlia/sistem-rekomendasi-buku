import streamlit as st
import pandas as pd
from PIL import Image
import Levenshtein
import os

# --- Fungsi-fungsi Pembantu ---
def cari_gambar_dari_id(id_buku, folder="gambar"):
    for ext in ['jpg', 'jpeg', 'png']:
        path = os.path.join(folder, f"{id_buku}.{ext}")
        if os.path.exists(path):
            return path
    return None

def hitung_kemiripan_levenshtein(a, b):
    if not isinstance(a, str) or not isinstance(b, str) or not a or not b:
        return 0
    return (1 - Levenshtein.distance(a.lower(), b.lower()) / max(len(a), len(b))) * 100

# --- Load Data ---
df = pd.read_excel("Data Buku.xlsx", engine='openpyxl')
df['Judul'].fillna('', inplace=True)
df['Penulis'].fillna('', inplace=True)
df['Sinopsis/Deskripsi'].fillna('', inplace=True)

# --- Streamlit UI ---
st.set_page_config(page_title="Rekomendasi Buku", layout="wide")
st.title("📚 Sistem Rekomendasi Buku")

if 'selected_book_from_recommendation' not in st.session_state:
    st.session_state.selected_book_from_recommendation = None

initial_selection = st.session_state.selected_book_from_recommendation or df['Judul'].iloc[0]
st.session_state.selected_book_from_recommendation = None

judul_pilihan = st.selectbox(
    "📘 Pilih buku favorit Anda:",
    df['Judul'].unique(),
    index=df['Judul'].unique().tolist().index(initial_selection),
    key='main_selectbox'
)

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
        st.markdown(f"""
        **Judul:** {data_pilihan['Judul']}  
        **Penulis:** {data_pilihan['Penulis']}  
        **Penerbit:** {data_pilihan['Penerbit']}  
        **Tanggal Terbit:** {data_pilihan['Tanggal Terbit']}  
        **Halaman:** {data_pilihan['Halaman']}  
        **ISBN:** {data_pilihan['ISBN']}
        """)
        with st.expander("📝 Sinopsis"):
            st.write(data_pilihan['Sinopsis/Deskripsi'])

    st.markdown("---")

    # --- Hitung Skor Kemiripan (semua pakai Levenshtein) ---
    df['Skor_Sinopsis_Levenshtein'] = df['Sinopsis/Deskripsi'].apply(lambda x: hitung_kemiripan_levenshtein(x, data_pilihan['Sinopsis/Deskripsi']))
    df['Skor_Judul_Levenshtein'] = df['Judul'].apply(lambda x: hitung_kemiripan_levenshtein(x, data_pilihan['Judul']))
    df['Skor_Penulis_Levenshtein'] = df['Penulis'].apply(lambda x: hitung_kemiripan_levenshtein(x, data_pilihan['Penulis']))

    # Bobot Kemiripan
    bobot_sinopsis = 0.6
    bobot_judul = 0.2
    bobot_penulis = 0.2

    df['Skor_Total'] = (df['Skor_Sinopsis_Levenshtein'] * bobot_sinopsis) + \
                       (df['Skor_Judul_Levenshtein'] * bobot_judul) + \
                       (df['Skor_Penulis_Levenshtein'] * bobot_penulis)

    df_rekomendasi = df[df['ID'] != data_pilihan['ID']].sort_values(by='Skor_Total', ascending=False).head(5)

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
                st.button(
                    label=f"**{row['Judul']}**",
                    key=f"rekomendasi_button_{row['ID']}",
                    on_click=lambda judul=row['Judul']: st.session_state.update({'selected_book_from_recommendation': judul})
                )
                st.markdown(f"""
    💯 **Skor Kesamaan Total:** {round(row['Skor_Total'], 2)}%  
    ➡️ (Sinopsis : {round(row['Skor_Sinopsis_Levenshtein'], 2)}% | Judul : {round(row['Skor_Judul_Levenshtein'], 2)}% | Penulis : {round(row['Skor_Penulis_Levenshtein'], 2)}%)

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
        st.info("Tidak ada rekomendasi yang ditemukan.")
