import streamlit as st
import google.generativeai as genai
import yt_dlp
import time
import os
import re
import subprocess

# ==================== PAGE CONFIG ====================
st.set_page_config(page_title="GROK APEX ARCHITECT", page_icon="⚡", layout="wide")

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #050505;
    font-family: 'Inter', sans-serif;
}

.main-header {
    font-family: 'Orbitron', sans-serif;
    font-size: 2.6rem;
    font-weight: 900;
    background: linear-gradient(90deg, #FFD700, #FF4B4B);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 10px;
}

.glass-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 20px;
    padding: 24px;
    margin-bottom: 20px;
}

.instant-box {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border: 2px solid #FFD700;
    border-radius: 24px;
    padding: 28px;
    margin-bottom: 25px;
    box-shadow: 0 0 30px rgba(255, 215, 0, 0.15);
}

.stButton>button {
    width: 100%;
    border-radius: 14px;
    font-weight: 700;
    background: linear-gradient(45deg, #FF4B4B, #800000);
    color: white;
    height: 3.2em;
    border: none;
    font-size: 1.05rem;
}

.instant-btn {
    background: linear-gradient(45deg, #FFD700, #FFA500) !important;
    color: #000000 !important;
    font-weight: 900 !important;
    font-size: 1.15rem !important;
    height: 3.6em !important;
    box-shadow: 0 0 25px rgba(255, 215, 0, 0.5);
}

.success-box {
    background-color: #0a2f1f;
    border: 1px solid #22c55e;
    border-radius: 16px;
    padding: 16px;
    margin-top: 15px;
}
</style>
""", unsafe_allow_html=True)

# ==================== SESSION STATE ====================
if 'all_prompts' not in st.session_state: st.session_state.all_prompts = []
if 'api_key_saved' not in st.session_state: st.session_state.api_key_saved = ""
if 'api_active' not in st.session_state: st.session_state.api_active = False
if 'reference_videos' not in st.session_state: st.session_state.reference_videos = []
if 'auto_dance_name' not in st.session_state: st.session_state.auto_dance_name = ""

# ==================== HELPER FUNCTIONS ====================
def fix_video_codec(input_path: str, output_path: str):
    """Convert video to universal web format (H.264 Baseline)"""
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-c:v", "libx264", "-profile:v", "baseline", "-level", "3.0",
        "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(result.stderr)
    return output_path

def download_and_prepare_video(url: str):
    """Download + Remove watermark + Fix codec + Detect song"""
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    temp_path = "downloads/temp_raw.mp4"
    final_path = "downloads/ready_video.mp4"

    # Download with yt-dlp (best quality + no watermark where possible)
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': temp_path,
        'merge_output_format': 'mp4',
        'quiet': True,
        'noplaylist': True,
        'writesubtitles': False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        
        # Auto-detect song / music / backsound
        song_name = (
            info.get('track') or 
            info.get('alt_title') or 
            info.get('title') or 
            "Unknown Trend"
        )
        # Clean song name
        song_name = re.sub(r'[^\w\s\-]', '', song_name).strip()[:50]

    # Fix codec to web standard
    fix_video_codec(temp_path, final_path)

    # Read final video
    with open(final_path, "rb") as f:
        video_bytes = f.read()

    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)

    return video_bytes, song_name, "ready_video.mp4"

# ==================== HEADER ====================
st.markdown('<p class="main-header">GROK APEX ARCHITECT</p>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:#aaa; margin-top:-10px; font-size:1.1rem;">Instant Link Mode • Auto Detect Music • One-Click Magic</p>', unsafe_allow_html=True)

# ==================== API KEY ====================
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
        c1, c2 = st.columns([6, 1])
        c1.success("✅ SYSTEM ONLINE")
        if c2.button("LOGOUT"):
            st.session_state.api_active = False
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("## 🎛️ MASTER CONTROL")
    dance_name = st.text_input("🎵 Nama Tarian / Lagu", value=st.session_state.auto_dance_name)
    style = st.selectbox("🎨 Visual Style", ["Hyper-Realistic", "Cinematic", "TikTok Viral", "Film Look"])
    camera = st.selectbox("📷 Camera Movement", ["Static", "Slow Zoom In", "Gentle Pan", "Handheld"])
    language = st.radio("🌍 Language", ["English", "Bahasa Indonesia"])

# ==================== 🚀 INSTANT LINK MODE (NEW FEATURE) ====================
st.markdown("### 🚀 INSTANT LINK MODE (Recommended)")

with st.container():
    st.markdown('<div class="instant-box">', unsafe_allow_html=True)
    st.markdown("**Paste link video TikTok / YouTube / Instagram → Klik 1 tombol → Langsung siap!**")
    
    url_input = st.text_input("🔗 Paste Video Link", placeholder="https://www.tiktok.com/@username/video/1234567890", key="instant_url")

    if st.button("🚀 INSTANT DOWNLOAD + AUTO DETECT + PREPARE", key="instant_btn", help="Download + Fix Codec + Detect Song + Auto Fill"):
        if url_input.strip():
            with st.spinner("🔄 Downloading, removing watermark, fixing codec, and detecting music..."):
                try:
                    video_bytes, song_name, filename = download_and_prepare_video(url_input.strip())
                    
                    # Auto fill dance name
                    st.session_state.auto_dance_name = song_name
                    
                    # Add to reference videos
                    st.session_state.reference_videos.append({
                        "name": song_name,
                        "bytes": video_bytes,
                        "filename": filename
                    })
                    
                    st.success(f"✅ Berhasil! Lagu terdeteksi: **{song_name}**")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Gagal memproses link: {str(e)}")
        else:
            st.warning("Link tidak boleh kosong!")

    # Show prepared videos from Instant Link
    if st.session_state.reference_videos:
        st.markdown("**📼 Video yang sudah disiapkan (Instant Link):**")
        for i, vid in enumerate(st.session_state.reference_videos):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.video(vid["bytes"])
                st.caption(f"🎵 {vid['name']}")
            with col2:
                if st.button("🗑️ Hapus", key=f"del_instant_{i}"):
                    st.session_state.reference_videos.pop(i)
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== MANUAL UPLOAD (BACKUP) ====================
st.markdown("### 📤 MANUAL UPLOAD (Cadangan)")

with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    uploaded_files = st.file_uploader("Upload Video Manual (MP4/MOV)", type=["mp4", "mov"], accept_multiple_files=True)

    if uploaded_files:
        for i, file in enumerate(uploaded_files):
            col1, col2 = st.columns([1, 3])
            with col1:
                st.video(file)
            with col2:
                st.caption(f"📄 {file.name}")
                if st.button(f"🔧 Fix Codec", key=f"fix_manual_{i}"):
                    with st.spinner("Memperbaiki codec..."):
                        temp_in = f"temp_in_{i}.mp4"
                        temp_out = f"temp_out_{i}.mp4"
                        with open(temp_in, "wb") as f: f.write(file.getbuffer())
                        try:
                            fix_video_codec(temp_in, temp_out)
                            with open(temp_out, "rb") as f:
                                fixed_bytes = f.read()
                            st.session_state.reference_videos.append({
                                "name": f"Fixed_{file.name}",
                                "bytes": fixed_bytes,
                                "filename": file.name
                            })
                            st.success("✅ Codec diperbaiki & ditambahkan!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal: {e}")
                        finally:
                            if os.path.exists(temp_in): os.remove(temp_in)
                            if os.path.exists(temp_out): os.remove(temp_out)
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== GENERATE BUTTON ====================
all_videos = st.session_state.reference_videos + (uploaded_files or [])

if st.button("🔥 GENERATE OFFICIAL PROMPT", disabled=not st.session_state.api_active or len(all_videos) == 0):
    st.session_state.all_prompts = []
    genai.configure(api_key=st.session_state.api_key_saved)
    model = genai.GenerativeModel("gemini-1.5-flash-latest")

    for video in all_videos:
        name = video.get("name", "Video") if isinstance(video, dict) else video.name
        
        with st.status(f"Analyzing {name}...") as status:
            try:
                # Save to temp
                temp_path = f"temp_{name.replace(' ', '_')}.mp4"
                if isinstance(video, dict):
                    with open(temp_path, "wb") as f: f.write(video["bytes"])
                else:
                    with open(temp_path, "wb") as f: f.write(video.getbuffer())

                # Upload to Gemini
                vf = genai.upload_file(path=temp_path)
                while vf.state.name == "PROCESSING":
                    time.sleep(2)
                    vf = genai.get_file(vf.name)

                # Analysis prompt
                analysis_prompt = f"""Analyze this dance video.
Trend/Song: {dance_name or name}
Task: Provide detailed 1-second skeletal motion breakdown.
Separate Part 1 (0-10s) and Part 2 (10-20s) with '---SEPARATOR---'."""

                response = model.generate_content([vf, analysis_prompt])
                raw = response.text

                part1 = raw.split("---SEPARATOR---")[0].strip() if "---SEPARATOR---" in raw else raw
                part2 = raw.split("---SEPARATOR---")[1].strip() if "---SEPARATOR---" in raw else "continuing the dance smoothly"

                # Build final prompts
                p1 = f"""Cinematic 10-second video.

[SUBJECT] Young woman dancing '{dance_name or name}' in exact same outfit and location from reference.
[CAMERA] {camera}.
[MOTION] {part1}
[STYLE] {style}, realistic film look, natural physics, high detail.
[VISUAL LOCK] Strictly maintain exact character appearance, clothing, and background.
[TECHNICAL] 24fps, smooth motion, coherent movement, latent space stabilization."""

                p2 = f"""Seamless continuation for another 10 seconds.

[CONTINUATION] {part2}
[CONSISTENCY] Same character, lighting, outfit, and environment from previous clip.
[STYLE] {style}, high detail, natural motion."""

                # Add to results
                video_data = video.get("bytes") if isinstance(video, dict) else video.getbuffer()
                st.session_state.all_prompts.append({
                    "name": name,
                    "p1": p1,
                    "p2": p2,
                    "video": video_data
                })

                os.remove(temp_path)
                genai.delete_file(vf.name)
                status.update(label=f"✅ Done: {name}", state="complete")

            except Exception as e:
                st.error(f"Error analyzing {name}: {e}")

# ==================== RESULTS ====================
if st.session_state.all_prompts:
    st.markdown("### 📜 FINAL PROMPTS")
    for item in st.session_state.all_prompts:
        with st.container():
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader(f"🎥 {item['name']}")
            c1, c2 = st.columns([1, 2])
            with c1:
                st.video(item['video'])
            with c2:
                t1, t2 = st.tabs(["📌 Prompt 1 (10s)", "📌 Prompt 2 (Extend)"])
                t1.code(item['p1'])
                t2.code(item['p2'])
            st.markdown('</div>', unsafe_allow_html=True)

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("<p style='text-align:center; color:#666; font-size:0.85rem;'>GROK APEX ARCHITECT • Instant Link Mode • Powered by Gemini 1.5 + yt-dlp + FFmpeg</p>", unsafe_allow_html=True)
