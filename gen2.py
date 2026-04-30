import streamlit as st
import google.generativeai as genai
import yt_dlp
import time
import os
import re
import subprocess
from datetime import datetime

# ==================== PAGE CONFIG ====================
st.set_page_config(page_title="GROK APEX CHOICE", page_icon="⚡", layout="wide")

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
    font-size: 2.8rem;
    font-weight: 900;
    background: linear-gradient(90deg, #FFD700, #FF4B4B);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 5px;
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

.history-item {
    background: #1a1a2e;
    border-radius: 12px;
    padding: 10px 15px;
    margin: 8px 0;
    border-left: 4px solid #FFD700;
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
</style>
""", unsafe_allow_html=True)

# ==================== SESSION STATE ====================
if 'all_prompts' not in st.session_state: st.session_state.all_prompts = []
if 'api_keys' not in st.session_state: st.session_state.api_keys = ["", "", ""]
if 'api_saved' not in st.session_state: st.session_state.api_saved = False
if 'reference_videos' not in st.session_state: st.session_state.reference_videos = []
if 'link_history' not in st.session_state: st.session_state.link_history = []
if 'dance_names' not in st.session_state: st.session_state.dance_names = {}

# ==================== ADVANCED DOWNLOAD ====================
def advanced_download(url: str):
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    temp_path = "downloads/temp_raw.mp4"
    final_path = "downloads/ready.mp4"

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
st.markdown('<p class="main-header">GROK APEX CHOICE</p>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:#aaa; margin-top:-8px; font-size:1.05rem;">Prompt Choice • API Key Manager • History • Batch Link</p>', unsafe_allow_html=True)

# ==================== API KEY MANAGER ====================
with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 🔑 API KEY MANAGER (Simpan Sekali, Pakai Selamanya)")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.api_keys[0] = st.text_input("API Key 1", value=st.session_state.api_keys[0], type="password", key="key1")
        if st.button("🗑️ Hapus Key 1", key="del_key1"):
            st.session_state.api_keys[0] = ""
            st.rerun()
    with col2:
        st.session_state.api_keys[1] = st.text_input("API Key 2 (Optional)", value=st.session_state.api_keys[1], type="password", key="key2")
        if st.button("🗑️ Hapus Key 2", key="del_key2"):
            st.session_state.api_keys[1] = ""
            st.rerun()
    with col3:
        st.session_state.api_keys[2] = st.text_input("API Key 3 (Optional)", value=st.session_state.api_keys[2], type="password", key="key3")
        if st.button("🗑️ Hapus Key 3", key="del_key3"):
            st.session_state.api_keys[2] = ""
            st.rerun()

    col_save, col_status = st.columns([1, 3])
    with col_save:
        if st.button("💾 SIMPAN API KEYS", type="primary"):
            st.session_state.api_saved = True
            st.success("✅ API Keys berhasil disimpan!")
    with col_status:
        if st.session_state.api_saved:
            active = len([k for k in st.session_state.api_keys if k.strip()])
            st.success(f"✅ {active} API Key tersimpan dan siap digunakan")
        else:
            st.info("⚠️ Klik 'Simpan' setelah memasukkan API Key")

    st.markdown('</div>', unsafe_allow_html=True)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("## 🎛️ MASTER CONTROL")
    style = st.selectbox("🎨 Visual Style", ["Hyper-Realistic", "Cinematic", "TikTok Viral", "Film Look"])
    camera = st.selectbox("📷 Camera Movement", ["Static", "Slow Zoom In", "Gentle Pan", "Handheld"])
    language = st.radio("🌍 Language", ["English", "Bahasa Indonesia"])

    st.markdown("---")
    st.markdown("## 📜 LINK HISTORY")

    if st.session_state.link_history:
        for i, item in enumerate(reversed(st.session_state.link_history[-8:])):
            with st.container():
                st.markdown(f'<div class="history-item">', unsafe_allow_html=True)
                st.caption(f"🕒 {item['time']}")
                st.write(f"🎵 **{item['song']}**")
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("🔄 Pakai", key=f"use_h_{i}"):
                        st.session_state.reference_videos.append({
                            "name": item['song'],
                            "bytes": item['bytes'],
                            "filename": item['filename'],
                            "source": "history"
                        })
                        st.session_state.dance_names[item['song']] = item['song']
                        st.rerun()
                with col_b:
                    if st.button("🗑️", key=f"del_h_{i}"):
                        st.session_state.link_history.remove(item)
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Belum ada history")

# ==================== 🚀 BATCH INSTANT LINK ====================
st.markdown("### 🚀 BATCH INSTANT LINK")

with st.container():
    st.markdown('<div class="instant-box">', unsafe_allow_html=True)
    st.markdown("**Paste banyak link (satu per baris) → Otomatis masuk ke Ready to Generate + History**")

    links_text = st.text_area("🔗 Paste Links (satu per baris)", height=100, placeholder="https://www.tiktok.com/@user/video/111\nhttps://www.tiktok.com/@user/video/222")

    if st.button("🚀 PROCESS ALL LINKS", key="batch_btn"):
        if links_text.strip():
            links = [line.strip() for line in links_text.strip().split('\n') if line.strip()]
            progress = st.progress(0)
            status = st.empty()
            success = 0

            for i, link in enumerate(links):
                progress.progress(int(((i+1)/len(links))*100))
                status.text(f"⏳ Memproses {i+1}/{len(links)}...")

                try:
                    video_bytes, song_name, filename = advanced_download(link)
                    
                    st.session_state.reference_videos.append({
                        "name": song_name,
                        "bytes": video_bytes,
                        "filename": filename,
                        "source": "link"
                    })
                    
                    st.session_state.dance_names[song_name] = song_name
                    
                    st.session_state.link_history.append({
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "song": song_name,
                        "bytes": video_bytes,
                        "filename": filename,
                        "link": link
                    })
                    success += 1
                except Exception as e:
                    st.error(f"Gagal link {i+1}: {e}")

            progress.progress(100)
            status.success(f"✅ {success}/{len(links)} video berhasil!")
            time.sleep(1)
            st.rerun()
        else:
            st.warning("Link kosong!")

    st.markdown('</div>', unsafe_allow_html=True)

# ==================== 📋 READY TO GENERATE ====================
st.markdown("### 📋 READY TO GENERATE")

with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    if st.session_state.reference_videos:
        st.markdown(f"**Total: {len(st.session_state.reference_videos)} video**")
        
        for i, vid in enumerate(st.session_state.reference_videos):
            col1, col2, col3 = st.columns([4, 1.5, 0.5])
            with col1:
                st.video(vid["bytes"])
                st.caption(f"🎵 {vid['name']}")
            with col2:
                if st.button("🗑️ Hapus", key=f"del_r_{i}"):
                    st.session_state.reference_videos.pop(i)
                    st.rerun()
            with col3:
                st.write("")
    else:
        st.info("Belum ada video siap.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== 📤 MANUAL UPLOAD ====================
st.markdown("### 📤 MANUAL UPLOAD")

with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload Video Manual", type=["mp4", "mov"], accept_multiple_files=True)

    if uploaded:
        for i, file in enumerate(uploaded):
            col1, col2 = st.columns([1, 3])
            with col1:
                st.video(file)
            with col2:
                st.caption(file.name)
                if st.button(f"🔧 Fix + Tambah", key=f"fix_{i}"):
                    with st.spinner("Processing..."):
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
                            st.session_state.dance_names[song_name] = song_name
                            st.success("✅ Ditambahkan!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal: {e}")
                        finally:
                            if os.path.exists(temp_in): os.remove(temp_in)
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== 🔥 GENERATE ====================
if st.button("🔥 GENERATE OFFICIAL PROMPT", disabled=not st.session_state.api_saved or len(st.session_state.reference_videos) == 0):
    st.session_state.all_prompts = []
    
    active_keys = [k for k in st.session_state.api_keys if k.strip().startswith("AIza")]
    if not active_keys:
        st.error("Minimal 1 API Key diperlukan!")
        st.stop()

    videos = st.session_state.reference_videos.copy()
    num_keys = len(active_keys)
    chunks = [videos[i::num_keys] for i in range(num_keys)]

    for key_idx, key in enumerate(active_keys):
        if key_idx >= len(chunks) or not chunks[key_idx]:
            continue

        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        for video in chunks[key_idx]:
            name = video["name"]
            song = st.session_state.dance_names.get(name, name)

            with st.status(f"Analyzing {name} (Key {key_idx+1})...") as status:
                try:
                    temp_path = f"temp_{name.replace(' ', '_')}.mp4"
                    with open(temp_path, "wb") as f: f.write(video["bytes"])

                    vf = genai.upload_file(path=temp_path)
                    while vf.state.name == "PROCESSING":
                        time.sleep(2)
                        vf = genai.get_file(vf.name)

                    analysis_prompt = f"Analyze this dance video. Trend/Song: {song}. Provide detailed 1-second skeletal motion breakdown. Separate Part 1 and Part 2 with '---SEPARATOR---'."
                    response = model.generate_content([vf, analysis_prompt])
                    raw = response.text

                    part1 = raw.split("---SEPARATOR---")[0].strip() if "---SEPARATOR---" in raw else raw
                    part2 = raw.split("---SEPARATOR---")[1].strip() if "---SEPARATOR---" in raw else "continuing smoothly"

                    p1 = f"""Cinematic 10-second video.
[SUBJECT] Young woman dancing '{song}' in exact same outfit and location from reference.
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
                        "video": video["bytes"],
                        "song": song
                    })

                    os.remove(temp_path)
                    genai.delete_file(vf.name)
                    status.update(label=f"✅ Done: {name}", state="complete")

                except Exception as e:
                    st.error(f"Error analyzing {name}: {e}")

