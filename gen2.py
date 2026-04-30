import streamlit as st
import google.generativeai as genai
import yt_dlp
import time
import os
import re

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Grok Masterpiece - Omnipotent", 
    page_icon="👑", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Responsif (Android & Desktop)
st.markdown("""
    <style>
    @media (max-width: 768px) { .main-header { font-size: 1.6rem !important; } [data-testid="column"] { width: 100% !important; } }
    .main-header { font-size: 2.8rem; font-weight: 800; color: #FFD700; text-align: center; margin-bottom: 5px; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; background-color: #FF4B4B; color: white; height: 3em; }
    .api-container { background-color: #1e272e; padding: 20px; border-radius: 15px; border: 1px solid #3d4e5e; margin-bottom: 20px; }
    .result-card { background-color: #1e272e; padding: 20px; border-radius: 15px; border-left: 5px solid #FFD700; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. INISIALISASI SESSION STATE ---
if 'all_prompts' not in st.session_state: st.session_state.all_prompts = [] 
if 'api_key_saved' not in st.session_state: st.session_state.api_key_saved = "" 
if 'api_active' not in st.session_state: st.session_state.api_active = False
if 'auto_dance_name' not in st.session_state: st.session_state.auto_dance_name = ""
if 'dl_path' not in st.session_state: st.session_state.dl_path = None

# --- 3. FUNGSI OMNIPOTENT DOWNLOADER ---
def get_video_info_and_download(url):
    if not os.path.exists('downloads'): os.makedirs('downloads')
    
    # Opsi yt-dlp untuk kualitas terbaik & Metadata
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # Deteksi lagu dari metadata TikTok/YouTube
        track = info.get('track')
        artist = info.get('artist')
        title = info.get('title')
        
        if track and artist:
            detected_name = f"{artist} - {track}"
        elif track:
            detected_name = track
        else:
            # Bersihkan judul dari karakter aneh jika tidak ada track info
            detected_name = re.sub(r'[^\w\s]', '', title).split('\n')[0]
            
        video_path = ydl.prepare_filename(info)
        return video_path, detected_name

# --- 4. API KEY MANAGER ---
st.markdown('<p class="main-header">👑 GROK MOTION ARCHITECT PRO</p>', unsafe_allow_html=True)
col_k1, col_k2, col_k3 = st.columns([1, 2, 1])
with col_k2:
    st.markdown('<div class="api-container">', unsafe_allow_html=True)
    if not st.session_state.api_active:
        new_key = st.text_input("Enter Gemini API Key:", type="password")
        if st.button("💾 Save & Active API"):
            if new_key.startswith("AIza"):
                st.session_state.api_key_saved = new_key; st.session_state.api_active = True; st.rerun()
            else: st.error("Invalid Key! Harus diawali AIza")
    else:
        st.success("✅ API Key Active")
        if st.button("🗑️ Change Key"): st.session_state.api_active = False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 5. SIDEBAR: EPIC CONTROLS ---
with st.sidebar:
    st.markdown("## 🎛️ Studio Settings")
    
    with st.expander("🎶 Context & Energy", expanded=True):
        # Gunakan session state untuk auto-fill
        dance_name_input = st.text_input("Nama Tarian/Lagu:", value=st.session_state.auto_dance_name)
        energy_lvl = st.select_slider("Vibe Kecepatan:", options=["Slow", "Smooth", "Energetic"])

    with st.expander("📸 Sinematografi", expanded=False):
        camera_gear = st.selectbox("Lensa:", ["Sony A7R IV, 35mm f/1.8", "Arri Alexa, 50mm", "iPhone 15 Pro Max"])
        cam_movement = st.selectbox("Gerakan:", ["slow pan right", "gentle dolly forward", "static handheld"])
        shot_type = st.selectbox("Tipe Shot:", ["Full Body Wide Shot", "Medium Shot", "Close-up Focus"])

    with st.expander("🧬 Realisme & Soul", expanded=False):
        realism = st.select_slider("Tekstur:", options=["Standard", "Detailed", "Hyper-Real"])
        mannerisms = st.multiselect("Soul:", ["Natural Blinking", "Fixing hair", "Adjusting outfit"], default=["Natural Blinking"])
        face_expr = st.selectbox("Ekspresi:", ["Warm smile", "Playful wink", "Confident smirk", "Joyful laugh"])

    st.markdown("---")
    bahasa = st.radio("Output Language:", ("English", "Bahasa Indonesia"))

# --- 6. INPUT MODE: LINK VS MANUAL ---
st.markdown("### 🎬 1. Input Reference Video")
tab_link, tab_manual = st.tabs(["🔗 Download via Link (TikTok/YT/IG)", "📁 Upload Manual (Batch)"])

with tab_link:
    input_url = st.text_input("Tempel Link Video Di Sini:", placeholder="https://www.tiktok.com/@user/video/...")
    if st.button("📥 Process Link & Auto-Fill"):
        if input_url and st.session_state.api_active:
            with st.spinner("Mengunduh & Mendeteksi Lagu..."):
                try:
                    path, name = get_video_info_and_download(input_url)
                    st.session_state.dl_path = path
                    st.session_state.auto_dance_name = name
                    st.success(f"Video Siap! Terdeteksi: {name}")
                    st.rerun()
                except Exception as e: st.error(f"Download Error: {e}")
        else: st.warning("Masukkan Link & Pastikan API Key Active!")

    if st.session_state.dl_path:
        st.video(st.session_state.dl_path)
        if st.button("🗑️ Clear Downloaded Video"):
            if os.path.exists(st.session_state.dl_path): os.remove(st.session_state.dl_path)
            st.session_state.dl_path = None; st.session_state.auto_dance_name = ""; st.rerun()

with tab_manual:
    uploaded_files = st.file_uploader("Upload video (banyak sekaligus)", type=["mp4", "mov", "avi"], accept_multiple_files=True)
    if uploaded_files:
        m_cols = st.columns(3)
        for idx, f in enumerate(uploaded_files):
            with m_cols[idx % 3]: st.video(f)

# --- 7. PROSES GENERATE (INTEGRASI TOTAL) ---
st.divider()
if st.button("🔥 GENERATE OFFICIAL GROK PROMPT", disabled=not st.session_state.api_active):
    st.session_state.all_prompts = []
    genai.configure(api_key=st.session_state.api_key_saved)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash")

    # Daftar video untuk diproses (Download + Manual)
    queue = []
    if st.session_state.dl_path: queue.append(('link', st.session_state.dl_path))
    if uploaded_files: 
        for f in uploaded_files: queue.append(('manual', f))

    if not queue:
        st.error("Tidak ada video untuk diproses!")
    else:
        for v_type, v_source in queue:
            v_display_name = os.path.basename(v_source) if v_type == 'link' else v_source.name
            with st.status(f"Analysing: {v_display_name}...") as status:
                try:
                    # Upload ke Gemini
                    if v_type == 'link':
                        video_file = genai.upload_file(path=v_source)
                    else:
                        temp_p = f"temp_{v_display_name}"
                        with open(temp_p, "wb") as f: f.write(v_source.getbuffer())
                        video_file = genai.upload_file(path=temp_p)

                    while video_file.state.name == "PROCESSING": time.sleep(2); video_file = genai.get_file(video_file.name)

                    # Analisa Gemini
                    instruction = f"Analyze dance choreography for '{dance_name_input}'. Extract ONLY skeletal motion 1s intervals for 20s. Separate Part 1 (0-10s) and 2 (10-20s) with '---SEPARATOR---'."
                    response = model.generate_content([video_file, instruction])
                    raw_motion = response.text

                    # FORMAT GROK OFFICIAL
                    p1_text = raw_motion.split('---SEPARATOR---')[0] if '---SEPARATOR---' in raw_motion else raw_motion
                    p2_text = raw_motion.split('---SEPARATOR---')[1] if '---SEPARATOR---' in raw_motion else "fluid sequence"
                    
                    final_p1 = f"A cinematic 10s video. [SUBJEK] Woman in image dancing '{dance_name_input}'. [CAMERA] {cam_movement} {shot_type}. [MOTION] {p1_text} [STYLE] {lighting_setup}, {realism} pores, {face_expr}. [TECHNICAL] 24fps, coherent physics."
                    final_p2 = f"Continue 10s seamlessly. [LANJUTAN] {p2_text}. [MOTION CONTROL] {energy_lvl.lower()} pacing. [CONSISTENCY] Same outfit/background."

                    st.session_state.all_prompts.append({"name": v_display_name, "p1": final_p1, "p2": final_p2, "video": v_source})
                    
                    if v_type == 'manual': os.remove(temp_p)
                    genai.delete_file(video_file.name)
                    status.update(label=f"Analysis Complete: {v_display_name}", state="complete")
                except Exception as e: st.error(f"Error: {e}")

# --- 8. STUDIO DISPLAY ---
if st.session_state.all_prompts:
    st.markdown("### 🚀 2. Final Motion Prompts")
    for item in st.session_state.all_prompts:
        with st.container():
            st.markdown(f'<div class="result-card"><h4>🎥 Result: {item["name"]}</h4></div>', unsafe_allow_html=True)
            col_r1, col_r2 = st.columns([1, 2])
            with col_r1: st.video(item['video'])
            with col_res2:
                t1, t2 = st.tabs(["📌 Prompt 1 (Main)", "📌 Prompt 2 (Extend)"])
                t1.code(item['p1']); t2.code(item['p2'])
