import streamlit as st
import pandas as pd
import numpy as np

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="SPK: SAW vs WP (Final Color Fix)", layout="wide")

st.title("Sistem Pendukung Keputusan: Perbandingan SAW & WP")
st.write("Project Akhir: Dimas Ramadhani - 4611422126")

# --- 1. INISIALISASI DATA (SESSION STATE) ---
if 'df_data' not in st.session_state:
    # Data Awal (Default)
    initial_data = {
        'Alternatif': ['A1 (Midtrans)', 'A2 (Xendit)', 'A3 (Doku)', 'A4 (Faspay)', 'A5 (Tripay)'],
        'C1 (Biaya MDR)': [4000, 4500, 3500, 4000, 2500],
        'C2 (Biaya Bulanan)': [0, 0, 250000, 500000, 0],
        'C3 (Jml Channel)': [24, 28, 20, 18, 12],
        'C4 (Kecepatan)': [3, 3, 2, 2, 4],     # 1-4 Skala
        'C5 (Integrasi)': [4, 4, 3, 2, 3]      # 1-4 Skala
    }
    st.session_state.df_data = pd.DataFrame(initial_data)

# --- 2. SIDEBAR (BOBOT) ---
with st.sidebar:
    st.header("Konfigurasi Bobot")
    w1 = st.number_input("Bobot C1 (Biaya MDR)", value=0.25, step=0.05)
    w2 = st.number_input("Bobot C2 (Biaya Bulanan)", value=0.15, step=0.05)
    w3 = st.number_input("Bobot C3 (Jml Channel)", value=0.20, step=0.05)
    w4 = st.number_input("Bobot C4 (Kecepatan)", value=0.20, step=0.05)
    w5 = st.number_input("Bobot C5 (Integrasi)", value=0.20, step=0.05)
    
    weights = {'C1': w1, 'C2': w2, 'C3': w3, 'C4': w4, 'C5': w5}
    
    st.divider()
    if st.button("Reset Data ke Default"):
        del st.session_state['df_data']
        st.rerun()

# --- 3. INPUT DATA & FORM ---
st.header("1. Input Data & CRUD")
st.info("Silakan edit tabel di bawah. Data baru akan diproses setelah Anda menekan tombol 'Simpan & Hitung'.")

with st.form("data_form"):
    edited_df = st.data_editor(
        st.session_state.df_data,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Alternatif": st.column_config.TextColumn("Nama Alternatif", required=True),
            "C1 (Biaya MDR)": st.column_config.NumberColumn("C1: Biaya MDR (Rp)", min_value=0, format="Rp %d", required=True),
            "C2 (Biaya Bulanan)": st.column_config.NumberColumn("C2: Biaya Bulanan (Rp)", min_value=0, format="Rp %d", required=True),
            "C3 (Jml Channel)": st.column_config.NumberColumn("C3: Jml Channel", min_value=0, required=True),
            "C4 (Kecepatan)": st.column_config.NumberColumn("C4: Kecepatan (1-4)", min_value=1, max_value=4, required=True),
            "C5 (Integrasi)": st.column_config.NumberColumn("C5: Integrasi (1-4)", min_value=1, max_value=4, required=True),
        }
    )
    submit = st.form_submit_button("Simpan & Hitung Hasil")

if submit:
    if edited_df.isnull().values.any():
        st.error("Data tidak boleh kosong! Harap lengkapi semua sel.")
    else:
        st.session_state.df_data = edited_df
        st.rerun()

# --- 4. PERSIAPAN DATA HITUNG ---
df_working = st.session_state.df_data.copy()

def get_c1_score(val):
    if val < 3000: return 1.0
    elif 3000 <= val <= 3999: return 0.75
    elif 4000 <= val <= 4499: return 0.5
    else: return 0.25

def get_c2_score(val):
    if val == 0: return 1.0
    elif 1 <= val <= 199999: return 0.75
    elif 200000 <= val <= 499999: return 0.5
    else: return 0.25

