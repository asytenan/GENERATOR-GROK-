import streamlit as st
import google.generativeai as genai
import yt_dlp
import time
import os
import re
import subprocess
from pathlib import Path

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="GROK APEX ARCHITECT", page_icon="⚡", layout="wide")

# --- CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600&display=swap');
html, body, [data-testid="stAppViewContainer"] { background-color: #050505; font-family: 'Inter', sans-serif; }
.main-header { font-family: 'Orbitron', sans-serif; font-size: 2.4rem; font-weight: 900; background: linear-gradient(90deg, #FFD700, #FF4B4B); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 15px; }
.glass-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 20px; padding: 24px; margin-bottom: 20px; }
.stButton>button { width: 100%; border-radius: 14px; font-weight: 700; background: linear-gradient(45deg, #FF4B4B, #800000); color: white; height: 3.2em; border: none; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'all_prompts' not in st.session_state: st.session_state.all_prompts = []
if 'api_key_saved' not in st.session_state: st.session_state.api_key_saved = ""
if 'api_active' not in st.session_state: st.session_state.api_active = False
if 'prepared_video' not in st.session_state: st.session_state.prepared_video = None
if 'fixed_videos' not in st.session_state: st.session_state.fixed_videos = []

# --- FUNGSI FIX CODEC (OTOMATIS) ---
def fix_video_codec(input_path: str, output_path: str):
    """Convert any video to web-compatible H.264 + AAC"""
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-c:v", "libx264",
        "-profile:v", "baseline",
        "-level", "3.0",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"FFmpeg error: {result.stderr}")
    return output_path

# --- FUNGSI DOWNLOAD + AUTO FIX CODEC ---
def download_and_fix_tiktok(url: str):
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    temp_path = "downloads/temp_download.mp4"
    final_path = "downloads/video_web_ready.mp4"

    # Download dulu
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': temp_path,
        'merge_output_format': 'mp4',
        'quiet': True,
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        detected_name = info.get('track') or info.get('title') or "Trend Dance"
        detected_name = re.sub(r'[^\w\s]', '', detected_name).strip()[:40]

    # Convert ke format web standar
    fix_video_codec(temp_path, final_path)

    # Baca file hasil
    with open(final_path, "rb") as f:
        video_bytes = f.read()

    # Bersihkan file temp
    if os.path.exists(temp_path):
        os.remove(temp_path)

    return video_bytes, detected_name, "motion_ready.mp4"

# --- HEADER ---
st.markdown('<p class="main-header">GROK APEX ARCHITECT PRO</p>', unsafe_allow_html=True)

# --- API KEY ---
with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    if not st.session_state.api_active:
        key = st.text_input("🔑 ENTER GEMINI API KEY", type="password")
        if st.button("🚀 INITIALIZE SYSTEM"):
            if key.startswith("AIza"):
                st.session_state.api_key_saved = key
                st.session_state.api_active = True
                st.rerun()
    else:
        col1, col2 = st.columns([5, 1])
        col1.success("✅ SYSTEM ONLINE - Ready for Motion Analysis")
        if col2.button("LOGOUT"):
            st.session_state.api_active = False
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## 🎛️ MASTER CONTROL")
    dance_name = st.text_input("🎵 Trend / Song Name", value="")
    style = st.selectbox("🎨 Visual Style", ["Hyper-Realistic", "Cinematic", "TikTok Viral", "Film Look"])
    camera = st.selectbox("📷 Camera Movement", ["Static", "Slow Zoom In", "Gentle Pan", "Handheld"])
    language = st.radio("🌍 Output Language", ["English", "Bahasa Indonesia"])

# --- STEP 1: DOWNLOAD + AUTO FIX ---
st.markdown("### 1. DOWNLOAD & AUTO FIX CODEC")

with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    url = st.text_input("Paste TikTok / YouTube Link", placeholder="https://www.tiktok.com/@.../video/...")

    if st.button("🔄 DOWNLOAD + FIX CODEC OTOMATIS", type="primary"):
        if url:
            with st.spinner("Downloading & Converting to Web Standard (H.264 Baseline)..."):
                try:
                    video_bytes, name, filename = download_and_fix_tiktok(url)
                    st.session_state.prepared_video = {
                        "bytes": video_bytes,
                        "name": name,
                        "filename": filename
                    }
                    st.success(f"✅ Video berhasil difix! Nama: {name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal: {str(e)}")

    # Preview video yang sudah difix
    if st.session_state.prepared_video:
        st.markdown("**✅ Video Siap Pakai (Codec Sudah Diperbaiki)**")
        st.video(st.session_state.prepared_video["bytes"])
        st.download_button(
            "📥 Download Video (Web Ready)",
            data=st.session_state.prepared_video["bytes"],
            file_name=st.session_state.prepared_video["filename"],
            mime="video/mp4"
        )
    st.markdown('</div>', unsafe_allow_html=True)

# --- STEP 2: UPLOAD & ANALYSIS ---
st.markdown("### 2. UPLOAD VIDEO & ANALISIS")

with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload Video (MP4/MOV) - Bisa multiple", type=["mp4", "mov"], accept_multiple_files=True)

    if uploaded:
        for i, file in enumerate(uploaded):
            col1, col2 = st.columns([1, 3])
            with col1:
                st.video(file)
            with col2:
                st.caption(f"📄 {file.name}")
                if st.button(f"🔧 Fix Codec Otomatis", key=f"fix_{i}"):
                    with st.spinner("Memperbaiki codec..."):
                        temp_in = f"temp_in_{i}.mp4"
                        temp_out = f"temp_out_{i}.mp4"
                        with open(temp_in, "wb") as f:
                            f.write(file.getbuffer())
                        try:
                            fix_video_codec(temp_in, temp_out)
                            with open(temp_out, "rb") as f:
                                fixed_bytes = f.read()
                            st.session_state.fixed_videos.append({
                                "name": f"fixed_{file.name}",
                                "bytes": fixed_bytes
                            })
                            st.success("✅ Codec berhasil diperbaiki!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal fix: {e}")
                        finally:
                            if os.path.exists(temp_in): os.remove(temp_in)
                            if os.path.exists(temp_out): os.remove(temp_out)

    # Tampilkan video yang sudah difix
    if st.session_state.fixed_videos:
        st.markdown("**📼 Video yang Sudah Di-Fix:**")
        for vid in st.session_state.fixed_videos:
            st.video(vid["bytes"])
            st.caption(vid["name"])
    st.markdown('</div>', unsafe_allow_html=True)

# --- GENERATE PROMPT ---
if st.button("🔥 GENERATE OFFICIAL PROMPT", disabled=not st.session_state.api_active):
    videos_to_process = uploaded or []
    if st.session_state.fixed_videos:
        videos_to_process += st.session_state.fixed_videos

    if not videos_to_process:
        st.warning("Upload minimal 1 video dulu!")
    else:
        st.session_state.all_prompts = []
        genai.configure(api_key=st.session_state.api_key_saved)
        model = genai.GenerativeModel("gemini-1.5-flash-latest")

        for video in videos_to_process:
            name = video.name if hasattr(video, 'name') else video.get("name", "Video")
            with st.status(f"Analyzing {name}...") as status:
                try:
                    # Simpan ke temp
                    temp_path = f"temp_{name}"
                    if hasattr(video, 'getbuffer'):
                        with open(temp_path, "wb") as f:
                            f.write(video.getbuffer())
                    else:
                        with open(temp_path, "wb") as f:
                            f.write(video["bytes"])

                    # Upload ke Gemini
                    vf = genai.upload_file(path=temp_path)
                    while vf.state.name == "PROCESSING":
                        time.sleep(2)
                        vf = genai.get_file(vf.name)

                    prompt = f"Analyze this dance video. Trend: {dance_name or 'Unknown'}. Give detailed 1-second skeletal motion breakdown. Separate Part 1 (0-10s) and Part 2 (10-20s) with '---SEPARATOR---'."
                    response = model.generate_content([vf, prompt])
                    raw = response.text

                    part1 = raw.split("---SEPARATOR---")[0].strip() if "---SEPARATOR---" in raw else raw
                    part2 = raw.split("---SEPARATOR---")[1].strip() if "---SEPARATOR---" in raw else "continuing the dance smoothly"

                    p1 = f"""Cinematic 10-second video.
[SUBJECT] Young woman dancing '{dance_name}' in exact same outfit and location from reference.
[CAMERA] {camera}.
[MOTION] {part1}
[STYLE] {style}, realistic film look, natural physics.
[VISUAL LOCK] Strictly keep exact character appearance, clothing, and background.
[TECHNICAL] 24fps, smooth motion, coherent movement."""

                    p2 = f"""Seamless continuation for another 10 seconds.
[CONTINUATION] {part2}
[CONSISTENCY] Same character, lighting, outfit, and environment.
[STYLE] {style}, high detail, natural motion."""

                    st.session_state.all_prompts.append({
                        "name": name,
                        "p1": p1,
                        "p2": p2,
                        "video": video.get("bytes") if isinstance(video, dict) else video.getbuffer()
                    })
                    os.remove(temp_path)
                    genai.delete_file(vf.name)
                    status.update(label=f"✅ Done: {name}", state="complete")
                except Exception as e:
                    st.error(f"Error analyzing {name}: {e}")

# --- HASIL PROMPT ---
if st.session_state.all_prompts:
    st.markdown("### 📜 FINAL PROMPTS")
    for item in st.session_state.all_prompts:
        with st.container():
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader(f"🎥 {item['name']}")
            c1, c2 = st.columns([1, 2])
            with c1:
                if isinstance(item['video'], bytes):
                    st.video(item['video'])
                else:
                    st.video(item['video'])
            with c2:
                t1, t2 = st.tabs(["Prompt 1 (10s)", "Prompt 2 (Extend)"])
                t1.code(item['p1'])
                t2.code(item['p2'])
            st.markdown('</div>', unsafe_allow_html=True)
