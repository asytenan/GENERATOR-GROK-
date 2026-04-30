import streamlit as st
import google.generativeai as genai
import time
import os
import yt_dlp
from pathlib import Path

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Grok Masterpiece - Official Format", page_icon="👑", layout="wide", initial_sidebar_state="expanded")

# CSS Responsif & UI (Tetap Dipertahankan)
st.markdown("""
    <style>
    @media (max-width: 768px) { .main-header { font-size: 1.6rem !important; } }
    .main-header { font-size: 2.8rem; font-weight: 800; color: #FFD700; text-align: center; margin-bottom: 5px; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; background-color: #FF4B4B; color: white; height: 3em; }
    .result-card { background-color: #1e272e; padding: 20px; border-radius: 15px; border-left: 5px solid #FFD700; margin-bottom: 20px; }
    .tiktok-box { background-color: #0f1a24; padding: 15px; border-radius: 12px; border: 1px solid #00f2ff; margin: 15px 0; }
    </style>
""", unsafe_allow_html=True)

# --- 2. INISIALISASI SESSION STATE ---
if 'all_prompts' not in st.session_state: st.session_state.all_prompts = [] 
if 'api_key_saved' not in st.session_state: st.session_state.api_key_saved = "" 
if 'api_active' not in st.session_state: st.session_state.api_active = False
if 'downloaded_videos' not in st.session_state: st.session_state.downloaded_videos = []  # list of {"path": str, "name": str}

# --- 3. HEADER ---
st.markdown('<p class="main-header">👑 GROK MOTION ARCHITECT</p>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #bdc3c7;">Batch Processing with Official Grok AI Prompting Structures + TikTok Import</p>', unsafe_allow_html=True)

# --- 4. API KEY MANAGER (FITUR TETAP ADA) ---
col_k1, col_k2, col_k3 = st.columns([1, 2, 1])
with col_k2:
    if not st.session_state.api_active:
        new_key = st.text_input("Enter Gemini API Key:", type="password")
        if st.button("💾 Save & Active"):
            if new_key: st.session_state.api_key_saved = new_key; st.session_state.api_active = True; st.rerun()
    else:
        st.success("✅ API Key Active")
        if st.button("🗑️ Change Key"): st.session_state.api_active = False; st.rerun()

st.divider()

# --- 5. CONTROL PANEL (FITUR EPIC TETAP LENGKAP) ---
with st.sidebar:
    st.markdown("## 🎛️ Control Panel")
    
    with st.expander("🎶 Context & Energy", expanded=True):
        dance_name = st.text_input("Nama Tarian/Lagu:", placeholder="Contoh: Tor Monitor Ketua")
        energy_lvl = st.select_slider("Vibe Kecepatan:", options=["Slow/Gentle", "Smooth", "Energetic"])

    with st.expander("📸 Sinematografi", expanded=True):
        camera_gear = st.selectbox("Gear:", ["Sony A7R IV, 35mm f/1.8", "Arri Alexa, 50mm Cinematic", "iPhone 15 Pro Max"])
        cam_movement = st.selectbox("Gerakan Kamera:", ["slow pan right", "slow pan left", "gentle dolly forward", "subtle tracking shot", "static with slight handheld"])
        shot_type = st.selectbox("Tipe Shot:", ["Full Body Wide Shot", "Medium Shot", "Close-up Focus"])

    with st.expander("🧬 Realisme & Soul", expanded=True):
        realism = st.select_slider("Tekstur Kulit:", options=["Standard", "Detailed", "Hyper-Real"])
        mannerisms = st.multiselect("Soul (Mannerisms):", ["Natural Blinking", "Fixing hair", "Adjusting outfit", "Rhythmic breathing"], default=["Natural Blinking"])
        face_expr = st.selectbox("Ekspresi:", ["Warm smile", "Playful wink", "Confident smirk", "Joyful laugh"])

    with st.expander("🌬️ Fisika & Lighting", expanded=True):
        wind_power = st.select_slider("Kekuatan Angin:", options=["soft breeze", "gentle wind", "windy"])
        lighting_fx = st.selectbox("Lighting:", ["Cinematic lighting", "Golden hour glow", "Studio professional", "Natural sunlight", "Moody atmosphere"])
        vfx_particles = st.selectbox("Efek VFX:", ["None", "Floating dust", "Falling petals", "Golden sparkles", "Cinematic rain"])

    bahasa = st.radio("Bahasa Output:", ("English", "Bahasa Indonesia"))

