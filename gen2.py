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
    initial_sidebar_state="expanded"
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
    .stButton>button {
        width: 100%; border-radius: 12px; font-weight: 700;
        background: linear-gradient(45deg, #FF4B4B, #800000);
        color: white; border: none; height: 3.5em;
    }
    .download-btn>div>button {
        background: linear-gradient(45deg, #00C851, #007E33) !important;
    }
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'all_prompts' not in st.session_state: st.session_state.all_prompts = [] 
if 'api_key_saved' not in st.session_state: st.session_state.api_key_saved = "" 
if 'api_active' not in st.session_state: st.session_state.api_active = False
if 'auto_dance_name' not in st.session_state: st.session_state.auto_dance_name = ""
if 'prepared_video' not in st.session_state: st.session_state.prepared_video = None

# --- 4. ENGINE: SYNC MUSIC & PREPARE DOWNLOAD ---
def sync_and_prepare(url):
    if not os.path.exists('downloads'): os.makedirs('downloads')
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_path = ydl.prepare_filename(info)
        
        # Deteksi Lagu/Artis
        track = info.get('track')
        artist = info.get('artist')
        title = info.get('title')
        
        if track and artist: detected_name = f"{artist} - {track}"
        elif track: detected_name = track
        else: detected_name = re.sub(r'[^\w\s]', '', title).split('\n')[0]
        
        with open(video_path, 'rb') as f:
            v_bytes = f.read()
            
        return v_bytes, detected_name, os.path.basename(video_path)

# --- 5. TOP SECTION ---
st.markdown('<p class="main-header">GROK APEX ARCHITECT</p>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    if not st.session_state.api_active:
        key_input = st.text_input("🛡️ SYSTEM ACCESS KEY", type="password")
        if st.button("INITIALIZE CORE SYSTEM"):
            if key_input.startswith("AIza"):
                st.session_state.api_key_saved = key_input; st.session_state.api_active = True; st.rerun()
    else:
        c1, c2 = st.columns([4, 1])
        c1.success("✅ SYSTEM ONLINE")
        if c2.button("LOGOUT"): st.session_state.api_active = False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 6. SIDEBAR: MASTER CONTROLS ---
with st.sidebar:
    st.markdown("<h2 style='color:#FFD700; font-family:Orbitron; font-size:1.1rem;'>MASTER CONTROL</h2>", unsafe_allow_html=True)
    
    with st.expander("🎵 DANCE CONTEXT", expanded=True):
        dance_name_input = st.text_input("Trend Name:", value=st.session_state.auto_dance_name)
        visual_preset = st.selectbox("Style Preset:", ["Hyper-Realistic", "90s VHS", "Cyberpunk", "Cinematic Film"])
        energy = st.select_slider("Energy:", options=["Gentle", "Smooth", "Explosive"])

    with st.expander("📸 OPTICS & PHYSICS", expanded=True):
        cam_gear = st.selectbox("Camera:", ["Sony A7R IV", "Arri Alexa", "iPhone 15 Pro Max"])
        cam_move = st.selectbox("Movement:", ["slow pan right", "gentle dolly forward", "subtle tracking"])
        shot_type = st.selectbox("Shot Type:", ["Full Body Wide", "Medium Shot", "Close-up Focus"])
        wind = st.select_slider("Wind Power:", options=["Soft Breeze", "Gentle Wind", "Strong"])

    with st.expander("🧬 REALISME & SOUL", expanded=False):
        char_desc = st.text_area("Detail Model:", placeholder="Contoh: Rambut sebahu, baju maroon...", height=80)
        face_expr = st.selectbox("Ekspresi:", ["Warm smile", "Playful wink", "Confident smirk", "Joyful laugh"])
        realism = st.select_slider("Texture:", options=["Standard", "Detailed", "Hyper-Real"])

    bahasa = st.radio("Prompt Language:", ("English", "Bahasa Indonesia"))

# --- 7. SOURCE SECTION ---
st.markdown("### 🎬 1. MOTION SOURCE")

# Step 1: Music Sync & Download Tool
with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("#### 🔗 Step 1: Sync Music & Download Video")
    url_input = st.text_input("Paste Link TikTok/YouTube:", placeholder="https://...")
    
    col_sync, col_dl = st.columns([1, 1])
    
    if col_sync.button("🔄 SYNC MUSIC & PREPARE"):
        if url_input:
            with st.spinner("Syncing Metadata..."):
                try:
                    v_bytes, v_name, f_name = sync_and_prepare(url_input)
                    st.session_state.auto_dance_name = v_name
                    st.session_state.prepared_video = {"bytes": v_bytes, "filename": f_name}
                    st.rerun()
                except Exception as e: st.error(f"Sync Failed: {e}")
    
    if st.session_state.prepared_video:
        with col_dl:
            st.markdown('<div class="download-btn">', unsafe_allow_html=True)
            st.download_button(
                label="📥 DOWNLOAD VIDEO TO DEVICE",
                data=st.session_state.prepared_video["bytes"],
                file_name=st.session_state.prepared_video["filename"],
                mime="video/mp4"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        st.info(f"✅ Music Synced: **{st.session_state.auto_dance_name}**. Silakan download video di atas lalu upload di Step 2.")
    st.markdown('</div>', unsafe_allow_html=True)

# Step 2: Upload & Analyze
with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("#### 📤 Step 2: Upload Video for Analysis")
    up_files = st.file_uploader("Upload video yang sudah didownload (Batch)", type=["mp4", "mov", "avi"], accept_multiple_files=True)
    if up_files:
        f_cols = st.columns(3)
        for idx, f in enumerate(up_files): f_cols[idx%3].video(f)
    st.markdown('</div>', unsafe_allow_html=True)

# --- 8. EXECUTION ---
if st.button("🔥 EXECUTE ANALYSIS"):
    if not st.session_state.api_active: st.error("API Key Required!")
    elif not up_files: st.warning("Please upload video in Step 2 first!")
    else:
        st.session_state.all_prompts = []
        genai.configure(api_key=st.session_state.api_key_saved)
        model = genai.GenerativeModel(model_name="gemini-2.5-flash")

        for f in up_files:
            v_name = f.name
            with st.status(f"Analysing {v_name}...") as status:
                try:
                    # File handling
                    v_content = f.read()
                    tmp_p = f"temp_{v_name}"
                    with open(tmp_p, "wb") as temp_f: temp_f.write(v_content)
                    
                    video_file = genai.upload_file(path=tmp_p)
                    while video_file.state.name == "PROCESSING": time.sleep(2); video_file = genai.get_file(video_file.name)
                    
                    res = model.generate_content([video_file, f"Analyze dance for '{dance_name_input}'. 1s skeletal breakdown. Separate Part 1/2 with '---SEPARATOR---'."])
                    raw_m = res.text

                    # Build Logic
                    p1_m = raw_m.split('---SEPARATOR---')[0].strip() if '---SEPARATOR---' in raw_m else raw_m
                    p2_m = raw_m.split('---SEPARATOR---')[1].strip() if '---SEPARATOR---' in raw_m else "fluid sequences"
                    
                    p1 = f"A cinematic 10s video. [SUBJEK] Woman in image dance '{dance_name_input}'. [CAMERA] {cam_move} {shot_type}. [MOTION] {p1_m} [STYLE] {visual_preset}. [VISUAL LOCK] Strictly maintain outfit. [TECHNICAL] 24fps, coherent."
                    p2 = f"Continue 10s seamlessly. [LANJUTAN] {p2_m}. [CONTROL] smooth pacing. [CONSISTENCY] Match image exactly."

                    st.session_state.all_prompts.append({"name": v_name, "p1": p1, "p2": p2, "video": v_content})
                    os.remove(tmp_p)
                    status.update(label=f"Done: {v_name}", state="complete")
                except Exception as e: st.error(f"Error: {e}")

# --- 9. RESULTS ---
if st.session_state.all_prompts:
    st.markdown("### 🚀 2. GENERATED PROMPTS")
    for item in st.session_state.all_prompts:
        st.markdown(f'<div class="glass-card">', unsafe_allow_html=True)
        st.subheader(f"🎥 {item['name']}")
        c_r1, c_r2 = st.columns([1, 2])
        with c_r1: st.video(item['video'])
        with c_r2:
            tab1, tab2 = st.tabs(["📌 PROMPT 1", "📌 PROMPT 2"])
            tab1.code(item['p1'], language="text"); tab2.code(item['p2'], language="text")
        st.markdown('</div>', unsafe_allow_html=True)
