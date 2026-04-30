import streamlit as st
import google.generativeai as genai
import time
import os

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Grok Masterpiece Architect Pro", 
    page_icon="👑", 
    layout="wide",
    initial_sidebar_state="collapsed" # Diubah ke collapsed agar layar HP lebih luas saat awal buka
)

# Custom CSS untuk Responsive Android
st.markdown("""
    <style>
    /* Gaya Desktop (Default) */
    .main-header { font-size: 2.8rem; font-weight: 800; color: #FFD700; text-align: center; margin-bottom: 5px; }
    .sub-header { font-size: 1.1rem; text-align: center; color: #bdc3c7; margin-bottom: 25px; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; background-color: #FF4B4B; color: white; border: none; height: 3em; }
    .api-container { background-color: #1e272e; padding: 20px; border-radius: 15px; border: 1px solid #3d4e5e; margin-bottom: 20px; }
    .result-card { background-color: #1e272e; padding: 20px; border-radius: 15px; border-left: 5px solid #FFD700; margin-bottom: 20px; }

    /* Penyesuaian khusus untuk Android / Mobile (Layar di bawah 768px) */
    @media (max-width: 768px) {
        .main-header { font-size: 1.6rem !important; } /* Font judul lebih kecil agar tidak pecah */
        .sub-header { font-size: 0.8rem !important; }
        .api-container { padding: 15px !important; }
        
        /* Memaksa kolom yang tadinya bersampingan menjadi tumpuk ke bawah */
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }
        
        /* Mengurangi padding agar layar kecil tidak terasa sesak */
        .stVideo {
            width: 100% !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. INISIALISASI SESSION STATE ---
if 'all_prompts' not in st.session_state:
    st.session_state.all_prompts = [] 
if 'api_key_saved' not in st.session_state:
    st.session_state.api_key_saved = "" 
if 'api_active' not in st.session_state:
    st.session_state.api_active = False

# --- 3. HEADER ---
st.markdown('<p class="main-header">👑 DAIGO SUKA APLIKASI INI</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Produksi Prompt Grok AI</p>', unsafe_allow_html=True)

# --- 4. API KEY MANAGER (SAVE & DELETE) ---
with st.container():
    col_k1, col_k2, col_k3 = st.columns([1, 4, 1]) # Diperlebar kolom tengahnya untuk mobile
    with col_k2:
        st.markdown('<div class="api-container">', unsafe_allow_html=True)
        st.markdown("### 🔑 MASUKKAN API KEY KAMU")
        
        if not st.session_state.api_active:
            new_key = st.text_input("Enter Gemini API Key:", type="password", placeholder="Paste your API Key here...")
            if st.button("💾 Save API Key"):
                if new_key:
                    st.session_state.api_key_saved = new_key
                    st.session_state.api_active = True
                    st.rerun()
                else:
                    st.error("Please enter a key first!")
        else:
            st.success("✅ API Key is Active and Saved")
            if st.button("🗑️ Delete & Change API Key"):
                st.session_state.api_key_saved = ""
                st.session_state.api_active = False
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.api_active:
    genai.configure(api_key=st.session_state.api_key_saved)

st.divider()

# --- 5. CONTROL PANEL (SIDEBAR) ---
with st.sidebar:
    st.markdown("## 🎛️ Control Panel")
    
    with st.expander("📸 Sinematografi", expanded=True):
        camera_gear = st.selectbox("Lensa Kamera:", ["Sony A7R IV, 35mm f/1.8", "Arri Alexa, 50mm Cinematic", "iPhone 15 Pro Max (TikTok)"])
        cam_movement = st.selectbox("Gerakan Kamera:", ["Static", "Slow Zoom In", "Handheld TikTok Shake", "Dynamic Tracking", "Speed Ramp"])
        shot_type = st.selectbox("Tipe Shot:", ["Full Body Wide", "Medium Shot", "Close-up Focus"])

    with st.expander("🧬 Realisme Manusia", expanded=True):
        realism_level = st.select_slider("Detail Tekstur:", options=["Standard", "Detailed", "Hyper-Real (Pores & Sweat)"])
        mannerisms = st.multiselect("Human Mannerisms:", ["Natural Blinking", "Fixing hair", "Adjusting outfit", "Rhythmic breathing", "Eye-focus shift"], default=["Natural Blinking"])
        face_expr = st.selectbox("Ekspresi:", ["Warm smile", "Playful wink", "Confident smirk", "Joyful laugh"])

    with st.expander("🌬️ Fisika & Atmosfer", expanded=True):
        wind_power = st.select_slider("Kekuatan Angin:", options=["No Wind", "Soft Breeze", "Windy", "Strong Wind"])
        lighting_setup = st.selectbox("Pencahayaan:", ["Natural Soft Sunlight", "Golden Hour Glow", "Studio Softbox", "Neon Cyberpunk", "Dramatic Rim Lighting"])
        vfx_particles = st.selectbox("Efek VFX:", ["None", "Floating Dust", "Falling Petals", "Golden Sparkles", "Cinematic Rain"])

    st.markdown("---")
    bahasa = st.radio("Output Language:", ("English", "Bahasa Indonesia"))

# --- 6. MULTI-VIDEO UPLOADER & PREVIEW ---
st.markdown("### 🎬 1. Upload Reference Videos")
uploaded_files = st.file_uploader("Upload Video Referensi", type=["mp4", "mov", "avi"], accept_multiple_files=True)

if uploaded_files:
    # Menggunakan container untuk preview yang lebih fleksibel
    cols = st.columns(3)
    for idx, file in enumerate(uploaded_files):
        with cols[idx % 3]:
            st.video(file)
            st.caption(f"📄 {file.name}")

    st.markdown("---")
    if st.button("🔥 GENERATE DAN HASILKAN PROMPT", disabled=not st.session_state.api_active):
        st.session_state.all_prompts = [] 
        model = genai.GenerativeModel(model_name="gemini-flash-latest")

        for i, uploaded_file in enumerate(uploaded_files):
            file_name = uploaded_file.name
            with st.status(f"Analysing: {file_name}...") as status:
                try:
                    temp_path = f"temp_{i}_{file_name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    video_file = genai.upload_file(path=temp_path)
                    while video_file.state.name == "PROCESSING":
                        time.sleep(2)
                        video_file = genai.get_file(video_file.name)

                    instruction = "Analyze dance choreography. Extract ONLY skeletal movement in 1-second intervals for 20s. Separate Part 1 (0-10s) and Part 2 (10-20s) with '---SEPARATOR---'."
                    response = model.generate_content([video_file, instruction])
                    raw_motion = response.text

                    tex_mantra = "8k, raw photo, subsurface scattering, visible pores. " if realism_level == "Hyper-Real (Pores & Sweat)" else "Realistic human skin. "
                    soul_str = ", ".join(mannerisms)
                    
                    p1_prefix = (
                        f"Generate video Part 1. Shot: {shot_type}. Camera: {cam_movement} ({camera_gear}). "
                        f"[VISUAL LOCK] Use image as ABSOLUTE visual reference. Strictly maintain exact outfit and background. "
                        f"Lighting: {lighting_setup}. Expression: {face_expr}. Soul: {soul_str}. Wind: {wind_power}. VFX: {vfx_particles}. {tex_mantra} "
                        f"Follow this choreography:\n\n"
                    )
                    
                    p2_prefix = f"Continue Part 2. Maintain 100% consistency. Next sequence:\n\n"

                    if "---SEPARATOR---" in raw_motion:
                        parts = raw_motion.split("---SEPARATOR---")
                        p1, p2 = parts[0].strip(), parts[1].strip()
                    else:
                        p1, p2 = raw_motion, ""

                    st.session_state.all_prompts.append({
                        "name": file_name,
                        "p1": p1_prefix + p1,
                        "p2": p2_prefix + p2,
                        "video": uploaded_file
                    })

                    genai.delete_file(video_file.name)
                    os.remove(temp_path)
                    status.update(label=f"Done: {file_name}", state="complete")
                except Exception as e:
                    st.error(f"Error {file_name}: {e}")

# --- 7. STUDIO DISPLAY ---
if st.session_state.all_prompts:
    st.markdown("### 🚀 2. Final Motion Prompts")
    for idx, item in enumerate(st.session_state.all_prompts):
        with st.container():
            st.markdown(f'<div class="result-card"><h4>🎥 Video Reference: {item["name"]}</h4></div>', unsafe_allow_html=True)
            
            # Kolom hasil akan tumpuk otomatis di HP berkat CSS di atas
            col_res1, col_res2 = st.columns([1, 2])
            with col_res1:
                st.video(item['video'])
            with col_res2:
                t1, t2 = st.tabs(["📌 Prompt 1 (0-10s)", "📌 Prompt 2 (10-20s)"])
                with t1: 
                    st.code(item['p1'], language="text")
                with t2: 
                    st.code(item['p2'], language="text")