# --- 6. TIKTOK DOWNLOADER (FITUR BARU - SOLUSI PREVIEW) ---
st.markdown("### 📥 Download Video dari TikTok (Langsung Bisa Preview)")

with st.container():
    st.markdown('<div class="tiktok-box">', unsafe_allow_html=True)
    col_t1, col_t2 = st.columns([3, 1])
    
    with col_t1:
        tiktok_url = st.text_input(
            "Paste Link TikTok di sini:", 
            placeholder="https://www.tiktok.com/@username/video/1234567890123456789",
            key="tiktok_input"
        )
    
    with col_t2:
        download_btn = st.button("⬇️ DOWNLOAD", type="primary", disabled=not tiktok_url.strip(), use_container_width=True)
    
    if download_btn and tiktok_url.strip():
        with st.spinner("🔄 Sedang download dari TikTok (yt-dlp + ffmpeg)..."):
            try:
                download_dir = Path("references")
                download_dir.mkdir(exist_ok=True)
                
                unique_id = abs(hash(tiktok_url.strip())) % 100000000
                output_path = str(download_dir / f"tiktok_{unique_id}.mp4")
                
                ydl_opts = {
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'outtmpl': output_path,
                    'merge_output_format': 'mp4',
                    'quiet': True,
                    'no_warnings': True,
                    'postprocessors': [{
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': 'mp4',
                    }],
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(tiktok_url.strip(), download=True)
                    video_title = info.get('title', 'TikTok Video')[:60]
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 100000:
                    st.session_state.downloaded_videos.append({
                        "path": output_path,
                        "name": video_title
                    })
                    st.success(f"✅ Berhasil download: {video_title}")
                    st.video(output_path)  # ← INI YANG BIKIN PREVIEW LANGSUNG JALAN!
                else:
                    st.error("❌ File terlalu kecil atau gagal download. Coba link lain.")
                    
            except Exception as e:
                st.error(f"❌ Error download: {str(e)}")
                st.info("💡 Tips: Pastikan link TikTok publik & coba lagi. yt-dlp biasanya work bagus.")
    
    # Tampilkan daftar video TikTok yang sudah didownload
    if st.session_state.downloaded_videos:
        st.markdown("**📼 Video TikTok yang sudah ditambahkan:**")
        for i, vid in enumerate(st.session_state.downloaded_videos):
            col_v1, col_v2 = st.columns([4, 1])
            with col_v1:
                st.caption(f"• {vid['name'][:45]}...")
            with col_v2:
                if st.button("🗑️", key=f"del_{i}", help="Hapus video ini"):
                    if os.path.exists(vid["path"]):
                        os.remove(vid["path"])
                    st.session_state.downloaded_videos.pop(i)
                    st.rerun()
        
        if st.button("🧹 Clear Semua TikTok Video", type="secondary"):
            for vid in st.session_state.downloaded_videos:
                if os.path.exists(vid["path"]):
                    os.remove(vid["path"])
            st.session_state.downloaded_videos = []
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- 7. MULTI-VIDEO UPLOADER (BATCH TETAP ADA) ---
uploaded_files = st.file_uploader(
    "Upload Video Referensi Tari (Batch) - MP4/MOV/AVI", 
    type=["mp4", "mov", "avi"], 
    accept_multiple_files=True,
    key="batch_uploader"
)

# Gabungkan semua referensi (uploaded + downloaded)
all_reference_videos = []

if uploaded_files:
    for f in uploaded_files:
        all_reference_videos.append({"type": "upload", "obj": f, "name": f.name})

for dv in st.session_state.downloaded_videos:
    all_reference_videos.append({"type": "tiktok", "obj": dv["path"], "name": dv["name"]})

# Tampilkan preview semua video
if all_reference_videos:
    st.markdown("### 🎥 Semua Video Referensi (Upload + TikTok)")
    cols = st.columns(min(len(all_reference_videos), 3))
    for idx, ref in enumerate(all_reference_videos):
        with cols[idx % 3]:
            if ref["type"] == "upload":
                st.video(ref["obj"])
            else:
                st.video(ref["obj"])  # path string → tetap jalan!
            st.caption(ref["name"][:35] + ("..." if len(ref["name"]) > 35 else ""))

# --- 8. GENERATE BUTTON (DIPINDAH KE LUAR, BISA PAKAI TIKTOK SAJA) ---
has_any_video = bool(all_reference_videos)

if has_any_video:
    if st.button("🔥 GENERATE OFFICIAL GROK PROMPT", disabled=not st.session_state.api_active, type="primary"):
        st.session_state.all_prompts = [] 
        model = genai.GenerativeModel(model_name="gemini-2.5-flash")

        # Proses Uploaded Files
        for i, uploaded_file in enumerate(uploaded_files or []):
            with st.status(f"Grok-Style Precision Analysis: {uploaded_file.name}...") as status:
                try:
                    temp_path = f"temp_{i}_{uploaded_file.name}"
                    with open(temp_path, "wb") as f: f.write(uploaded_file.getbuffer())

                    video_file = genai.upload_file(path=temp_path)
                    while video_file.state.name == "PROCESSING": 
                        time.sleep(2)
                        video_file = genai.get_file(video_file.name)

                    instruction = f"""
                    Analyze this dance choreography. The dance is '{dance_name if dance_name else "Unknown Trend"}'.
                    Task: Provide a highly detailed 1-second interval skeletal motion breakdown focusing on weight shift and limb trajectory.
                    Separate with '---SEPARATOR---' for Part 1 (0-10s) and Part 2 (10-20s).
                    """
                    response = model.generate_content([video_file, instruction])
                    raw_motion = response.text

                    tex_mantra = "Visible skin pores, realistic skin texture, subsurface scattering, micro-skin details. " if realism == "Hyper-Real" else "High detail skin texture. "
                    soul_str = ", ".join(mannerisms)
                    vfx_str = f"{vfx_particles} particles in the air" if vfx_particles != "None" else "clear atmosphere"
                    
                    p1 = f"""A highly detailed cinematic 10-second video. 

[SUBJEK UTAMA + AKSI]
A young woman as seen in the reference image is performing the '{dance_name}' choreography in the exact same room and background from the image. 

[CAMERA MOVEMENT]
Camera {cam_movement} in a {shot_type}, revealing smooth and {energy_lvl.lower()} transitions. {camera_gear} lens feel.

[MOTION DETAIL]
{raw_motion.split('---SEPARATOR---')[0].strip() if '---SEPARATOR---' in raw_motion else raw_motion}
Every movement is natural with smooth motion. Human mannerisms: {soul_str}. {wind_power} effect on hair and outfit.

[STYLE & MOOD]
{lighting_fx}, {vfx_str}, {tex_mantra} {face_expr}, realistic filmic style. [VISUAL LOCK] Use image as ABSOLUTE visual reference. Strictly maintain exact character appearance, outfit, and environment. No morphing.

[TECHNICAL]
Smooth motion, high quality, 10 seconds duration, 24fps, natural physics, no sudden jumps, coherent movement, latent space stabilization."""

                    p2 = f"""Continue the previous 10-second video seamlessly for another 10 seconds.

[LANJUTAN AKSI]
The woman continues the '{dance_name}' dance choreography naturally from the previous clip. 

[MOTION CONTROL]
- Camera movement: {cam_movement}
- Character/Object motion: {raw_motion.split('---SEPARATOR---')[1].strip() if '---SEPARATOR---' in raw_motion else "continuing the fluid dance sequence"}, {soul_str}, {wind_power} blowing hair.
- Speed: {energy_lvl.lower()} cinematic pacing, no fast movements, coherent skeleton dynamics.

[CONSISTENCY]
Maintain exact same character appearance, clothing, lighting, and environment from the previous clip. Smooth transition, no jump cuts.

[STYLE]
{lighting_fx}, {tex_mantra} cinematic filmic color grade, high detail, natural physics, 10 seconds, smooth motion, coherent continuation."""

                    st.session_state.all_prompts.append({
                        "name": uploaded_file.name, "p1": p1, "p2": p2, "video": uploaded_file
                    })

                    genai.delete_file(video_file.name)
                    os.remove(temp_path)
                    status.update(label=f"Analysis Complete: {uploaded_file.name}", state="complete")
                except Exception as e:
                    st.error(f"Error processing {uploaded_file.name}: {e}")

        # Proses TikTok Downloaded Videos
        for dv in st.session_state.downloaded_videos:
            with st.status(f"Grok-Style Precision Analysis: {dv['name']}...") as status:
                try:
                    video_path = dv["path"]

                    video_file = genai.upload_file(path=video_path)
                    while video_file.state.name == "PROCESSING": 
                        time.sleep(2)
                        video_file = genai.get_file(video_file.name)

                    instruction = f"""
                    Analyze this dance choreography. The dance is '{dance_name if dance_name else "Unknown Trend"}'.
                    Task: Provide a highly detailed 1-second interval skeletal motion breakdown focusing on weight shift and limb trajectory.
                    Separate with '---SEPARATOR---' for Part 1 (0-10s) and Part 2 (10-20s).
                    """
                    response = model.generate_content([video_file, instruction])
                    raw_motion = response.text

                    tex_mantra = "Visible skin pores, realistic skin texture, subsurface scattering, micro-skin details. " if realism == "Hyper-Real" else "High detail skin texture. "
                    soul_str = ", ".join(mannerisms)
                    vfx_str = f"{vfx_particles} particles in the air" if vfx_particles != "None" else "clear atmosphere"
                    
                    p1 = f"""A highly detailed cinematic 10-second video. 

[SUBJEK UTAMA + AKSI]
A young woman as seen in the reference image is performing the '{dance_name}' choreography in the exact same room and background from the image. 

[CAMERA MOVEMENT]
Camera {cam_movement} in a {shot_type}, revealing smooth and {energy_lvl.lower()} transitions. {camera_gear} lens feel.

[MOTION DETAIL]
{raw_motion.split('---SEPARATOR---')[0].strip() if '---SEPARATOR---' in raw_motion else raw_motion}
Every movement is natural with smooth motion. Human mannerisms: {soul_str}. {wind_power} effect on hair and outfit.

[STYLE & MOOD]
{lighting_fx}, {vfx_str}, {tex_mantra} {face_expr}, realistic filmic style. [VISUAL LOCK] Use image as ABSOLUTE visual reference. Strictly maintain exact character appearance, outfit, and environment. No morphing.

[TECHNICAL]
Smooth motion, high quality, 10 seconds duration, 24fps, natural physics, no sudden jumps, coherent movement, latent space stabilization."""

                    p2 = f"""Continue the previous 10-second video seamlessly for another 10 seconds.

[LANJUTAN AKSI]
The woman continues the '{dance_name}' dance choreography naturally from the previous clip. 

[MOTION CONTROL]
- Camera movement: {cam_movement}
- Character/Object motion: {raw_motion.split('---SEPARATOR---')[1].strip() if '---SEPARATOR---' in raw_motion else "continuing the fluid dance sequence"}, {soul_str}, {wind_power} blowing hair.
- Speed: {energy_lvl.lower()} cinematic pacing, no fast movements, coherent skeleton dynamics.

[CONSISTENCY]
Maintain exact same character appearance, clothing, lighting, and environment from the previous clip. Smooth transition, no jump cuts.

[STYLE]
{lighting_fx}, {tex_mantra} cinematic filmic color grade, high detail, natural physics, 10 seconds, smooth motion, coherent continuation."""

                    st.session_state.all_prompts.append({
                        "name": dv["name"], "p1": p1, "p2": p2, "video": video_path
                    })

                    genai.delete_file(video_file.name)
                    status.update(label=f"Analysis Complete: {dv['name']}", state="complete")
                except Exception as e:
                    st.error(f"Error processing TikTok video {dv['name']}: {e}")

# --- 9. STUDIO DISPLAY (VISUAL PREVIEW + PROMPTS) ---
if st.session_state.all_prompts:
    st.divider()
    st.markdown("## 🎬 Hasil Prompt Grok Motion Architect")
    
    for idx, item in enumerate(st.session_state.all_prompts):
        with st.container():
            st.markdown(f'<div class="result-card"><h4>🎥 Video Reference: {item["name"]}</h4></div>', unsafe_allow_html=True)
            col_res1, col_res2 = st.columns([1, 2])
            with col_res1: 
                st.video(item['video'])  # Bisa UploadedFile atau path string
            with col_res2:
                t1, t2 = st.tabs(["📌 Prompt 1 (Main 10s)", "📌 Prompt 2 (Extend 10s)"])
                with t1: st.code(item['p1'], language="text")
                with t2: st.code(item['p2'], language="text")
    
    # Tombol copy all prompts
    if st.button("📋 Copy Semua Prompt ke Clipboard"):
        all_text = "\n\n".join([f"=== {p['name']} ===\n\nPROMPT 1:\n{p['p1']}\n\nPROMPT 2:\n{p['p2']}" for p in st.session_state.all_prompts])
        st.code(all_text)
        st.success("Semua prompt ditampilkan di atas. Silakan copy manual.")
