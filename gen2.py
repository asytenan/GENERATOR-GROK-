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

# --- 2. FUTURISTIC & RESPONSIVE CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&family=Inter:wght@300;400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #050505;
        font-family: 'Inter', sans-serif;
    }

    .main-header {
        font-family: 'Orbitron', sans-serif;
        font-size: clamp(1.5rem, 5vw, 2.8rem);
        font-weight: 900;
        background: linear-gradient(90deg, #FFD700, #FF4B4B);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        letter-spacing: 2px;
        filter: drop-shadow(0px 4px 10px rgba(255, 75, 75, 0.3));
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

    /* Responsive untuk HP */
    @media (max-width: 768px) {
        [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
        }
        .main-header { font-size: 1.8rem !important; }
        .glass-card { padding: 15px; }
    }

    .stButton>button {
        width: 100%;
        border-radius: 12px;
        padding: 10px;
        font-weight: 700;
        background: linear-gradient(45deg, #FF4B4B, #800000);
        color: white;
        border: none;
    }

    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. INISIALISASI SESSION STATE ---
if 'all_prompts' not in st.session_state: st.session_state.all_prompts = [] 
if 'api_key_saved' not in st.session_state: st.session_state.api_key_saved = "" 
if 'api_active' not in st.session_state: st.session_state.api_active = False
if 'auto_dance_name' not in st.session_state: st.session_state.auto_dance_name = ""
if 'dl_path' not in st.session_state: st.session_state.dl_path = None
if 'manual_videos' not in st.session_state: st.session_state.manual_videos = []

# --- 4. DOWNLOADER ENGINE ---
def download_engine(url):
    if not os.path.exists('downloads'): os.makedirs('downloads')
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True, 'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        raw_name = info.get('track') or info.get('title') or "Unknown_Trend"
        clean_name = re.sub(r'[^\w\s]', '', raw_name).split('\n')[0]
        return ydl.prepare_filename(info), clean_name

# --- 5. TOP SECTION: HERO & API ---
st.markdown('<p class="main-header">GROK APEX ARCHITECT</p>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    if not st.session_state.api_active:
        key_input = st.text_input("🛡️ SYSTEM ACCESS KEY (GEMINI API)", type="password")
        if st.button("INITIALIZE CORE SYSTEM"):
            if key_input.startswith("AIza"):
                st.session_state.api_key_saved = key_input; st.session_state.api_active = True; st.rerun()
            else: st.error("ACCESS DENIED: Invalid API Key")
    else:
        c1, c2 = st.columns([4, 1])
        c1.success("✅ SYSTEM ONLINE: Access Granted")
        if c2.button("LOGOUT"): 
            st.session_state.api_active = False; st.session_state.api_key_saved = ""; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 6. SIDEBAR: MASTER CONTROLS ---
with st.sidebar:
    st.markdown("<h2 style='color:#FF4B4B; font-family:Orbitron; font-size:1.2rem;'>MASTER CONTROL</h2>", unsafe_allow_html=True)
    
    with st.expander("🎵 DANCE CONTEXT", expanded=True):
        dance_name = st.text_input("Trend Name:", value=st.session_state.auto_dance_name)
        visual_preset = st.selectbox("Style Preset:", ["Hyper-Realistic", "90s VHS", "Cyberpunk Neon", "Cinematic Film"])
        energy = st.select_slider("Energy:", options=["Gentle", "Smooth", "Explosive"])

    with st.expander("📸 OPTICS & PHYSICS", expanded=True):
        cam_gear = st.selectbox("Camera:", ["Sony A7R IV", "Arri Alexa", "iPhone 15 Pro Max"])
        cam_move = st.selectbox("Movement:", ["slow pan right", "gentle dolly forward", "subtle tracking"])
        shot_type = st.selectbox("Shot Type:", ["Full Body Wide", "Medium Shot", "Close-up"])
        wind = st.select_slider("Wind Power:", options=["Soft Breeze", "Gentle Wind", "Strong"])

    with st.expander("👤 CHARACTER LOCK", expanded=False):
        char_desc = st.text_area("Detail Model:", placeholder="Contoh: Rambut sebahu, baju maroon...", height=80)
        face_expr = st.selectbox("Ekspresi:", ["Warm smile", "Playful wink", "Confident smirk", "Joyful laugh"])
        realism = st.select_slider("Texture:", options=["Standard", "Detailed", "Hyper-Real"])

    bahasa = st.radio("Prompt Language:", ("English", "Bahasa Indonesia"))

# --- 7. SOURCE SECTION ---
st.markdown("### 🎬 1. MOTION SOURCE")
tab_url, tab_file = st.tabs(["🌐 DOWNLOAD LINK", "📤 BATCH UPLOAD"])

with tab_url:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    url_input = st.text_input("Paste URL (TikTok/YouTube):", placeholder="https://...")
    if st.button("SYNC & DOWNLOAD"):
        if url_input and st.session_state.api_active:
            with st.spinner("Processing Motion..."):
                try:
                    path, name = download_engine(url_input)
                    st.session_state.dl_path = path; st.session_state.auto_dance_name = name; st.rerun()
                except Exception as e: st.error(f"Sync Failed: {e}")
        else: st.warning("Check API Key & Link!")
    
    if st.session_state.dl_path:
        st.video(st.session_state.dl_path)
        if st.button("🗑️ CLEAR DOWNLOAD"):
            if os.path.exists(st.session_state.dl_path): os.remove(st.session_state.dl_path)
            st.session_state.dl_path = None; st.session_state.auto_dance_name = ""; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with tab_file:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    up_files = st.file_uploader("Upload MP4 Files", type=["mp4", "mov", "avi"], accept_multiple_files=True)
    if up_files:
        st.session_state.manual_videos = up_files
        f_cols = st.columns(3)
        for idx, f in enumerate(up_files): f_cols[idx%3].video(f)
    st.markdown('</div>', unsafe_allow_html=True)

# --- 8. EXECUTION ---
if st.button("🔥 EXECUTE ANALYSIS"):
    if not st.session_state.api_active: st.error("API Key Required!")
    else:
        st.session_state.all_prompts = []
        genai.configure(api_key=st.session_state.api_key_saved)
        model = genai.GenerativeModel(model_name="gemini-2.5-flash")

        queue = []
        if st.session_state.dl_path: queue.append(('link', st.session_state.dl_path))
        if st.session_state.manual_videos: 
            for f in st.session_state.manual_videos: queue.append(('manual', f))

        if not queue: st.warning("No video source detected!")
        else:
            for v_type, v_source in queue:
                v_name = os.path.basename(v_source) if v_type == 'link' else v_source.name
                with st.status(f"Processing {v_name}...") as status:
                    try:
                        if v_type == 'link': video_file = genai.upload_file(path=v_source)
                        else:
                            tmp = f"temp_{v_name}"
                            with open(tmp, "wb") as f: f.write(v_source.getbuffer())
                            video_file = genai.upload_file(path=tmp)

                        while video_file.state.name == "PROCESSING": time.sleep(2); video_file = genai.get_file(video_file.name)
                        
                        instruction = f"Analyze dance for '{dance_name}'. 1s skeletal breakdown. Split Part 1/2 with '---SEPARATOR---'."
                        res = model.generate_content([video_file, instruction])
                        raw_m = res.text

                        # Builder
                        p1_m = raw_m.split('---SEPARATOR---')[0].strip() if '---SEPARATOR---' in raw_m else raw_m
                        p2_m = raw_m.split('---SEPARATOR---')[1].strip() if '---SEPARATOR---' in raw_m else "fluid sequence"
                        
                        c_lock = f"Model Details: {char_desc}. " if char_desc else ""
                        tex_m = "Visible skin pores, subsurface scattering. " if realism == "Hyper-Real" else "Detailed skin. "
                        
                        prompt1 = f"A cinematic 10s video. [SUBJEK] Woman in image, {c_lock}dance '{dance_name}'. [CAMERA] {cam_move} {shot_type} ({cam_gear}). [MOTION] {p1_m} [STYLE] {visual_preset}, {tex_m}, {face_expr}, {wind} effect. [VISUAL LOCK] Strictly maintain image outfit. [TECHNICAL] 24fps, coherent."
                        prompt2 = f"Continue 10s seamlessly. [LANJUTAN] {p2_m}. [CONTROL] {energy.lower()} pacing. [CONSISTENCY] Match image exactly."

                        st.session_state.all_prompts.append({"name": v_name, "p1": prompt1, "p2": prompt2, "video": v_source, "v_type": v_type})
                        if v_type == 'manual': os.remove(tmp)
                        status.update(label=f"Done: {v_name}", state="complete")
                    except Exception as e: st.error(f"Error: {e}")

# --- 9. RESULTS ---
if st.session_state.all_prompts:
    st.markdown("### 🚀 2. GENERATED PROMPTS")
    for item in st.session_state.all_prompts:
        st.markdown(f'<div class="glass-card">', unsafe_allow_html=True)
        st.subheader(f"🎥 {item['name']}")
        
        # Grid per video result
        res_col1, res_col2 = st.columns([1, 2])
        
        with res_col1:
            # Re-display video preview di hasil
            if item['v_type'] == 'link': st.video(item['video'])
            else: st.video(item['video'])
            
        with res_col2:
            tab1, tab2 = st.tabs(["📌 PROMPT 1 (0-10s)", "📌 PROMPT 2 (10-20s)"])
            tab1.code(item['p1'], language="text")
            tab2.code(item['p2'], language="text")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Global Download
    full_txt = "\n\n".join([f"FILE: {i['name']}\nP1: {i['p1']}\nP2: {i['p2']}" for i in st.session_state.all_prompts])
    st.download_button("💾 DOWNLOAD ALL (.TXT)", data=full_txt, file_name="Apex_Prompts.txt")
