import streamlit as st
import google.generativeai as genai
import yt_dlp
import time
import os
import re

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="GROK APEX ARCHITECT", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. FUTURISTIC CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&family=Inter:wght@300;400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { background-color: #050505; font-family: 'Inter', sans-serif; }
    .main-header {
        font-family: 'Orbitron', sans-serif;
        font-size: clamp(1.5rem, 5vw, 2.8rem);
        font-weight: 900;
        background: linear-gradient(90deg, #FFD700, #FF4B4B);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 20px;
    }
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .stButton>button {
        width: 100%; border-radius: 12px; font-weight: 700;
        background: linear-gradient(45deg, #FF4B4B, #800000);
        color: white; border: none; height: 3.5em;
    }
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. INISIALISASI SESSION STATE ---
if 'all_prompts' not in st.session_state: st.session_state.all_prompts = [] 
if 'api_key_saved' not in st.session_state: st.session_state.api_key_saved = "" 
if 'api_active' not in st.session_state: st.session_state.api_active = False
if 'auto_dance_name' not in st.session_state: st.session_state.auto_dance_name = ""
# Penyimpanan Video dalam bentuk BYTES agar preview tidak hilang
if 'dl_video_bytes' not in st.session_state: st.session_state.dl_video_bytes = None
if 'dl_file_name' not in st.session_state: st.session_state.dl_file_name = None
if 'manual_videos_data' not in st.session_state: st.session_state.manual_videos_data = []

# --- 4. DOWNLOADER ENGINE (Fixed to return Bytes) ---
def download_engine(url):
    if not os.path.exists('downloads'): os.makedirs('downloads')
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True, 'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_path = ydl.prepare_filename(info)
        raw_name = info.get('track') or info.get('title') or "Unknown_Trend"
        clean_name = re.sub(r'[^\w\s]', '', raw_name).split('\n')[0]
        
        # Baca file menjadi bytes sebelum dihapus atau ditinggal
        with open(video_path, 'rb') as f:
            video_bytes = f.read()
            
        return video_bytes, clean_name, video_path

# --- 5. TOP SECTION: API KEY ---
st.markdown('<p class="main-header">GROK APEX ARCHITECT</p>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    if not st.session_state.api_active:
        key_input = st.text_input("🛡️ SYSTEM ACCESS KEY (GEMINI API)", type="password")
        if st.button("INITIALIZE CORE SYSTEM"):
            if key_input.startswith("AIza"):
                st.session_state.api_key_saved = key_input; st.session_state.api_active = True; st.rerun()
            else: st.error("Invalid API Key!")
    else:
        c1, c2 = st.columns([4, 1])
        c1.success("✅ SYSTEM ONLINE: Access Granted")
        if c2.button("LOGOUT"): 
            st.session_state.api_active = False; st.session_state.api_key_saved = ""; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 6. SIDEBAR: MASTER CONTROLS ---
with st.sidebar:
    st.markdown("<h2 style='color:#FFD700; font-family:Orbitron; font-size:1.1rem;'>MASTER CONTROL</h2>", unsafe_allow_html=True)
    
    with st.expander("🎵 DANCE CONTEXT", expanded=True):
        dance_name = st.text_input("Trend Name:", value=st.session_state.auto_dance_name)
        visual_preset = st.selectbox("Style Preset:", ["Hyper-Realistic", "90s VHS", "Cyberpunk Neon", "Cinematic Film"])
        energy = st.select_slider("Energy:", options=["Gentle", "Smooth", "Explosive"])

    with st.expander("📸 OPTICS & PHYSICS", expanded=True):
        cam_gear = st.selectbox("Camera:", ["Sony A7R IV", "Arri Alexa", "iPhone 15 Pro Max"])
        cam_move = st.selectbox("Movement:", ["slow pan right", "gentle dolly forward", "subtle tracking"])
        shot_type = st.selectbox("Shot Type:", ["Full Body Wide", "Medium Shot", "Close-up"])
        wind = st.select_slider("Wind Power:", options=["Soft Breeze", "Gentle Wind", "Strong"])

    with st.expander("🧬 REALISME & SOUL", expanded=False):
        char_desc = st.text_area("Detail Model:", placeholder="Contoh: Rambut sebahu, baju maroon...", height=80)
        face_expr = st.selectbox("Ekspresi:", ["Warm smile", "Playful wink", "Confident smirk", "Joyful laugh"])
        realism = st.select_slider("Texture:", options=["Standard", "Detailed", "Hyper-Real"])

    bahasa = st.radio("Prompt Language:", ("English", "Bahasa Indonesia"))

# --- 7. SOURCE SECTION ---
st.markdown("### 🎬 1. MOTION SOURCE")
tab_url, tab_file = st.tabs(["🌐 DOWNLOAD LINK", "📤 BATCH UPLOAD"])

with tab_url:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    url_input = st.text_input("Paste TikTok / YouTube URL:", placeholder="https://...")
    if st.button("SYNC & DOWNLOAD MOTION"):
        if url_input and st.session_state.api_active:
            with st.spinner("Downloading & Syncing..."):
                try:
                    v_bytes, v_name, v_path = download_engine(url_input)
                    st.session_state.dl_video_bytes = v_bytes
                    st.session_state.dl_file_name = v_name
                    st.session_state.auto_dance_name = v_name
                    # Simpan path hanya untuk upload ke Gemini nanti
                    st.session_state.last_dl_path = v_path
                    st.rerun()
                except Exception as e: st.error(f"Download Error: {e}")
    
    if st.session_state.dl_video_bytes:
        st.video(st.session_state.dl_video_bytes) # Menampilkan dari BYTES (Pasti Muncul)
        if st.button("🗑️ CLEAR DOWNLOAD"):
            st.session_state.dl_video_bytes = None
            st.session_state.auto_dance_name = ""
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with tab_file:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    up_files = st.file_uploader("Upload MP4 Files", type=["mp4", "mov", "avi"], accept_multiple_files=True)
    if up_files:
        st.session_state.manual_videos_data = up_files
        f_cols = st.columns(3)
        for idx, f in enumerate(up_files): f_cols[idx%3].video(f)
    st.markdown('</div>', unsafe_allow_html=True)

# --- 8. EXECUTION ---
if st.button("🔥 EXECUTE MOTION ANALYSIS"):
    if not st.session_state.api_active: st.error("API Key Required!")
    else:
        st.session_state.all_prompts = []
        genai.configure(api_key=st.session_state.api_key_saved)
        model = genai.GenerativeModel(model_name="gemini-2.5-flash")

        queue = []
        if st.session_state.dl_video_bytes: 
            # Gunakan file sementara dari path terakhir download
            queue.append(('link', st.session_state.last_dl_path, st.session_state.dl_video_bytes, st.session_state.dl_file_name))
        
        if st.session_state.manual_videos_data:
            for f in st.session_state.manual_videos_data:
                queue.append(('manual', f, f.read(), f.name))

        if not queue: st.warning("No video source detected!")
        else:
            for v_type, v_ref, v_content, v_name in queue:
                with st.status(f"Analysing {v_name}...") as status:
                    try:
                        # Upload ke Gemini
                        if v_type == 'link':
                            video_file = genai.upload_file(path=v_ref)
                        else:
                            tmp_p = f"temp_{v_name}"
                            with open(tmp_p, "wb") as f: f.write(v_content)
                            video_file = genai.upload_file(path=tmp_p)

                        while video_file.state.name == "PROCESSING": time.sleep(2); video_file = genai.get_file(video_file.name)
                        
                        res = model.generate_content([video_file, f"Analyze dance choreography for '{dance_name}'. 1s skeletal breakdown. Separate Part 1/2 with '---SEPARATOR---'."])
                        raw_m = res.text

                        p1_m = raw_m.split('---SEPARATOR---')[0].strip() if '---SEPARATOR---' in raw_m else raw_m
                        p2_m = raw_m.split('---SEPARATOR---')[1].strip() if '---SEPARATOR---' in raw_m else "fluid sequence"
                        
                        c_lock = f"Model Details: {char_desc}. " if char_desc else ""
                        
                        prompt1 = f"A cinematic 10s video. [SUBJEK] Woman in image, {c_lock}dance '{dance_name}'. [CAMERA] {cam_move} {shot_type} ({cam_gear}). [MOTION] {p1_m} [STYLE] {visual_preset}, {face_expr}, {wind} effect. [VISUAL LOCK] Strictly maintain image outfit. [TECHNICAL] 24fps, coherent."
                        prompt2 = f"Continue 10s seamlessly. [LANJUTAN] {p2_m}. [CONTROL] {energy.lower()} pacing. [CONSISTENCY] Match image exactly."

                        # Simpan video dalam bentuk bytes agar preview di hasil generate tidak hilang
                        st.session_state.all_prompts.append({
                            "name": v_name, "p1": prompt1, "p2": prompt2, "video_bytes": v_content
                        })
                        
                        if v_type == 'manual': os.remove(tmp_p)
                        status.update(label=f"Done: {v_name}", state="complete")
                    except Exception as e: st.error(f"Error: {e}")

# --- 9. RESULTS ---
if st.session_state.all_prompts:
    st.markdown("### 🚀 2. GENERATED PROMPTS")
    for item in st.session_state.all_prompts:
        st.markdown(f'<div class="glass-card">', unsafe_allow_html=True)
        st.subheader(f"🎥 {item['name']}")
        
        res_col1, res_col2 = st.columns([1, 2])
        with res_col1:
            st.video(item['video_bytes']) # Putar dari BYTES
            
        with res_col2:
            tab1, tab2 = st.tabs(["📌 PROMPT 1 (0-10s)", "📌 PROMPT 2 (10-20s)"])
            tab1.code(item['p1'], language="text")
            tab2.code(item['p2'], language="text")
        st.markdown('</div>', unsafe_allow_html=True)
    
    full_txt = "\n\n".join([f"FILE: {i['name']}\nP1: {i['p1']}\nP2: {i['p2']}" for i in st.session_state.all_prompts])
    st.download_button("💾 DOWNLOAD ALL (.TXT)", data=full_txt, file_name="Apex_Prompts.txt")
