import streamlit as st
import google.generativeai as genai
import yt_dlp
import time
import os
import re

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="GROK APEX ARCHITECT", page_icon="⚡", layout="wide")

# --- 2. FUTURISTIC CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&family=Inter:wght@300;400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { background-color: #050505; font-family: 'Inter', sans-serif; }
    .main-header { font-family: 'Orbitron', sans-serif; font-size: clamp(1.5rem, 5vw, 2.8rem); font-weight: 900; background: linear-gradient(90deg, #FFD700, #FF4B4B); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .glass-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); border-radius: 20px; padding: 20px; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 12px; font-weight: 700; background: linear-gradient(45deg, #FF4B4B, #800000); color: white; border: none; height: 3.5em; }
    </style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'all_prompts' not in st.session_state: st.session_state.all_prompts = [] 
if 'api_key_saved' not in st.session_state: st.session_state.api_key_saved = "" 
if 'api_active' not in st.session_state: st.session_state.api_active = False
if 'auto_dance_name' not in st.session_state: st.session_state.auto_dance_name = ""
if 'video_bytes' not in st.session_state: st.session_state.video_bytes = None

# --- 4. DOWNLOADER ENGINE (POWERED BY FFMEG) ---
def download_engine(url):
    if not os.path.exists('downloads'): os.makedirs('downloads')
    
    # Opsi yt-dlp untuk MEMAKSA konversi ke format yang bisa diputar browser
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        # Menggunakan ffmpeg (dari packages.txt) untuk meremux video agar kompatibel
        'merge_output_format': 'mp4',
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_path = ydl.prepare_filename(info)
        # Jika yt-dlp merubah ekstensi, kita ambil path yang benar
        if not os.path.exists(video_path):
            video_path = video_path.rsplit('.', 1)[0] + '.mp4'
            
        raw_name = info.get('track') or info.get('title') or "Trend"
        clean_name = re.sub(r'[^\w\s]', '', raw_name).split('\n')[0]
        
        with open(video_path, 'rb') as f:
            v_data = f.read()
            
        return v_data, clean_name, video_path

# --- 5. TOP SECTION ---
st.markdown('<p class="main-header">GROK APEX ARCHITECT</p>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    if not st.session_state.api_active:
        key_input = st.text_input("🛡️ SYSTEM ACCESS KEY", type="password")
        if st.button("INITIALIZE CORE SYSTEM"):
            if key_input.startswith("AIza"):
                st.session_state.api_key_saved = key_input; st.session_state.api_active = True; st.rerun()
            else: st.error("Invalid API Key!")
    else:
        c1, c2 = st.columns([4, 1])
        c1.success("✅ SYSTEM ONLINE")
        if c2.button("LOGOUT"): st.session_state.api_active = False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown("## MASTER CONTROL")
    with st.expander("🎵 DANCE CONTEXT", expanded=True):
        dance_name_input = st.text_input("Trend Name:", value=st.session_state.auto_dance_name)
        visual_preset = st.selectbox("Style Preset:", ["Hyper-Realistic", "90s VHS", "Cyberpunk", "Cinematic"])
    with st.expander("📸 OPTICS", expanded=True):
        cam_gear = st.selectbox("Camera:", ["Sony A7R IV", "Arri Alexa", "iPhone 15 Pro"])
        cam_move = st.selectbox("Movement:", ["slow pan right", "gentle dolly forward", "static handheld"])
    bahasa = st.radio("Language:", ("English", "Bahasa Indonesia"))

# --- 7. SOURCE SECTION ---
st.markdown("### 🎬 1. MOTION SOURCE")
tab_url, tab_file = st.tabs(["🌐 DOWNLOAD LINK", "📤 BATCH UPLOAD"])

with tab_url:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    url_input = st.text_input("Paste Link (TikTok/YT):", placeholder="https://...")
    if st.button("SYNC & DOWNLOAD MOTION"):
        if url_input and st.session_state.api_active:
            with st.spinner("Processing with FFmpeg (Please wait)..."):
                try:
                    v_bytes, v_name, v_path = download_engine(url_input)
                    st.session_state.video_bytes = v_bytes
                    st.session_state.auto_dance_name = v_name
                    st.session_state.last_path = v_path
                    st.rerun()
                except Exception as e: st.error(f"Error: {e}")
    
    if st.session_state.video_bytes:
        # Penanganan khusus agar video terputar dengan lancar
        st.video(st.session_state.video_bytes, format="video/mp4")
        if st.button("🗑️ CLEAR"):
            st.session_state.video_bytes = None; st.session_state.auto_dance_name = ""; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with tab_file:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    up_files = st.file_uploader("Upload Files", type=["mp4", "mov", "avi"], accept_multiple_files=True)
    if up_files:
        st.session_state.manual_videos = up_files
        for f in up_files: st.video(f)
    st.markdown('</div>', unsafe_allow_html=True)

# --- 8. EXECUTION ---
if st.button("🔥 EXECUTE ANALYSIS"):
    if not st.session_state.api_active: st.error("API Key Required!")
    else:
        st.session_state.all_prompts = []
        genai.configure(api_key=st.session_state.api_key_saved)
        model = genai.GenerativeModel(model_name="gemini-2.5-flash")
        
        queue = []
        if st.session_state.video_bytes: 
            queue.append(('link', st.session_state.last_path, st.session_state.video_bytes, st.session_state.auto_dance_name))
        if up_files:
            for f in up_files: queue.append(('manual', f, f.read(), f.name))

        for v_type, v_ref, v_content, v_name in queue:
            with st.status(f"Analysing {v_name}...") as status:
                try:
                    if v_type == 'link': video_file = genai.upload_file(path=v_ref)
                    else:
                        tmp_p = f"temp_{v_name}"
                        with open(tmp_p, "wb") as f: f.write(v_content)
                        video_file = genai.upload_file(path=tmp_p)

                    while video_file.state.name == "PROCESSING": time.sleep(2); video_file = genai.get_file(video_file.name)
                    res = model.generate_content([video_file, f"Analyze dance choreography for '{dance_name_input}'. 1s skeletal breakdown. Separate Part 1/2 with '---SEPARATOR---'."])
                    
                    p1_m = res.text.split('---SEPARATOR---')[0].strip() if '---SEPARATOR---' in res.text else res.text
                    p2_m = res.text.split('---SEPARATOR---')[1].strip() if '---SEPARATOR---' in res.text else "fluid continuation"
                    
                    p1 = f"A cinematic 10s video. [SUBJEK] Woman in image dance '{dance_name_input}'. [CAMERA] {cam_move}. [MOTION] {p1_m} [STYLE] {visual_preset}. [VISUAL LOCK] Strictly maintain outfit. [TECHNICAL] 24fps, coherent."
                    p2 = f"Continue 10s seamlessly. [LANJUTAN] {p2_m}. [CONTROL] smooth pacing. [CONSISTENCY] Match image exactly."
                    
                    st.session_state.all_prompts.append({"name": v_name, "p1": p1, "p2": p2, "video": v_content})
                    if v_type == 'manual': os.remove(tmp_p)
                    status.update(label=f"Done: {v_name}", state="complete")
                except Exception as e: st.error(f"Error: {e}")

# --- 9. RESULTS ---
if st.session_state.all_prompts:
    st.markdown("### 🚀 2. GENERATED PROMPTS")
    for item in st.session_state.all_prompts:
        st.markdown(f'<div class="glass-card">', unsafe_allow_html=True)
        st.subheader(f"🎥 {item['name']}")
        c_res1, c_res2 = st.columns([1, 2])
        with c_res1: st.video(item['video'], format="video/mp4")
        with c_res2:
            t1, t2 = st.tabs(["📌 PROMPT 1", "📌 PROMPT 2"])
            t1.code(item['p1'], language="text"); t2.code(item['p2'], language="text")
        st.markdown('</div>', unsafe_allow_html=True)
