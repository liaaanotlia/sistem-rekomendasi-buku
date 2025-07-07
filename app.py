if st.button("🔄 Reset Pilihan"):
    st.session_state['judul_terpilih'] = df['Judul'].iloc[0]
    st.rerun()
