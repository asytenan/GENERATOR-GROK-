import streamlit as st
import google.generativeai as genai
import time
import os
import yt_dlp
from pathlib import Path

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Grok Masterpiece - Official Format", page_icon="👑", layout="wide", initial_sidebar_state="expanded")

# CSS
st.markdown("""
    <style>
    @media (max-width: 768px) { .main-header { font-size: 1.6rem !important; } }
    .main-header { font-size: 2.8rem; font-weight: 800; color: #FFD700; text-align: center; margin-bottom: 5px; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; background-color: #FF4B4B; color: white; height: 3em; }
    .result-card { background-color: #1e272e; padding: 20px; border-radius: 15px; border-left: 5px solid #FFD700; margin-bottom: 20px; }
    .tiktok-box { background-color: #0f1a24; padding: 15px; border-radius: 12px; border: 1px solid #00f2ff; margin: 15px 0; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if 'all_prompts' not in st.session_state: st.session_state.all_prompts = [] 
if 'api_key_saved' not in st.session_state: st.session_state.api_key_saved = "" 
if 'api_active' not in st.session_state: st.session_state.api_active = False
if 'downloaded_videos' not in st.session_state: st.session_state.downloaded_videos = []

# --- 3. HEADER ---
st.markdown('<p class="main-header">👑 GROK MOTION ARCHITECT</p>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #bdc3c7;">Batch Processing + TikTok Import (No FFmpeg)</p>', unsafe_allow_html=True)

# --- 4. API KEY ---
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

# --- 5. SIDEBAR CONTROL (TIDAK DIUBAH) ---
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

# --- 6. TIKTOK DOWNLOAD (VERSI TANPA FFMPEG - LEBIH STABIL) ---
st.markdown("### 📥 Download Video dari TikTok")

with st.container():
    st.markdown('<div class="tiktok-box">', unsafe_allow_html=True)
    col_t1, col_t2 = st.columns([3, 1])
    
    with col_t1:
        tiktok_url = st.text_input("Paste Link TikTok:", placeholder="https://www.tiktok.com/@username/video/1234567890", key="tiktok_input")
    
    with col_t2:
        if st.button("⬇️ DOWNLOAD", type="primary", disabled=not tiktok_url.strip(), use_container_width=True):
            with st.spinner("🔄 Downloading dari TikTok..."):
                try:
                    download_dir = Path("references")
                    download_dir.mkdir(exist_ok=True)
                    unique_id = abs(hash(tiktok_url.strip())) % 100000000
                    output_path = str(download_dir / f"tiktok_{unique_id}.mp4")
                    
                    # VERSI RINGAN TANPA FFMPEG
                    ydl_opts = {
                        'format': 'best[ext=mp4]/best',
                        'outtmpl': output_path,
                        'quiet': True,
                        'no_warnings': True,
                        'http_headers': {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
                        }
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(tiktok_url.strip(), download=True)
                        video_title = info.get('title', 'TikTok Video')[:50]
                    
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 80000:
                        st.session_state.downloaded_videos.append({"path": output_path, "name": video_title})
                        st.success(f"✅ Berhasil download: {video_title}")
                        st.video(output_path)
                    else:
                        st.error("❌ File terlalu kecil. Coba link lain atau upload manual.")
                        
                except Exception as e:
                    st.error(f"❌ Gagal download: {str(e)}")
                    st.info("💡 Saran: Download manual dari tiktokdownloader.site lalu upload biasa.")
    
    # Daftar video TikTok
    if st.session_state.downloaded_videos:
        st.markdown("**📼 Video TikTok ditambahkan:**")
        for i, vid in enumerate(st.session_state.downloaded_videos):
            c1, c2 = st.columns([5, 1])
            with c1: st.caption(f"• {vid['name'][:50]}")
            with c2:
                if st.button("🗑️", key=f"del_tiktok_{i}"):
                    if os.path.exists(vid["path"]): os.remove(vid["path"])
                    st.session_state.downloaded_videos.pop(i)
                    st.rerun()
        
        if st.button("🧹 Hapus Semua TikTok Video"):
            for v in st.session_state.downloaded_videos:
                if os.path.exists(v["path"]): os.remove(v["path"])
            st.session_state.downloaded_videos = []
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- 7. UPLOAD BATCH + PREVIEW ---
uploaded_files = st.file_uploader("Upload Video Referensi Tari (Batch)", type=["mp4", "mov", "avi"], accept_multiple_files=True)

all_refs = []
if uploaded_files:
    for f in uploaded_files:
        all_refs.append({"type": "upload", "obj": f, "name": f.name})
for dv in st.session_state.downloaded_videos:
    all_refs.append({"type": "tiktok", "obj": dv["path"], "name": dv["name"]})

if all_refs:
    st.markdown("### 🎥 Semua Video Referensi")
    cols = st.columns(min(len(all_refs), 3))
    for idx, ref in enumerate(all_refs):
        with cols[idx % 3]:
            st.video(ref["obj"])
            st.caption(ref["name"][:40])

# --- 8. GENERATE BUTTON ---
if all_refs:
    if st.button("🔥 GENERATE OFFICIAL GROK PROMPT", disabled=not st.session_state.api_active, type="primary"):
        st.session_state.all_prompts = []
        model = genai.GenerativeModel(model_name="gemini-2.5-flash")

        # Proses Upload
        for i, up in enumerate(uploaded_files or []):
            with st.status(f"Analyzing: {up.name}...") as status:
                try:
                    tmp = f"temp_{i}_{up.name}"
                    with open(tmp, "wb") as f: f.write(up.getbuffer())
                    vf = genai.upload_file(path=tmp)
                    while vf.state.name == "PROCESSING": time.sleep(2); vf = genai.get_file(vf.name)
                    
                    instr = f"Analyze this dance choreography. The dance is '{dance_name or 'Unknown Trend'}'. Provide detailed 1-second skeletal motion breakdown. Separate Part 1 (0-10s) and Part 2 (10-20s) with '---SEPARATOR---'."
                    resp = model.generate_content([vf, instr])
                    raw = resp.text
                    
                    tex = "Visible skin pores, realistic skin texture... " if realism == "Hyper-Real" else "High detail skin texture. "
                    soul = ", ".join(mannerisms)
                    vfx = f"{vfx_particles} particles" if vfx_particles != "None" else "clear atmosphere"
                    
                    p1 = f"""A highly detailed cinematic 10-second video.

[SUBJEK UTAMA + AKSI]
A young woman performing '{dance_name}' choreography in the exact same room from the reference.

[CAMERA]
Camera {cam_movement} in a {shot_type}. {camera_gear} lens.

[MOTION]
{raw.split('---SEPARATOR---')[0].strip() if '---SEPARATOR---' in raw else raw}
Natural movement, {soul}, {wind_power} on hair.

[STYLE]
{lighting_fx}, {vfx}, {tex} {face_expr}, realistic filmic style. [VISUAL LOCK] Exact character, outfit, environment from reference.

[TECHNICAL]
10 seconds, 24fps, smooth motion, natural physics."""

                    p2 = f"""Continue seamlessly for another 10 seconds.

[LANJUTAN]
The woman continues the '{dance_name}' choreography naturally.

[MOTION CONTROL]
Camera {cam_movement}, {raw.split('---SEPARATOR---')[1].strip() if '---SEPARATOR---' in raw else 'continuing fluid motion'}, {soul}, {wind_power}.

[CONSISTENCY]
Exact same character, lighting, environment. Smooth transition.

[STYLE]
{lighting_fx}, high detail, natural physics, 10 seconds."""

                    st.session_state.all_prompts.append({"name": up.name, "p1": p1, "p2": p2, "video": up})
                    genai.delete_file(vf.name)
                    os.remove(tmp)
                    status.update(label=f"Done: {up.name}", state="complete")
                except Exception as e:
                    st.error(f"Error: {e}")

        # Proses TikTok
        for dv in st.session_state.downloaded_videos:
            with st.status(f"Analyzing: {dv['name']}...") as status:
                try:
                    vf = genai.upload_file(path=dv["path"])
                    while vf.state.name == "PROCESSING": time.sleep(2); vf = genai.get_file(vf.name)
                    
                    instr = f"Analyze this dance choreography. The dance is '{dance_name or 'Unknown Trend'}'. Provide detailed 1-second skeletal motion breakdown. Separate Part 1 (0-10s) and Part 2 (10-20s) with '---SEPARATOR---'."
                    resp = model.generate_content([vf, instr])
                    raw = resp.text
                    
                    tex = "Visible skin pores... " if realism == "Hyper-Real" else "High detail skin texture. "
                    soul = ", ".join(mannerisms)
                    vfx = f"{vfx_particles} particles" if vfx_particles != "None" else "clear atmosphere"
                    
                    p1 = f"""A highly detailed cinematic 10-second video.

[SUBJEK UTAMA + AKSI]
A young woman performing '{dance_name}' choreography in the exact same room from the reference.

[CAMERA]
Camera {cam_movement} in a {shot_type}. {camera_gear} lens.

[MOTION]
{raw.split('---SEPARATOR---')[0].strip() if '---SEPARATOR---' in raw else raw}
Natural movement, {soul}, {wind_power} on hair.

[STYLE]
{lighting_fx}, {vfx}, {tex} {face_expr}, realistic filmic style. [VISUAL LOCK] Exact character from reference.

[TECHNICAL]
10 seconds, 24fps, smooth motion."""

                    p2 = f"""Continue seamlessly for another 10 seconds.

[LANJUTAN]
The woman continues the '{dance_name}' choreography naturally.

[MOTION CONTROL]
Camera {cam_movement}, {raw.split('---SEPARATOR---')[1].strip() if '---SEPARATOR---' in raw else 'continuing motion'}, {soul}, {wind_power}.

[CONSISTENCY]
Exact same character, lighting, environment.

[STYLE]
{lighting_fx}, high detail, natural physics, 10 seconds."""

                    st.session_state.all_prompts.append({"name": dv["name"], "p1": p1, "p2": p2, "video": dv["path"]})
                    genai.delete_file(vf.name)
                    status.update(label=f"Done: {dv['name']}", state="complete")
                except Exception as e:
                    st.error(f"Error: {e}")

# --- 9. HASIL PROMPT ---
if st.session_state.all_prompts:
    st.divider()
    st.markdown("## 🎬 Hasil Prompt")
    for item in st.session_state.all_prompts:
        with st.container():
            st.markdown(f'<div class="result-card"><h4>🎥 {item["name"]}</h4></div>', unsafe_allow_html=True)
            c1, c2 = st.columns([1, 2])
            with c1: st.video(item['video'])
            with c2:
                t1, t2 = st.tabs(["Prompt 1 (10s)", "Prompt 2 (Extend)"])
                with t1: st.code(item['p1'])
                with t2: st.code(item['p2'])
