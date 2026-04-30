import streamlit as st
import google.generativeai as genai
import yt_dlp
import time
import os
import re
import subprocess
from datetime import datetime

# ==================== PAGE CONFIG ====================
st.set_page_config(page_title="GROK APEX ULTIMATE", page_icon="⚡", layout="wide")

# ==================== CUSTOM CSS + ANIMATIONS ====================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #050505;
    font-family: 'Inter', sans-serif;
}

.main-header {
    font-family: 'Orbitron', sans-serif;
    font-size: 2.8rem;
    font-weight: 900;
    background: linear-gradient(90deg, #FFD700, #FF4B4B);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 5px;
    animation: glow 2s ease-in-out infinite alternate;
}

@keyframes glow {
    from { text-shadow: 0 0 10px #FFD700; }
    to { text-shadow: 0 0 25px #FF4B4B; }
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
    box-shadow: 0 0 40px rgba(255, 215, 0, 0.2);
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
    transition: all 0.3s ease;
}

.stButton>button:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 20px rgba(255, 75, 75, 0.4);
}

.instant-btn {
    background: linear-gradient(45deg, #FFD700, #FFA500) !important;
    color: #000000 !important;
    font-weight: 900 !important;
    font-size: 1.2rem !important;
    height: 3.8em !important;
    box-shadow: 0 0 35px rgba(255, 215, 0, 0.7) !important;
}

.loading-text {
    font-size: 1.1rem;
    color: #FFD700;
    animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

.history-item {
    background: #1a1a2e;
    border-radius: 12px;
    padding: 10px 15px;
    margin: 8px 0;
    border-left: 4px solid #FFD700;
    transition: all 0.2s ease;
}

.history-item:hover {
    background: #252545;
    transform: translateX(5px);
}
</style>
""", unsafe_allow_html=True)

# ==================== SESSION STATE ====================
if 'all_prompts' not in st.session_state: st.session_state.all_prompts = []
if 'api_key_saved' not in st.session_state: st.session_state.api_key_saved = ""
if 'api_active' not in st.session_state: st.session_state.api_active = False
if 'reference_videos' not in st.session_state: st.session_state.reference_videos = []
if 'auto_dance_name' not in st.session_state: st.session_state.auto_dance_name = ""
if 'link_history' not in st.session_state: st.session_state.link_history = []

# ==================== ADVANCED DOWNLOAD FUNCTION ====================
def advanced_download(url: str, progress_callback=None):
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    temp_path = "downloads/temp_raw.mp4"
    final_path = "downloads/ready.mp4"

    if progress_callback:
        progress_callback("Downloading video...")

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': temp_path,
        'merge_output_format': 'mp4',
        'quiet': True,
        'noplaylist': True,
        'extractor_args': {
            'tiktok': {
                'api_hostname': 'api16-normal-c-useast1a.tiktokv.com',
                'app_version': '34.1.2',
                'manifest_app_version': '2023401020',
            }
        },
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        song_name = (info.get('track') or info.get('alt_title') or info.get('title') or "Unknown Trend")
        song_name = re.sub(r'[^\w\s\-]', '', song_name).strip()[:50]

    if progress_callback:
        progress_callback("Fixing codec & removing watermark...")

    cmd = [
        "ffmpeg", "-y", "-i", temp_path,
        "-c:v", "libx264", "-profile:v", "baseline", "-level", "3.0",
        "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-vf", "crop=iw:ih-80:0:0",
        "-movflags", "+faststart",
        final_path
    ]
    subprocess.run(cmd, capture_output=True)

    with open(final_path, "rb") as f:
        video_bytes = f.read()

    if os.path.exists(temp_path):
        os.remove(temp_path)

    return video_bytes, song_name, "ready_video.mp4"

# ==================== HEADER ====================
st.markdown('<p class="main-header">GROK APEX ULTIMATE</p>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:#aaa; margin-top:-8px; font-size:1.05rem;">Batch Link • No Watermark • History • Animated Experience</p>', unsafe_allow_html=True)

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

# ==================== SIDEBAR (HISTORY) ====================
with st.sidebar:
    st.markdown("## 🎛️ MASTER CONTROL")
    dance_name = st.text_input("🎵 Nama Tarian / Lagu", value=st.session_state.auto_dance_name)
    style = st.selectbox("🎨 Visual Style", ["Hyper-Realistic", "Cinematic", "TikTok Viral", "Film Look"])
    camera = st.selectbox("📷 Camera Movement", ["Static", "Slow Zoom In", "Gentle Pan", "Handheld"])
    language = st.radio("🌍 Language", ["English", "Bahasa Indonesia"])

    st.markdown("---")
    st.markdown("## 📜 LINK HISTORY")

    if st.session_state.link_history:
        for i, item in enumerate(reversed(st.session_state.link_history[-10:])):
            with st.container():
                st.markdown(f'<div class="history-item">', unsafe_allow_html=True)
                st.caption(f"🕒 {item['time']}")
                st.write(f"🎵 **{item['song']}**")
                if st.button("🔄 Gunakan Lagi", key=f"use_history_{i}"):
                    st.session_state.reference_videos.append({
                        "name": item['song'],
                        "bytes": item['bytes'],
                        "filename": item['filename'],
                        "source": "history"
                    })
                    st.success("✅ Ditambahkan ke Ready!")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Belum ada history")

# ==================== 🚀 BATCH INSTANT LINK ====================
st.markdown("### 🚀 BATCH INSTANT LINK")

with st.container():
    st.markdown('<div class="instant-box">', unsafe_allow_html=True)
    st.markdown("**Paste banyak link (satu per baris) → Otomatis masuk ke Ready to Generate**")

    links_text = st.text_area(
        "🔗 Paste Links (satu per baris)",
        height=110,
        placeholder="https://www.tiktok.com/@user/video/111\nhttps://www.tiktok.com/@user/video/222"
    )

    if st.button("🚀 PROCESS ALL LINKS + ANIMATED PROGRESS", key="batch_btn"):
        if links_text.strip():
            links = [line.strip() for line in links_text.strip().split('\n') if line.strip()]
            total = len(links)
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            success_count = 0
            
            for i, link in enumerate(links):
                percent = int(((i + 1) / total) * 100)
                progress_bar.progress(percent)
                
                status_text.markdown(f"""
                <div class="loading-text">
                ⏳ Memproses link {i+1} dari {total}...<br>
                <small>{link[:60]}...</small>
                </div>
                """, unsafe_allow_html=True)
                
                try:
                    video_bytes, song_name, filename = advanced_download(link)
                    
                    # Simpan ke reference
                    st.session_state.reference_videos.append({
                        "name": song_name,
                        "bytes": video_bytes,
                        "filename": filename,
                        "source": "link"
                    })
                    
                    # Simpan ke history
                    st.session_state.link_history.append({
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "song": song_name,
                        "bytes": video_bytes,
                        "filename": filename,
                        "link": link
                    })
                    
                    # Auto fill jika hanya 1 link
                    if total == 1:
                        st.session_state.auto_dance_name = song_name
                    
                    success_count += 1
                    
                except Exception as e:
                    st.error(f"❌ Gagal link ke-{i+1}: {str(e)}")
            
            progress_bar.progress(100)
            status_text.success(f"✅ Selesai! {success_count}/{total} video berhasil diproses.")
            time.sleep(1.5)
            st.rerun()
        else:
            st.warning("Tidak ada link!")

    st.markdown('</div>', unsafe_allow_html=True)

# ==================== 📋 READY TO GENERATE ====================
st.markdown("### 📋 READY TO GENERATE")

with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    if st.session_state.reference_videos:
        st.markdown(f"**Total Video Siap: {len(st.session_state.reference_videos)}**")
        
        for i, vid in enumerate(st.session_state.reference_videos):
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.video(vid["bytes"])
                st.caption(f"🎵 {vid['name']} ({vid.get('source', 'manual')})")
            with col2:
                if st.button("🗑️", key=f"del_ready_{i}"):
                    st.session_state.reference_videos.pop(i)
                    st.rerun()
            with col3:
                st.write("")
    else:
        st.info("Belum ada video siap. Gunakan Batch Link di atas.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== 📤 MANUAL UPLOAD ====================
st.markdown("### 📤 MANUAL UPLOAD (Cadangan)")

with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    uploaded_files = st.file_uploader("Upload Video Manual", type=["mp4", "mov"], accept_multiple_files=True)

    if uploaded_files:
        for i, file in enumerate(uploaded_files):
            col1, col2 = st.columns([1, 3])
            with col1:
                st.video(file)
            with col2:
                st.caption(file.name)
                if st.button(f"🔧 Fix + Add", key=f"fix_{i}"):
                    with st.spinner("⏳ Processing..."):
                        temp_in = f"temp_in_{i}.mp4"
                        with open(temp_in, "wb") as f: f.write(file.getbuffer())
                        try:
                            video_bytes, song_name, _ = advanced_download(temp_in)
                            st.session_state.reference_videos.append({
                                "name": song_name,
                                "bytes": video_bytes,
                                "filename": file.name,
                                "source": "manual"
                            })
                            st.success("✅ Ditambahkan!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal: {e}")
                        finally:
                            if os.path.exists(temp_in): os.remove(temp_in)
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== 🔥 GENERATE ====================
if st.button("🔥 GENERATE OFFICIAL PROMPT", disabled=not st.session_state.api_active or len(st.session_state.reference_videos) == 0):
    st.session_state.all_prompts = []
    genai.configure(api_key=st.session_state.api_key_saved)
    model = genai.GenerativeModel("gemini-1.5-flash-latest")

    total = len(st.session_state.reference_videos)
    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, video in enumerate(st.session_state.reference_videos):
        percent = int(((idx + 1) / total) * 100)
        progress_bar.progress(percent)
        status_text.markdown(f"⏳ Generating prompt {idx+1}/{total} — **{video['name']}**", unsafe_allow_html=True)

        name = video["name"]
        
        with st.status(f"Analyzing {name}...") as status:
            try:
                temp_path = f"temp_{name.replace(' ', '_')}.mp4"
                with open(temp_path, "wb") as f: f.write(video["bytes"])

                vf = genai.upload_file(path=temp_path)
                while vf.state.name == "PROCESSING":
                    time.sleep(2)
                    vf = genai.get_file(vf.name)

                analysis_prompt = f"Analyze this dance video. Trend/Song: {dance_name or name}. Provide detailed 1-second skeletal motion breakdown. Separate Part 1 and Part 2 with '---SEPARATOR---'."
                response = model.generate_content([vf, analysis_prompt])
                raw = response.text

                part1 = raw.split("---SEPARATOR---")[0].strip() if "---SEPARATOR---" in raw else raw
                part2 = raw.split("---SEPARATOR---")[1].strip() if "---SEPARATOR---" in raw else "continuing smoothly"

                p1 = f"""Cinematic 10-second video.
[SUBJECT] Young woman dancing '{dance_name or name}' in exact same outfit and location from reference.
[CAMERA] {camera}.
[MOTION] {part1}
[STYLE] {style}, realistic film look, natural physics, high detail.
[VISUAL LOCK] Strictly maintain exact character, clothing, and background.
[TECHNICAL] 24fps, smooth motion, coherent movement."""

                p2 = f"""Seamless continuation for another 10 seconds.
[CONTINUATION] {part2}
[CONSISTENCY] Same character, lighting, outfit, and environment."""

                st.session_state.all_prompts.append({
                    "name": name,
                    "p1": p1,
                    "p2": p2,
                    "video": video["bytes"]
                })

                os.remove(temp_path)
                genai.delete_file(vf.name)
                status.update(label=f"✅ Done: {name}", state="complete")

            except Exception as e:
                st.error(f"Error analyzing {name}: {e}")

    progress_bar.progress(100)
    status_text.success("🎉 Semua prompt berhasil dibuat!")

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
                t1, t2 = st.tabs(["Prompt 1 (10s)", "Prompt 2 (Extend)"])
                t1.code(item['p1'])
                t2.code(item['p2'])
            st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown("<p style='text-align:center; color:#666; font-size:0.85rem;'>GROK APEX ULTIMATE • Batch + History + Animation • Powered by Gemini + yt-dlp + FFmpeg</p>", unsafe_allow_html=True)
