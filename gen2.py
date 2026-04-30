import streamlit as st
import google.generativeai as genai
import yt_dlp
import time
import os
import re
import base64

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="GROK APEX ARCHITECT", page_icon="⚡", layout="wide")

# --- 2. CSS CUSTOM ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&family=Inter:wght@300;400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { background-color: #050505; font-family: 'Inter', sans-serif; }
    .main-header { font-family: 'Orbitron', sans-serif; font-size: 2.2rem; font-weight: 900; background: linear-gradient(90deg, #FFD700, #FF4B4B); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .glass-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); border-radius: 20px; padding: 20px; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 12px; font-weight: 700; background: linear-gradient(45deg, #FF4B4B, #800000); color: white; border: none; height: 3.5em; }
    </style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'all_prompts' not in st.session_state: st.session_state.all_prompts = [] 
if 'api_key_saved' not in st.session_state: st.session_state.api_key_saved = "" 
if 'api_active' not in st.session_state: st.session_state.api_active = False
if 'auto_dance_name' not in st.session_state: st.session_state.auto_dance_name = ""
if 'prepared_video' not in st.session_state: st.session_state.prepared_video = None

# --- 4. ENGINE: ULTRA-TRANSCODE (MENGUBAH TOTAL MENJADI FORMAT WEB) ---
def sync_and_transcode_ultra(url):
    if not os.path.exists('downloads'): os.makedirs('downloads')
    
    # Opsi paling agresif untuk memaksa video menjadi H.264 Baseline (Format Web Paling Dasar)
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': 'downloads/video_fixed.%(ext)s',
        'merge_output_format': 'mp4',
        'quiet': True,
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'postprocessor_args': [
            '-c:v', 'libx264',        # Codec paling kompatibel
            '-profile:v', 'baseline', # Profil dasar (Pasti jalan di HP manapun)
            '-level', '3.0',
            '-pix_fmt', 'yuv420p',    # Format warna standar web
            '-movflags', '+faststart',# Agar video bisa langsung diputar saat loading
            '-c:a', 'aac',            # Audio standar
            '-b:a', '128k'
        ],
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_path = ydl.prepare_filename(info)
        
        # Pastikan kita mengambil file MP4
        if not video_path.endswith('.mp4'):
            video_path = video_path.rsplit('.', 1)[0] + '.mp4'
        
        detected_name = info.get('track') or info.get('title') or "Trend"
        detected_name = re.sub(r'[^\w\s]', '', detected_name).split('\n')[0]
        
        with open(video_path, 'rb') as f:
            v_bytes = f.read()
            
        return v_bytes, detected_name, "motion_video_web.mp4"

# --- 5. TOP SECTION ---
st.markdown('<p class="main-header">GROK APEX ARCHITECT PRO</p>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    if not st.session_state.api_active:
        key_input = st.text_input("🛡️ ENTER SYSTEM ACCESS KEY", type="password")
        if st.button("INITIALIZE CORE SYSTEM"):
            if key_input.startswith("AIza"):
                st.session_state.api_key_saved = key_input; st.session_state.api_active = True; st.rerun()
    else:
        c1, c2 = st.columns([4, 1])
        c1.success("✅ SYSTEM ONLINE")
        if c2.button("LOGOUT"): st.session_state.api_active = False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown("## MASTER CONTROL")
    dance_name_input = st.text_input("🎵 Trend Name:", value=st.session_state.auto_dance_name)
    visual_preset = st.selectbox("✨ Style:", ["Hyper-Realistic", "Cinematic", "TikTok Style"])
    cam_move = st.selectbox("📸 Camera:", ["Static", "Slow Zoom", "Handheld Shake"])
    bahasa = st.radio("🌐 Language:", ("English", "Bahasa Indonesia"))

# --- 7. SOURCE SECTION ---
st.markdown("### 🎬 1. MOTION SOURCE")

# Step 1: Sync & Transcode
with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("#### 🔗 Step 1: Sync Music & Fix Codec (Ultra Mode)")
    url_input = st.text_input("Paste Link TikTok/YouTube:", placeholder="https://...")
    
    if st.button("🔄 SYNC & FIX VIDEO CODEC"):
        if url_input:
            with st.spinner("Processing Video with FFmpeg Ultra-Compatibility..."):
                try:
                    v_bytes, v_name, f_name = sync_and_transcode_ultra(url_input)
                    st.session_state.auto_dance_name = v_name
                    st.session_state.prepared_video = {"bytes": v_bytes, "filename": f_name}
                    st.rerun()
                except Exception as e: st.error(f"Sync Failed: {e}")

    if st.session_state.prepared_video:
        st.download_button(
            label="📥 DOWNLOAD WEB-READY VIDEO", 
            data=st.session_state.prepared_video["bytes"], 
            file_name=st.session_state.prepared_video["filename"], 
            mime="video/mp4"
        )
        st.info(f"Musik: {st.session_state.auto_dance_name}. Video sudah dikonversi ke standar web. Download lalu upload di Step 2.")
    st.markdown('</div>', unsafe_allow_html=True)

# Step 2: Upload & Analysis
with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("#### 📤 Step 2: Upload Video for Analysis")
    up_files = st.file_uploader("Upload video yang sudah didownload tadi (Batch)", type=["mp4", "mov"], accept_multiple_files=True)
    if up_files:
        cols = st.columns(min(len(up_files), 3))
        for idx, f in enumerate(up_files):
            with cols[idx % 3]:
                # Memaksa player membungkus data dengan tipe yang benar
                st.video(f, format="video/mp4")
                st.caption(f"📄 {f.name}")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 8. EXECUTION ---
if st.button("🔥 EXECUTE ANALYSIS"):
    if not st.session_state.api_active: st.error("API Key Required!")
    elif not up_files: st.warning("Upload video in Step 2 first!")
    else:
        st.session_state.all_prompts = []
        genai.configure(api_key=st.session_state.api_key_saved)
        model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")

        for f in up_files:
            v_name = f.name
            with st.status(f"Analysing {v_name}...") as status:
                try:
                    f_bytes = f.read()
                    temp_p = f"temp_{v_name}"
                    with open(temp_p, "wb") as temp_f: temp_f.write(f_bytes)
                    video_file = genai.upload_file(path=temp_p)
                    while video_file.state.name == "PROCESSING": time.sleep(2); video_file = genai.get_file(video_file.name)
                    res = model.generate_content([video_file, f"Analyze dance for '{dance_name_input}'. 1s skeletal breakdown. Separate Part 1/2 with '---SEPARATOR---'."])
                    
                    p1_m = res.text.split('---SEPARATOR---')[0].strip() if '---SEPARATOR---' in res.text else res.text
                    p2_m = res.text.split('---SEPARATOR---')[1].strip() if '---SEPARATOR---' in res.text else "fluid continuation"
                    
                    p1 = f"A cinematic 10s video. [SUBJEK] Woman in image dance '{dance_name_input}'. [CAMERA] {cam_move}. [MOTION] {p1_m} [STYLE] {visual_preset}. [VISUAL LOCK] Strictly maintain outfit. [TECHNICAL] 24fps, coherent."
                    p2 = f"Continue 10s seamlessly. [LANJUTAN] {p2_m}. [CONSISTENCY] Match image exactly."

                    st.session_state.all_prompts.append({"name": f.name, "p1": p1, "p2": p2, "video": f_bytes})
                    os.remove(temp_p)
                    status.update(label=f"Done: {v_name}", state="complete")
                except Exception as e: st.error(f"Error: {e}")

# --- 9. RESULTS ---
if st.session_state.all_prompts:
    st.markdown("### 🚀 2. FINAL PROMPTS")
    for item in st.session_state.all_prompts:
        st.markdown(f'<div class="glass-card">', unsafe_allow_html=True)
        st.subheader(f"🎥 {item['name']}")
        c_r1, c_r2 = st.columns([1, 2])
        with c_r1: st.video(item['video'], format="video/mp4")
        with c_r2:
            tab1, tab2 = st.tabs(["📌 P1", "📌 P2"])
            tab1.code(item['p1'], language="text"); tab2.code(item['p2'], language="text")
        st.markdown('</div>', unsafe_allow_html=True)