def get_c3_score(val):
    if val > 25: return 1.0
    elif 20 <= val <= 25: return 0.75
    elif 15 <= val <= 19: return 0.5
    else: return 0.25

def get_c4_c5_score(val):
    if val == 4: return 1.0
    elif val == 3: return 0.75
    elif val == 2: return 0.5
    else: return 0.25

# --- 5. PROSES HITUNG ---
try:
    # 5.1 Fuzzifikasi
    df_crisp = df_working.copy()
    df_crisp['C1'] = df_working['C1 (Biaya MDR)'].apply(get_c1_score)
    df_crisp['C2'] = df_working['C2 (Biaya Bulanan)'].apply(get_c2_score)
    df_crisp['C3'] = df_working['C3 (Jml Channel)'].apply(get_c3_score)
    df_crisp['C4'] = df_working['C4 (Kecepatan)'].apply(get_c4_c5_score)
    df_crisp['C5'] = df_working['C5 (Integrasi)'].apply(get_c4_c5_score)
    
    matrix_x = df_crisp[['Alternatif', 'C1', 'C2', 'C3', 'C4', 'C5']].copy()

    with st.expander("Lihat Detail Matriks Konversi (Crisp)"):
        st.dataframe(matrix_x, use_container_width=True)

    # 5.2 Perhitungan SAW
    df_saw = matrix_x.copy()
    df_saw['Total_SAW'] = (
        (df_saw['C1'] * weights['C1']) +
        (df_saw['C2'] * weights['C2']) +
        (df_saw['C3'] * weights['C3']) +
        (df_saw['C4'] * weights['C4']) +
        (df_saw['C5'] * weights['C5'])
    )
    df_saw['Rank_SAW'] = df_saw['Total_SAW'].rank(ascending=False).astype(int)

    # 5.3 Perhitungan WP
    df_wp = matrix_x.copy()
    df_wp['Vektor_S'] = (
        (df_wp['C1'] ** weights['C1']) *
        (df_wp['C2'] ** weights['C2']) *
        (df_wp['C3'] ** weights['C3']) *
        (df_wp['C4'] ** weights['C4']) *
        (df_wp['C5'] ** weights['C5'])
    )
    
    total_s = df_wp['Vektor_S'].sum()
    if total_s == 0:
        df_wp['Vektor_V'] = 0
    else:
        df_wp['Vektor_V'] = df_wp['Vektor_S'] / total_s
        
    df_wp['Rank_WP'] = df_wp['Vektor_V'].rank(ascending=False).astype(int)

    # --- 6. TAMPILAN HASIL (COLOR FIX) ---
    st.divider()
    st.header("2. Hasil Perhitungan")
    
    # CSS Style: Background Gold, Tulisan Hitam Tebal
    highlight_style = 'background-color: #FFD700; color: black; font-weight: bold;'
    
    col_res1, col_res2 = st.columns(2)
    
    with col_res1:
        st.subheader("Metode SAW")
        st.dataframe(
            df_saw[['Alternatif', 'Total_SAW', 'Rank_SAW']].sort_values('Rank_SAW')
            .style.highlight_max(subset=['Total_SAW'], axis=0, props=highlight_style),
            use_container_width=True
        )
        
    with col_res2:
        st.subheader("Metode WP")
        st.dataframe(
            df_wp[['Alternatif', 'Vektor_V', 'Rank_WP']].sort_values('Rank_WP')
            .style.highlight_max(subset=['Vektor_V'], axis=0, props=highlight_style),
            use_container_width=True
        )

    # Visualisasi Chart
    st.subheader("Grafik Perbandingan")
    df_chart = pd.merge(df_saw[['Alternatif', 'Total_SAW']], df_wp[['Alternatif', 'Vektor_V']], on='Alternatif')
    df_chart = df_chart.set_index('Alternatif')
    df_chart.columns = ['Nilai SAW', 'Nilai WP']
    
    # Custom warna chart agar lebih estetik
    st.bar_chart(df_chart, color=["#FFD700", "#1f77b4"]) # Gold vs Blue

except Exception as e:
    st.error(f"Terjadi kesalahan perhitungan: {e}")