# ==================== RESULTS + PILIHAN PROMPT ====================
if st.session_state.all_prompts:
    st.markdown("### 📜 FINAL PROMPTS (Pilih Versi yang Kamu Suka)")

    for i, item in enumerate(st.session_state.all_prompts):
        with st.container():
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader(f"🎥 {item['name']}")

            # PILIHAN PROMPT
            prompt_choice = st.radio(
                "Pilih Versi Prompt:",
                ["Original (Detail)", "Image-to-Video Optimized (Pendek & Sinematik)"],
                key=f"choice_{i}",
                horizontal=True
            )

            c1, c2 = st.columns([1, 2])
            with c1:
                st.video(item['video'])
            with c2:
                if prompt_choice == "Original (Detail)":
                    t1, t2 = st.tabs(["Prompt 1 (10s)", "Prompt 2 (Extend)"])
                    t1.code(item['p1'])
                    t2.code(item['p2'])
                else:
                    # Versi Optimized untuk Image-to-Video
                    optimized = f"""Cinematic 10-second video of a young woman dancing '{item.get('song', item['name'])}' in the exact same outfit and location as the reference image.

Camera: {camera}. Smooth and natural movement with realistic physics. Highly detailed, filmic color grade, natural lighting.

Strict visual consistency with the reference image. No morphing.

{item['p1'][:450]}..."""

                    st.code(optimized)
                    if st.button(f"📋 Copy Optimized Prompt", key=f"copy_opt_{i}"):
                        st.toast("✅ Prompt berhasil disalin!")

            st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown("<p style='text-align:center; color:#666; font-size:0.85rem;'>GROK APEX CHOICE • Prompt Choice + API Key Manager • Powered by Gemini + yt-dlp + FFmpeg</p>", unsafe_allow_html=True)
