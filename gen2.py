import streamlit as st
import google.generativeai as genai
import yt_dlp
import time
import os
import re
import subprocess
import json
from datetime import datetime

# ==================== NEW LIBS FOR PRO TOOLS ====================
import cv2
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import numpy as np
from io import BytesIO
import tempfile

# ==================== PAGE CONFIG ====================
st.set_page_config(page_title="GROK APEX V5", page_icon="⚡", layout="wide")

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

# ==================== LOAD API KEYS FROM FILE ====================
def load_api_keys():
    try:
        if os.path.exists("api_keys.json"):
            with open("api_keys.json", "r") as f:
                return json.load(f)
    except:
        pass
    return ["", "", ""]

def save_api_keys(keys):
    try:
        with open("api_keys.json", "w") as f:
            json.dump(keys, f)
        return True
    except:
        return False

# ==================== SESSION STATE ====================
if 'all_prompts' not in st.session_state: st.session_state.all_prompts = []
if 'api_keys' not in st.session_state: st.session_state.api_keys = load_api_keys()
if 'api_saved' not in st.session_state: st.session_state.api_saved = any(st.session_state.api_keys)
if 'reference_videos' not in st.session_state: st.session_state.reference_videos = []
if 'link_history' not in st.session_state: st.session_state.link_history = []
if 'dance_names' not in st.session_state: st.session_state.dance_names = {}
if 'captions' not in st.session_state: st.session_state.captions = {}

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

# ==================== 🛠️ PRO TOOLS HELPER FUNCTIONS ====================
def get_gemini_model():
    """Get Gemini model with automatic API key rotation on rate limit"""
    if 'current_key_index' not in st.session_state:
        st.session_state.current_key_index = 0
    
    active_keys = [k for k in st.session_state.api_keys if k.strip().startswith("AIza")]
    
    if not active_keys:
        st.error("❌ Tidak ada API Key yang valid! Masukkan minimal 1 API Key.")
        st.stop()
    
    # Try to get or create model
    if 'model' not in st.session_state or st.session_state.model is None:
        try:
            current_key = active_keys[st.session_state.current_key_index % len(active_keys)]
            genai.configure(api_key=current_key)
            st.session_state.model = genai.GenerativeModel("gemini-2.5-flash")
            st.session_state.current_key = current_key[:10] + "..."  # For display
        except Exception as e:
            st.error(f"❌ Gagal menginisialisasi API Key: {e}")
            st.stop()
    
    return st.session_state.model

def rotate_api_key():
    """Rotate to next API key when rate limited"""
    active_keys = [k for k in st.session_state.api_keys if k.strip().startswith("AIza")]
    if len(active_keys) <= 1:
        st.warning("⚠️ Hanya ada 1 API Key. Tidak bisa rotate.")
        return False
    
    st.session_state.current_key_index = (st.session_state.current_key_index + 1) % len(active_keys)
    st.session_state.model = None  # Force re-initialization
    
    new_key = active_keys[st.session_state.current_key_index]
    genai.configure(api_key=new_key)
    st.session_state.model = genai.GenerativeModel("gemini-2.5-flash")
    st.session_state.current_key = new_key[:10] + "..."
    
    st.toast(f"🔄 Beralih ke API Key #{st.session_state.current_key_index + 1}")
    return True

def safe_generate_content(prompt_or_contents, max_retries=3):
    """Safely call Gemini with automatic key rotation on rate limit"""
    for attempt in range(max_retries):
        try:
            model = get_gemini_model()
            return model.generate_content(prompt_or_contents)
        except Exception as e:
            error_msg = str(e).lower()
            if "quota" in error_msg or "rate" in error_msg or "limit" in error_msg or "429" in error_msg:
                if rotate_api_key():
                    st.info(f"🔄 Rate limit terdeteksi. Mencoba API Key berikutnya... (Percobaan {attempt+1})")
                    time.sleep(1)
                    continue
                else:
                    st.error("❌ Semua API Key sudah limit. Tunggu beberapa menit lalu coba lagi.")
                    st.stop()
            else:
                # Other error, raise it
                raise e
    st.error("❌ Gagal setelah beberapa kali mencoba.")
    st.stop()

def get_video_metadata(video_bytes: bytes):
    """Get detailed video info using OpenCV"""
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(video_bytes)
            tmp_path = tmp.name
        
        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            return {"error": "Cannot open video"}
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        os.unlink(tmp_path)
        
        return {
            "duration": round(duration, 2),
            "fps": round(fps, 2),
            "resolution": f"{width}x{height}",
            "frame_count": frame_count,
            "aspect_ratio": round(width/height, 2) if height > 0 else 0
        }
    except Exception as e:
        return {"error": str(e)}

def extract_keyframes(video_bytes: bytes, num_frames: int = 4):
    """Extract evenly spaced keyframes using OpenCV"""
    frames = []
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(video_bytes)
            tmp_path = tmp.name
        
        cap = cv2.VideoCapture(tmp_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if total_frames < 2:
            cap.release()
            os.unlink(tmp_path)
            return frames
        
        indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
        
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)
                pil_img.thumbnail((400, 400))
                frames.append(pil_img)
        
        cap.release()
        os.unlink(tmp_path)
    except Exception as e:
        st.error(f"Keyframe extraction error: {e}")
    
    return frames

def extract_best_starting_frame(video_bytes: bytes):
    """Extract the most representative starting frame (usually frame 3-5 for dance videos)"""
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(video_bytes)
            tmp_path = tmp.name
        
        cap = cv2.VideoCapture(tmp_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # For dance videos, frame 3-6 usually has the best "ready pose"
        best_idx = min(5, total_frames - 1)
        cap.set(cv2.CAP_PROP_POS_FRAMES, best_idx)
        ret, frame = cap.read()
        
        cap.release()
        os.unlink(tmp_path)
        
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            # Convert to bytes for Gemini upload
            img_bytes = BytesIO()
            pil_img.save(img_bytes, format="JPEG", quality=92)
            return img_bytes.getvalue(), pil_img
        return None, None
    except Exception as e:
        st.error(f"Best frame extraction error: {e}")
        return None, None

def generate_dance_negative_prompt(high_accuracy: bool = False):
    """Generate aggressive negative prompt specifically for dance videos"""
    base = "3d render, cartoonish, plastic skin, deformed hands, deformed fingers, extra fingers, missing fingers, blurry face, text, watermark, logo, low quality, worst quality, normal quality, jpeg artifacts, signature, username, error, cropped, out of frame, poorly drawn face, mutation, bad anatomy, bad proportions, extra limbs, cloned face, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck, username, watermark, signature"
    
    if high_accuracy:
        dance_specific = (
            ", robotic movement, stiff joints, jerky motion, floating limbs, hair not moving naturally, "
            "clothes morphing, outfit changing, face changing between frames, inconsistent face, "
            "waxy skin, shiny plastic skin, no skin pores, flat lighting, overexposed, underexposed, "
            "motion blur on face, ghosting, double exposure, bad hand anatomy, broken fingers, "
            "unnatural weight distribution, floating feet, bad grounding, no contact with floor, "
            "hair clipping through body, clothes clipping, inconsistent lighting, face morphing, "
            "sudden pose change, teleporting, bad timing with music, off-beat movement"
        )
        return base + dance_specific
    else:
        return base

def create_styled_thumbnail(video_bytes: bytes, song_name: str, style: str = "cinematic"):
    """Create a beautiful thumbnail using Pillow"""
    try:
        frames = extract_keyframes(video_bytes, 1)
        if not frames:
            return None
        
        base_img = frames[0].convert("RGBA")
        
        width, height = 720, 1280
        thumb = Image.new("RGBA", (width, height), (5, 5, 5, 255))
        
        bg = base_img.resize((width, height), Image.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(radius=8))
        thumb.paste(bg, (0, 0))
        
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 120))
        thumb = Image.alpha_composite(thumb, overlay)
        
        draw = ImageDraw.Draw(thumb)
        draw.rectangle([0, 0, width, 8], fill=(255, 215, 0, 255))
        
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        title = song_name[:30] + "..." if len(song_name) > 30 else song_name
        bbox = draw.textbbox((0, 0), title, font=title_font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        draw.text((x, 180), title, font=title_font, fill=(255, 215, 0, 255))
        
        draw.text((width//2 - 120, 250), "⚡ GROK APEX V5", font=subtitle_font, fill=(255, 255, 255, 230))
        draw.text((width//2 - 140, 290), "OFFICIAL DANCE PROMPT", font=small_font, fill=(200, 200, 200, 200))
        
        draw.rectangle([0, height-100, width, height], fill=(0, 0, 0, 180))
        draw.text((40, height-80), "Ready for Kling / Runway / Luma", font=small_font, fill=(255, 215, 0, 255))
        
        output = BytesIO()
        thumb_rgb = thumb.convert("RGB")
        thumb_rgb.save(output, format="PNG")
        return output.getvalue()
    
    except Exception as e:
        st.error(f"Thumbnail error: {e}")
        return None

def create_captioned_tiktok_video(video_bytes: bytes, caption: str, song_name: str, duration_sec: float = 12.0):
    """Create TikTok-style video with caption overlay using MoviePy + Pillow"""
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_in:
            tmp_in.write(video_bytes)
            input_path = tmp_in.name
        
        clip = VideoFileClip(input_path)
        
        if clip.duration > duration_sec:
            clip = clip.subclip(0, duration_sec)
        
        def make_text_frame(t):
            bar_height = 160
            bar = Image.new("RGBA", (clip.w, bar_height), (0, 0, 0, 200))
            draw = ImageDraw.Draw(bar)
            
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
            except:
                font = ImageFont.load_default()
            
            max_width = clip.w - 80
            words = caption.split()
            lines = []
            current_line = ""
            for word in words:
                test_line = current_line + " " + word if current_line else word
                bbox = draw.textbbox((0, 0), test_line, font=font)
                if bbox[2] - bbox[0] <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            
            y_offset = 25
            for line in lines[:4]:
                draw.text((42, y_offset + 2), line, font=font, fill=(0, 0, 0, 255))
                draw.text((40, y_offset), line, font=font, fill=(255, 215, 0, 255))
                y_offset += 38
            
            return np.array(bar.convert("RGB"))
        
        txt_clip = TextClip(make_text_frame, duration=clip.duration, size=(clip.w, 160))
        txt_clip = txt_clip.set_position(("center", "bottom"))
        
        final = CompositeVideoClip([clip, txt_clip])
        final = final.set_duration(clip.duration)
        
        output_path = f"downloads/captioned_{song_name[:20].replace(' ', '_')}.mp4"
        os.makedirs("downloads", exist_ok=True)
        
        final.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            preset="fast",
            threads=2,
            logger=None
        )
        
        clip.close()
        final.close()
        
        with open(output_path, "rb") as f:
            result_bytes = f.read()
        
        os.unlink(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)
        
        return result_bytes, output_path.split("/")[-1]
    
    except Exception as e:
        st.error(f"Caption video error: {e}")
        return None, None

# ==================== HEADER ====================
st.markdown('<p class="main-header">GROK APEX V5</p>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:#aaa; margin-top:-8px; font-size:1.05rem;">API Key Saved • Upload Manual (No FFmpeg) • Music Control • Auto Caption • Optimized for Grok AI Image-to-Video</p>', unsafe_allow_html=True)

# ==================== API KEY MANAGER (LOCAL STORAGE) ====================
with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 🔑 API KEY MANAGER (Tersimpan Permanen)")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.api_keys[0] = st.text_input("API Key 1", value=st.session_state.api_keys[0], type="password", key="key1")
        if st.button("🗑️ Hapus Key 1", key="del_key1"):
            st.session_state.api_keys[0] = ""
            save_api_keys(st.session_state.api_keys)
            st.rerun()
    with col2:
        st.session_state.api_keys[1] = st.text_input("API Key 2 (Optional)", value=st.session_state.api_keys[1], type="password", key="key2")
        if st.button("🗑️ Hapus Key 2", key="del_key2"):
            st.session_state.api_keys[1] = ""
            save_api_keys(st.session_state.api_keys)
            st.rerun()
    with col3:
        st.session_state.api_keys[2] = st.text_input("API Key 3 (Optional)", value=st.session_state.api_keys[2], type="password", key="key3")
        if st.button("🗑️ Hapus Key 3", key="del_key3"):
            st.session_state.api_keys[2] = ""
            save_api_keys(st.session_state.api_keys)
            st.rerun()

    col_save, col_status = st.columns([1, 3])
    with col_save:
        if st.button("💾 SIMPAN API KEYS", type="primary"):
            if save_api_keys(st.session_state.api_keys):
                st.session_state.api_saved = True
                st.success("✅ API Keys berhasil disimpan permanen!")
            else:
                st.error("❌ Gagal menyimpan API Keys")
    with col_status:
        if st.session_state.api_saved:
            active = len([k for k in st.session_state.api_keys if k.strip()])
            st.success(f"✅ {active} API Key tersimpan permanen")
        else:
            st.info("⚠️ Klik 'Simpan' setelah memasukkan API Key")

    st.markdown('</div>', unsafe_allow_html=True)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("## 🎛️ MASTER CONTROL")
    
    style = st.selectbox("🎨 Visual Style", ["Hyper-Realistic", "Cinematic", "TikTok Viral", "Film Look"])
    camera = st.selectbox("📷 Camera Movement", [
        "Static", "Slow Zoom In", "Gentle Pan", "Handheld",
        "Speed Ramp (Fast → Slow)", "Arc Shot (Melingkar)", "Dolly In", "Truck Left/Right",
        "Crane Up", "Orbit Shot", "Push In", "Pull Out"
    ])
    language = st.radio("🌍 Language", ["English", "Bahasa Indonesia"])

    st.markdown("---")
    
    # === MUSIC CONTROL ===
    st.markdown("### 🎵 Music Control")
    manual_music = st.text_input("Nama Lagu / Musik (Manual)", placeholder="Kosongkan jika ingin otomatis")
    st.caption("Jika diisi manual, akan menggantikan deteksi otomatis")

    st.markdown("---")
    
    # === HUMAN QUIRKS ===
    st.markdown("### 👤 Human Quirks & Mannerisms")
    mannerisms = st.multiselect(
        "Pilih Gerakan Manusiawi:",
        ["Natural Blinking", "Fixing Hair", "Adjusting Clothes", "Rhythmic Breathing", "Joyful Laugh", "Playful Wink"],
        default=["Natural Blinking"]
    )

    st.markdown("---")
    
    # === PROFESSIONAL COLOR GRADING ===
    st.markdown("### 🎨 Professional Color Grading (LUTs)")
    color_grade = st.selectbox(
        "Pilih LUT:",
        ["None", "Kodak Portra 400", "FujiFilm Look", "Teal & Orange", "Cinematic", "Vintage Film"]
    )

    st.markdown("---")
    
    # === LIGHTING STYLE ===
    st.markdown("### 💡 Lighting Style")
    lighting = st.selectbox(
        "Pilih Pencahayaan:",
        ["Three-Point Lighting", "Rim Lighting", "Dynamic Studio", "Golden Hour", "Neon Cyberpunk", "Moody Atmosphere"]
    )

    st.markdown("---")
    
    # === VFX & PARTICLES ===
    st.markdown("### ✨ VFX & Particles")
    vfx = st.selectbox(
        "Pilih Efek Visual:",
        ["None", "Cinematic Dust", "Falling Petals", "Golden Sparkles", "Neon Particles", "Light Rays"]
    )

    st.markdown("---")
    
    # === WIND & HAIR FLOW ===
    st.markdown("### 🌬️ Wind & Hair Flow")
    wind = st.selectbox(
        "Kekuatan Angin:",
        ["None", "Breeze (Angin Sepoi)", "Windy (Berangin)", "Stormy (Badai)"]
    )

    st.markdown("---")
    
    # === SHOT SEQUENCING ===
    st.markdown("### 🎬 Shot Sequencing")
    multi_angle = st.checkbox("Enable Multi-Angle (Wide → Close-up)", value=False)

    st.markdown("---")
    
    # === GROK HIGH ACCURACY MODE (NEW) ===
    st.markdown("### 🎯 Grok High Accuracy Mode")
    grok_high_accuracy = st.checkbox(
        "Enable Grok High Accuracy Mode (Stronger First Frame Lock + Physics)",
        value=True,
        help="Aktifkan untuk akurasi maksimal di Grok AI. Prompt akan lebih panjang tapi hasil lebih dekat dengan referensi."
    )

    st.markdown("---")
    
    # === NEGATIVE PROMPT ===
    st.markdown("### 🚫 Negative Prompt (Anti-Glitch)")
    negative_prompt = st.text_area(
        "Kata yang DILARANG:",
        value="3d render, cartoonish, plastic skin, deformed hands, blurry face, text, watermark, logo",
        height=60
    )

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
                            "bytes": bytes(item['bytes']) if not isinstance(item['bytes'], bytes) else item['bytes'],
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
st.markdown("### 🚀 BATCH INSTANT LINK (Support Semua Platform)")

with st.container():
    st.markdown('<div class="instant-box">', unsafe_allow_html=True)
    st.markdown("**Support: TikTok HP/Desktop, Instagram HP/Desktop, YouTube, Facebook, Twitter, dll**")

    links_text = st.text_area("🔗 Paste Links (satu per baris)", height=100, placeholder="https://www.tiktok.com/@user/video/111\nhttps://www.instagram.com/reel/xxx\nhttps://youtube.com/shorts/yyy")

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
                # Handle both dict and other types
                if isinstance(vid, dict):
                    video_data = vid["bytes"] if isinstance(vid["bytes"], bytes) else bytes(vid["bytes"])
                    name = vid["name"]
                else:
                    video_data = bytes(vid.getbuffer()) if hasattr(vid, 'getbuffer') else bytes(vid)
                    name = vid.name if hasattr(vid, 'name') else str(vid)
                
                st.video(video_data)
                st.caption(f"🎵 {name}")
            with col2:
                if st.button("🗑️ Hapus", key=f"del_r_{i}"):
                    st.session_state.reference_videos.pop(i)
                    st.rerun()
            with col3:
                st.write("")
    else:
        st.info("Belum ada video siap.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== 📤 MANUAL UPLOAD (TANPA FFMPEG) ====================
st.markdown("### 📤 MANUAL UPLOAD (Tanpa FFmpeg - Langsung Pakai)")

with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.info("⚡ Upload manual tidak melalui ffmpeg. Langsung pakai video apa adanya.")

    uploaded = st.file_uploader("Upload Video Manual (MP4/MOV)", type=["mp4", "mov"], accept_multiple_files=True)

    if uploaded:
        for i, file in enumerate(uploaded):
            col1, col2 = st.columns([1, 3])
            with col1:
                st.video(file)
            with col2:
                st.caption(file.name)
                if st.button(f"✅ Tambah ke Ready", key=f"add_manual_{i}"):
                    st.session_state.reference_videos.append({
                        "name": file.name,
                        "bytes": bytes(file.getbuffer()),  # Fix: convert memoryview to bytes
                        "filename": file.name,
                        "source": "manual"
                    })
                    st.session_state.dance_names[file.name] = file.name
                    st.success("✅ Ditambahkan ke Ready to Generate!")
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== 🔥 GENERATE ====================
if st.button("🔥 GENERATE OFFICIAL PROMPT", disabled=not st.session_state.api_saved or len(st.session_state.reference_videos) == 0):
    st.session_state.all_prompts = []
    st.session_state.captions = []
    
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
            # Convert everything to a safe dict format
            try:
                if isinstance(video, dict):
                    safe_video = video
                elif hasattr(video, '__dict__'):
                    safe_video = video.__dict__
                elif hasattr(video, 'getbuffer'):
                    safe_video = {"name": getattr(video, 'name', 'Unknown'), "bytes": bytes(video.getbuffer())}
                elif isinstance(video, (list, tuple)):
                    if len(video) >= 2:
                        safe_video = {"name": str(video[0]) if video[0] else "Unknown", "bytes": video[1] if len(video) > 1 else b""}
                    else:
                        safe_video = {"name": "Unknown", "bytes": b""}
                else:
                    safe_video = {"name": str(video), "bytes": b""}
                
                name = str(safe_video.get("name", "Unknown"))
                raw_bytes = safe_video.get("bytes", b"")
                video_bytes = raw_bytes if isinstance(raw_bytes, bytes) else bytes(raw_bytes) if raw_bytes else b""
            except Exception as e:
                st.error(f"Error processing video item: {e}")
                continue
            
            song = str(st.session_state.dance_names.get(name, name))

            with st.status(f"Analyzing {name} (Key {key_idx+1})...") as status:
                try:
                    temp_path = f"temp_{name.replace(' ', '_')}.mp4"
                    with open(temp_path, "wb") as f: f.write(video_bytes)

                    vf = genai.upload_file(path=temp_path)
                    while vf.state.name == "PROCESSING":
                        time.sleep(2)
                        vf = genai.get_file(vf.name)

                    # Define vfx_str and wind_str (with fallback)
                    vfx_val = vfx if 'vfx' in dir() else "None"
                    wind_val = wind if 'wind' in dir() else "None"
                    vfx_str = f"{vfx_val} particles in the air" if vfx_val != "None" else "clear atmosphere"
                    wind_str = f"{wind_val} blowing hair and clothes" if wind_val != "None" else "still air"

                    analysis_prompt = f"""You are a world-class motion capture director and AI video prompt engineer. Your job is to analyze ANY dance performance video and create an extremely detailed prompt that will make Kling AI / Runway / Luma generate a video with IDENTICAL realism, timing, energy, and human nuance.

**IMPORTANT:** This reference video can be any style — K-pop, hip-hop, contemporary, traditional, freestyle, sensual, powerful, cute, dark, etc. Adapt your analysis to whatever style and energy is actually in the video. Do NOT force "cute" or specific gestures if they are not present.

**CRITICAL FOCUS AREAS (analyze whatever is relevant to THIS video):**

1. **OVERALL PERFORMANCE IDENTITY**
   - Dance style & genre (K-pop choreo, hip-hop, contemporary, waacking, etc.)
   - Overall energy level (explosive, smooth, sharp, fluid, aggressive, soft)
   - Emotional tone & character personality (confident, playful, intense, seductive, mysterious, joyful, etc.)

2. **FACIAL PERFORMANCE**
   - Facial expression style and changes throughout
   - Eye contact / gaze direction with camera
   - Head movement (speed, angle, isolation)
   - Lip sync quality and mouth shapes
   - Natural micro-expressions and blinking

3. **BODY MECHANICS & WEIGHT**
   - Weight distribution and grounding (how the performer uses the floor)
   - Posture, torso movement, hip isolation, shoulder movement
   - Knee bend, foot placement, balance shifts
   - Full-body coordination and lines

4. **HAND & ARM VOCABULARY**
   - Signature hand shapes and gestures specific to this performance
   - Speed, sharpness, and fluidity of arm movements
   - Finger articulation and wrist action

5. **HAIR, CLOTHING & SECONDARY PHYSICS**
   - How hair moves with the body (bounce, swing, settle)
   - Fabric behavior (stretch, wrinkle, flow) on the specific outfit
   - Skin detail, muscle engagement, natural body physics
   - Any accessories movement (necklace, earrings, etc.)

6. **MUSICALITY & TIMING**
   - Which movements hit the beat vs off-beat
   - Pauses, accents, builds, and releases
   - Breath and tension/release moments

**OUTPUT FORMAT (follow exactly):**

PERFORMANCE IDENTITY:
[Dance style + energy + emotional character in 2-3 sentences]

DETAILED TIMELINE (second-by-second breakdown):
0-1s: [face + eyes + head + torso + arms + hands + weight + hair + fabric]
1-2s: [same level of detail]
... (continue for the full duration of the video)

SIGNATURE MOVEMENT VOCABULARY:
- [List 5-8 most distinctive, repeatable movements or gestures from this specific performance with timing]

PHYSICS & REALISM REQUIREMENTS:
- Hair behavior: ...
- Fabric behavior: ...
- Skin & body physics: ...
- Weight & grounding: ...
- Lighting & surface interaction: ...

---SEPARATOR---
[If the video is longer than 15 seconds, continue the detailed timeline here]"""

                    response = safe_generate_content([vf, analysis_prompt])
                    raw = response.text

                    part1 = raw.split("---SEPARATOR---")[0].strip() if "---SEPARATOR---" in raw else raw
                    part2 = raw.split("---SEPARATOR---")[1].strip() if "---SEPARATOR---" in raw else "continuing smoothly"

                    p1 = f"""HYPER-REALISTIC 10-second dance video. 100% identical performer, face, body, outfit, location, and lighting as the reference video.

[SUBJECT] Exact same person as reference with perfect face lock, skin texture, hair style, and body proportions. Zero deviation in appearance.

[CAMERA] {camera}. Natural, subtle camera movement that feels human (slight breathing, micro-adjustments).

[PERFORMANCE] Replicate the exact dance style, energy, timing, micro-movements, facial expressions, and human nuance described in the analysis below:
{part1}

[PHYSICS] Ultra-realistic secondary motion: hair behaving naturally with every head movement, fabric stretching and wrinkling authentically, skin detail with visible pores and subsurface scattering, natural weight transfer and grounding, no robotic stiffness.

[STYLE] {style}, {lighting}, {color_grade} color grade, cinematic film grain, professional cinema camera look, 8K detail.

[VISUAL LOCK] Strict 1:1 visual consistency with reference video — same face, same clothing, same background, same lighting. No morphing, no drift.

[TECHNICAL] 24fps, perfect temporal consistency, coherent motion, natural physics simulation, zero artifacts."""

                    p2 = f"""Seamless 10-second continuation of the exact same performance. Maintain 100% identical face, body, outfit, lighting, and environment as the first 10 seconds and the reference.

[CONTINUATION] {part2}

[PHYSICS] Continue the same natural hair movement, fabric behavior, skin realism, and weight distribution. Keep consistent energy and personality throughout.

[TECHNICAL] 24fps, zero character drift, perfect motion coherence."""

                    if grok_high_accuracy:
                        auto_negative = generate_dance_negative_prompt(True)
                        p3 = f"""GROK AI HIGH ACCURACY IMAGE-TO-VIDEO PROMPT

CRITICAL INSTRUCTION: Use the reference image as the EXACT pixel-perfect first frame. 
Lock the face, body proportions, hairstyle, outfit, pose, lighting, and background 100% — 
DO NOT change ANYTHING in the first 1.5 seconds. The first frame must be identical to the reference image.

[PERFORMER] Exact same person as the reference image with zero deviation in face, skin texture, hair, body, and clothing.

[PERFORMANCE - HIGH FIDELITY] Replicate this sequence with maximum accuracy:
{part1[:650]}

[PHYSICS - ENHANCED] Ultra-realistic hair strand movement, fabric stretch and wrinkle physics, natural weight transfer and grounding, subtle breathing visible in chest and shoulders, realistic skin detail with pores and subsurface scattering. No robotic stiffness. Every micro-movement must feel human.

[STYLE] {style}, {lighting}, {color_grade} color grade, natural cinematic look, film grain, shot on professional camera.

[TECHNICAL] 24fps, perfect temporal consistency, zero morphing, zero artifacts, maximum realism. Treat the reference image as ground truth for the entire video.

[AVOID] {auto_negative}

Output must look like real footage, not AI-generated."""

                        p4 = f"""GROK AI HIGH ACCURACY EXTENSION PROMPT

Continue seamlessly from the previous clip. Maintain 100% identical face, body, outfit, lighting, and environment as the reference image and the first 10 seconds.

[CONTINUATION - HIGH FIDELITY] {part2[:500]}

[CONSISTENCY RULE] The face, hair, clothing, and lighting must remain pixel-perfect consistent with the reference image throughout. Same hair physics, fabric behavior, skin detail, and natural movement. No drift allowed.

{color_grade} color grade, ultra-realistic physics, maximum consistency."""
                    else:
                        p3 = f"""GROK AI IMAGE-TO-VIDEO PROMPT (Optimized for maximum accuracy)

Use the provided reference image as the EXACT first frame. Lock the face, body, outfit, hairstyle, lighting, and background 100% — do not change anything in the first 1 second.

The video must feel like a seamless continuation of this exact moment:

[PERFORMER] Exact same young woman as in the reference image, same face, same body, same white outfit, same location, same lighting.

[PERFORMANCE] Replicate this exact sequence with maximum fidelity:
{part1[:600]}

[STYLE] {style} visual style, {lighting}, {color_grade} color grade, natural film look, highly detailed skin with visible pores and realistic subsurface scattering.

[PHYSICS] Natural hair movement, fabric wrinkles and stretch, realistic weight shifts, subtle breathing, no robotic motion.

[TECHNICAL] 24fps, smooth motion, perfect temporal consistency, zero morphing, zero artifacts, maximum realism.

Make it look like real footage shot on a professional camera, not AI generated."""

                        p4 = f"""GROK AI IMAGE-TO-VIDEO EXTENSION PROMPT

Continue seamlessly from the previous clip. Keep the exact same face, body, outfit, lighting, and environment as the reference image and the first 10 seconds.

[CONTINUATION] {part2[:450]}

Maintain 100% visual consistency with the starting reference image. Same hair physics, fabric behavior, skin detail, and natural movement. {color_grade} color grade, realistic physics, no drift in character appearance."""

                    # Auto Caption
                    caption_prompt = f"Buatkan caption viral TikTok + 5 hashtag untuk video tari dengan lagu '{song}'. Buat dalam bahasa Indonesia, singkat, dan menarik."
                    caption_response = safe_generate_content(caption_prompt)
                    caption = caption_response.text

                    st.session_state.all_prompts.append({
                        "name": name,
                        "song": song,
                        "p1": p1,
                        "p2": p2,
                        "p3": p3,
                        "p4": p4,
                        "video": video_bytes
                    })

                    st.session_state.captions[name] = caption

                    os.remove(temp_path)
                    genai.delete_file(vf.name)
                    status.update(label=f"✅ Done: {name}", state="complete")

                except Exception as e:
                    st.error(f"Error analyzing {name}: {e}")

# ==================== RESULTS + PILIHAN PROMPT ====================
if st.session_state.all_prompts:
    st.markdown("### 📜 FINAL PROMPTS (Pilih Versi yang Kamu Suka)")

    if st.button("🗑️ CLEAR ALL CONTENT", type="secondary"):
        st.session_state.all_prompts = []
        st.session_state.captions = []
        st.rerun()

    for i, item in enumerate(st.session_state.all_prompts):
        with st.container():
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader(f"🎥 {item['name']}")

            prompt_choice = st.radio(
                "Pilih Versi Prompt:",
                [
                    "Original (Detail)",
                    "Image-to-Video Optimized (Main)",
                    "Image-to-Video Optimized (Extend)"
                ],
                key=f"choice_{i}",
                horizontal=True
            )

            c1, c2 = st.columns([1, 2])
            with c1:
                # Fix: ensure bytes type for st.video
                video_data = item['video'] if isinstance(item['video'], bytes) else bytes(item['video'])
                st.video(video_data)
            with c2:
                if prompt_choice == "Original (Detail)":
                    t1, t2 = st.tabs(["Prompt 1 (10s)", "Prompt 2 (Extend)"])
                    t1.code(item['p1'])
                    t2.code(item['p2'])
                elif prompt_choice == "Image-to-Video Optimized (Main)":
                    st.code(item['p3'])
                    if st.button(f"📋 Copy Main Optimized", key=f"copy_main_{i}"):
                        st.toast("✅ Prompt berhasil disalin!")
                else:
                    st.code(item['p4'])
                    if st.button(f"📋 Copy Extend Optimized", key=f"copy_extend_{i}"):
                        st.toast("✅ Prompt berhasil disalin!")

            if item['name'] in st.session_state.captions:
                st.markdown("**📱 Auto TikTok Caption + Hashtag:**")
                st.code(st.session_state.captions[item['name']])
                if st.button(f"📋 Copy Caption", key=f"copy_cap_{i}"):
                    st.toast("✅ Caption berhasil disalin!")

            # Show aggressive negative prompt when High Accuracy was used
            if grok_high_accuracy:
                auto_neg = generate_dance_negative_prompt(True)
                st.markdown("**🚫 Auto Negative Prompt (Dance Optimized):**")
                st.code(auto_neg[:300] + "...")
                if st.button(f"📋 Copy Negative Prompt", key=f"copy_neg_{i}"):
                    st.toast("✅ Negative Prompt berhasil disalin!")

            st.markdown('</div>', unsafe_allow_html=True)

# ==================== 🛠️ PRO TOOLS - OpenCV + MoviePy + Pillow ====================
st.markdown("---")
st.markdown("### 🛠️ PRO TOOLS (OpenCV • MoviePy • Pillow)")

with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.info("✨ Fitur tambahan untuk analisis video, thumbnail profesional, dan preview caption TikTok tanpa mengubah workflow utama.")

    tool = st.selectbox(
        "Pilih Tool:",
        ["📊 Video Metadata & Keyframes", "🖼️ Create Styled Thumbnail", "🎬 TikTok Caption Video Maker"],
        key="pro_tool"
    )

    if not st.session_state.reference_videos:
        st.warning("⚠️ Tambahkan video dulu di 'READY TO GENERATE' atau Manual Upload")
    else:
        video_names = [v["name"] if isinstance(v, dict) else getattr(v, 'name', str(v)) for v in st.session_state.reference_videos]
        selected_idx = st.selectbox("Pilih Video Referensi:", range(len(video_names)), format_func=lambda i: video_names[i], key="pro_video_select")
        
        selected_video = st.session_state.reference_videos[selected_idx]
        if isinstance(selected_video, dict):
            vid_bytes = selected_video["bytes"] if isinstance(selected_video["bytes"], bytes) else bytes(selected_video["bytes"])
            vid_name = selected_video["name"]
        else:
            vid_bytes = bytes(selected_video.getbuffer()) if hasattr(selected_video, 'getbuffer') else bytes(selected_video)
            vid_name = getattr(selected_video, 'name', 'video')

        if tool == "📊 Video Metadata & Keyframes":
            if st.button("🔍 ANALYZE VIDEO", key="analyze_btn"):
                with st.spinner("Menganalisis video..."):
                    meta = get_video_metadata(vid_bytes)
                    if "error" not in meta:
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("⏱️ Durasi", f"{meta['duration']}s")
                        col2.metric("🎞️ FPS", meta['fps'])
                        col3.metric("📐 Resolusi", meta['resolution'])
                        col4.metric("📏 Aspect", meta['aspect_ratio'])
                        
                        st.success("✅ Metadata berhasil diambil!")
                    else:
                        st.error(meta["error"])
                
                st.markdown("**🖼️ Keyframes (4 posisi penting):**")
                frames = extract_keyframes(vid_bytes, 4)
                if frames:
                    cols = st.columns(4)
                    for i, frame in enumerate(frames):
                        with cols[i]:
                            st.image(frame, caption=f"Frame {i+1}", use_column_width=True)
                else:
                    st.warning("Gagal extract keyframes")

        elif tool == "🖼️ Create Styled Thumbnail":
            if st.button("🎨 GENERATE THUMBNAIL", key="thumb_btn"):
                with st.spinner("Membuat thumbnail profesional..."):
                    thumb_bytes = create_styled_thumbnail(vid_bytes, vid_name)
                    if thumb_bytes:
                        st.image(thumb_bytes, caption="Styled Thumbnail (720x1280)", use_column_width=True)
                        st.download_button(
                            "📥 Download Thumbnail PNG",
                            data=thumb_bytes,
                            file_name=f"thumbnail_{vid_name[:20]}.png",
                            mime="image/png"
                        )
                    else:
                        st.error("Gagal membuat thumbnail")

        elif tool == "🎬 TikTok Caption Video Maker":
            caption_text = st.session_state.captions.get(vid_name, "")
            if not caption_text:
                caption_text = st.text_area("Masukkan Caption Manual (karena belum ada dari Gemini):", 
                                            value="Viral dance challenge! 🔥 #fyp #dance", height=80)
            
            st.caption(f"Caption yang akan dipakai: {caption_text[:80]}...")
            
            if st.button("🎥 CREATE CAPTIONED PREVIEW (12s)", key="capvid_btn"):
                with st.spinner("Rendering video dengan caption overlay... (mungkin 20-40 detik)"):
                    result_bytes, filename = create_captioned_tiktok_video(vid_bytes, caption_text, vid_name)
                    if result_bytes:
                        st.success("✅ Video dengan caption berhasil dibuat!")
                        st.video(result_bytes)
                        st.download_button(
                            "📥 Download Captioned Video",
                            data=result_bytes,
                            file_name=filename,
                            mime="video/mp4"
                        )
                    else:
                        st.error("Gagal membuat video. Coba video yang lebih pendek atau cek ffmpeg.")

    st.markdown('</div>', unsafe_allow_html=True)

# ==================== 🚀 EPIC AI FEATURES ====================
st.markdown("---")
st.markdown("### 🚀 EPIC AI FEATURES (New & Powerful)")

with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.info("🔥 6 Fitur baru yang bikin prompt kamu jauh lebih powerful untuk Grok AI!")

    epic_tab = st.tabs([
        "🚀 Master Prompt",
        "🧠 Smart Refiner", 
        "📊 Quality Score",
        "🎵 Beat Sync",
        "🔥 Heatmap",
        "🌀 Multi Fusion"
    ])

    # === TAB 1: One-Click Grok Master Prompt ===
    with epic_tab[0]:
        st.markdown("**🚀 One-Click Grok Master Prompt**")
        st.caption("Langsung generate prompt versi paling optimal untuk Grok AI (menggabungkan semua teknik terbaik)")
        
        if st.button("🚀 GENERATE MASTER PROMPT", key="master_btn", type="primary"):
            if not st.session_state.reference_videos:
                st.warning("Tambahkan minimal 1 video dulu!")
            else:
                with st.spinner("Membuat Master Prompt terbaik untuk Grok AI..."):
                    # Use the first video
                    vid = st.session_state.reference_videos[0]
                    if isinstance(vid, dict):
                        vid_bytes = vid["bytes"] if isinstance(vid["bytes"], bytes) else bytes(vid["bytes"])
                        vid_name = vid["name"]
                    else:
                        vid_bytes = bytes(vid.getbuffer()) if hasattr(vid, 'getbuffer') else bytes(vid)
                        vid_name = getattr(vid, 'name', 'video')
                    
                    # Generate strong analysis
                    temp_path = f"temp_master_{vid_name.replace(' ', '_')}.mp4"
                    with open(temp_path, "wb") as f: f.write(vid_bytes)
                    
                    vf = genai.upload_file(path=temp_path)
                    while vf.state.name == "PROCESSING":
                        time.sleep(1)
                        vf = genai.get_file(vf.name)
                    
                    master_analysis = f"""Create the most powerful prompt possible for Grok AI Image-to-Video.
Focus on: Perfect First Frame Lock, Ultra-realistic physics, Exact timing, Maximum human nuance.
Video: {vid_name}"""
                    
                    # Generate Main Prompt (first 10 seconds)
                    main_analysis = f"""Create a powerful 10-second Grok AI Image-to-Video prompt for the first part of the dance.
Focus on: Perfect First Frame Lock, Ultra-realistic physics, Exact timing for the first 10 seconds, Maximum human nuance.
Video: {vid_name}"""
                    main_response = safe_generate_content([vf, main_analysis])
                    
                    # Generate Extend Prompt (continuation)
                    extend_analysis = f"""Create a seamless 10-second continuation prompt for Grok AI Image-to-Video that continues the exact same performance from the first 10 seconds.
Maintain perfect consistency with the reference video and the first 10 seconds.
Video: {vid_name}"""
                    extend_response = safe_generate_content([vf, extend_analysis])
                    
                    master_main = f"""GROK AI MASTER PROMPT - MAIN (10 detik pertama)

{main_response.text}

[CRITICAL] Use the reference image as pixel-perfect first frame. Lock face, body, outfit, and lighting for the first 1.5 seconds.
[PHYSICS] Maximum realism in hair, fabric, skin, weight distribution.
[TECHNICAL] 24fps, zero morphing, zero artifacts, look like real footage."""

                    master_extend = f"""GROK AI MASTER PROMPT - EXTEND (10 detik lanjutan)

{extend_response.text}

[CRITICAL] Continue seamlessly from the first 10 seconds. Maintain 100% visual consistency with the reference image.
[PHYSICS] Same hair physics, fabric behavior, skin detail, and natural movement as the main prompt.
[TECHNICAL] 24fps, perfect temporal consistency, zero drift in character appearance."""

                    st.success("✅ Master Prompt (Main + Extend) berhasil dibuat!")
                    
                    st.markdown("**📌 Prompt 1 - MAIN (10 detik pertama)**")
                    st.code(master_main)
                    if st.button("📋 Copy Main Prompt", key="copy_master_main"):
                        st.toast("✅ Main Prompt disalin!")
                    
                    st.markdown("**📌 Prompt 2 - EXTEND (10 detik lanjutan)**")
                    st.code(master_extend)
                    if st.button("📋 Copy Extend Prompt", key="copy_master_extend"):
                        st.toast("✅ Extend Prompt disalin!")
                    
                    genai.delete_file(vf.name)
                    os.remove(temp_path)

    # === TAB 2: Smart Prompt Refiner ===
    with epic_tab[1]:
        st.markdown("**🧠 Smart Prompt Refiner**")
        st.caption("Ambil prompt yang sudah ada → Gemini akan memperbaiki & memperkuatnya khusus untuk Grok AI")
        
        if st.session_state.all_prompts:
            selected_idx = st.selectbox("Pilih Prompt yang ingin di-Refine:", 
                                        range(len(st.session_state.all_prompts)), 
                                        format_func=lambda i: st.session_state.all_prompts[i]['name'])
            
            if st.button("🧠 REFINE THIS PROMPT", key="refine_btn"):
                with st.spinner("Gemini sedang memperbaiki prompt (Main + Extend)..."):
                    old_prompt = st.session_state.all_prompts[selected_idx]['p3']
                    
                    # Refine Main Prompt (first 10s)
                    refine_main = f"""Improve this Grok AI prompt to be even stronger for the FIRST 10 SECONDS.
Make it more powerful, detailed, and accurate to the reference video. Focus on perfect First Frame Lock and maximum realism.

Original Prompt:
{old_prompt[:600]}"""
                    main_refined = safe_generate_content(refine_main).text
                    
                    # Refine Extend Prompt
                    refine_extend = f"""Improve this Grok AI prompt to be a strong SEAMLESS CONTINUATION (next 10 seconds) of the first 10 seconds.
Maintain perfect consistency with the reference video and the main prompt. Focus on smooth transition and sustained quality.

Original Prompt (for context):
{old_prompt[:600]}"""
                    extend_refined = safe_generate_content(refine_extend).text
                    
                    st.success("✅ Prompt berhasil di-refine! (Main + Extend)")
                    
                    st.markdown("**📌 REFINED MAIN (10 detik pertama)**")
                    st.code(main_refined)
                    if st.button("📋 Copy Refined Main", key="copy_refined_main"):
                        st.toast("✅ Refined Main disalin!")
                    
                    st.markdown("**📌 REFINED EXTEND (10 detik lanjutan)**")
                    st.code(extend_refined)
                    if st.button("📋 Copy Refined Extend", key="copy_refined_extend"):
                        st.toast("✅ Refined Extend disalin!")
        else:
            st.info("Generate prompt dulu di section utama, baru bisa di-refine.")

    # === TAB 3: Prompt Quality Score ===
    with epic_tab[2]:
        st.markdown("**📊 Prompt Quality Score + Tips**")
        st.caption("Gemini akan menilai kualitas prompt kamu (1-100) + kasih saran perbaikan")
        
        if st.session_state.all_prompts:
            selected_idx = st.selectbox("Pilih Prompt untuk dinilai:", 
                                        range(len(st.session_state.all_prompts)), 
                                        format_func=lambda i: st.session_state.all_prompts[i]['name'],
                                        key="score_select")
            
            if st.button("📊 ANALYZE PROMPT QUALITY", key="score_btn"):
                with st.spinner("Menganalisis kualitas prompt..."):
                    prompt_to_analyze = st.session_state.all_prompts[selected_idx]['p3']
                    score_prompt = f"""Rate this Grok AI image-to-video prompt from 1-100 based on:
- First Frame Lock strength
- Physics & realism detail
- Human nuance capture
- Clarity for Grok AI

Prompt:
{prompt_to_analyze[:700]}

Respond in this format:
SCORE: XX/100
STRENGTHS: ...
WEAKNESSES: ...
SUGGESTIONS: ..."""
                    
                    response = safe_generate_content(score_prompt)
                    st.success("✅ Analisis selesai!")
                    st.code(response.text)
        else:
            st.info("Generate prompt dulu untuk bisa dianalisis.")

    # === TAB 4: Beat-Synced Prompt (NOW ACTIVE) ===
    with epic_tab[3]:
        st.markdown("**🎵 Beat-Synced Prompt Generator**")
        st.caption("Deteksi beat musik otomatis + masukkan timing presisi ke dalam prompt untuk Grok AI")
        
        if st.session_state.reference_videos:
            selected_idx = st.selectbox("Pilih Video untuk Beat Analysis:", 
                                        range(len(st.session_state.reference_videos)), 
                                        format_func=lambda i: st.session_state.reference_videos[i]['name'] if isinstance(st.session_state.reference_videos[i], dict) else "video",
                                        key="beat_video_select")
            
            if st.button("🎵 ANALYZE BEAT & GENERATE TIMED PROMPT", key="beat_btn", type="primary"):
                with st.spinner("Menganalisis beat musik + membuat prompt..."):
                    vid = st.session_state.reference_videos[selected_idx]
                    if isinstance(vid, dict):
                        vid_bytes = vid["bytes"] if isinstance(vid["bytes"], bytes) else bytes(vid["bytes"])
                        vid_name = vid["name"]
                    else:
                        vid_bytes = bytes(vid.getbuffer()) if hasattr(vid, 'getbuffer') else bytes(vid)
                        vid_name = getattr(vid, 'name', 'video')
                    
                    try:
                        import tempfile
                        import soundfile as sf
                        
                        # Save video temporarily
                        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                            tmp.write(vid_bytes)
                            tmp_path = tmp.name
                        
                        # Extract audio using ffmpeg
                        audio_path = tmp_path.replace(".mp4", ".wav")
                        subprocess.run([
                            "ffmpeg", "-y", "-i", tmp_path, 
                            "-vn", "-acodec", "pcm_s16le", "-ar", "22050", "-ac", "1",
                            audio_path
                        ], capture_output=True)
                        
                        # Load audio with librosa
                        y, sr = librosa.load(audio_path, sr=22050)
                        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
                        beat_times = librosa.frames_to_time(beats, sr=sr)
                        
                        # Create beat timing string
                        beat_str = ", ".join([f"{t:.1f}s" for t in beat_times[:12]])
                        
                        # Generate beat-synced prompt
                        beat_prompt = f"""GROK AI BEAT-SYNCED PROMPT (High Precision Timing)

[PERFORMER] Exact same person as reference video "{vid_name}".

[PERFORMANCE] Perform the exact same dance with perfect musical timing:
- Hit sharp movements exactly at these beats: {beat_str}
- Pause or slow down during off-beat moments
- Match the energy and dynamics of the original music
- Keep all micro-expressions, hair physics, and weight shifts from the reference

[TECHNICAL] 24fps, perfect synchronization with music, zero drift in timing, maximum realism.

Use the reference image as the exact first frame. Lock face, body, and outfit for the first 1 second."""

                        st.success(f"✅ Beat analysis berhasil! Tempo: {tempo:.1f} BPM")
                        st.code(beat_prompt)
                        
                        if st.button("📋 Copy Beat-Synced Prompt", key="copy_beat"):
                            st.toast("✅ Beat-Synced Prompt disalin!")
                        
                        # Cleanup
                        os.unlink(tmp_path)
                        if os.path.exists(audio_path):
                            os.unlink(audio_path)
                            
                    except Exception as e:
                        st.error(f"Gagal analisis beat: {e}")
                        st.info("Pastikan video memiliki audio. Coba video lain.")
        else:
            st.info("Tambahkan video dulu di Ready to Generate.")

    # === TAB 5: Movement Heatmap (Already Active - kept as is) ===
    with epic_tab[4]:
        st.markdown("**🔥 Movement Heatmap Visualizer**")
        st.caption("Lihat area gerakan paling intens di video referensi (sangat berguna untuk paham apa yang harus difokuskan)")
        
        if st.session_state.reference_videos:
            selected_idx = st.selectbox("Pilih Video:", range(len(st.session_state.reference_videos)), 
                                        format_func=lambda i: st.session_state.reference_videos[i]['name'] if isinstance(st.session_state.reference_videos[i], dict) else "video",
                                        key="heat_select")
            
            if st.button("🔥 GENERATE HEATMAP", key="heat_btn"):
                with st.spinner("Membuat Movement Heatmap..."):
                    vid = st.session_state.reference_videos[selected_idx]
                    if isinstance(vid, dict):
                        vid_bytes = vid["bytes"] if isinstance(vid["bytes"], bytes) else bytes(vid["bytes"])
                    else:
                        vid_bytes = bytes(vid.getbuffer()) if hasattr(vid, 'getbuffer') else bytes(vid)
                    
                    try:
                        import tempfile
                        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                            tmp.write(vid_bytes)
                            tmp_path = tmp.name
                        
                        cap = cv2.VideoCapture(tmp_path)
                        ret, prev = cap.read()
                        if ret:
                            prev_gray = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
                            heatmap = np.zeros_like(prev_gray, dtype=np.float32)
                            
                            frame_count = min(30, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
                            for _ in range(frame_count):
                                ret, frame = cap.read()
                                if not ret: break
                                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                                flow = cv2.calcOpticalFlowFarneback(prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
                                mag, _ = cv2.cartToPolar(flow[...,0], flow[...,1])
                                heatmap += mag
                                prev_gray = gray
                            
                            cap.release()
                            os.unlink(tmp_path)
                            
                            heatmap = cv2.normalize(heatmap, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
                            heatmap_color = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
                            
                            first_frame = cv2.cvtColor(prev, cv2.COLOR_BGR2RGB)
                            overlay = cv2.addWeighted(first_frame, 0.6, heatmap_color, 0.4, 0)
                            
                            st.image(overlay, caption="Movement Heatmap (Merah = Gerakan Intens)", use_column_width=True)
                            st.success("✅ Heatmap berhasil dibuat!")
                    except Exception as e:
                        st.error(f"Gagal membuat heatmap: {e}")
        else:
            st.info("Tambahkan video dulu di Ready to Generate.")

    # === TAB 6: Multi-Reference Fusion (NOW ACTIVE) ===
    with epic_tab[5]:
        st.markdown("**🌀 Multi-Reference Fusion**")
        st.caption("Gabungkan 2-3 video referensi jadi satu prompt (contoh: Face cantik dari video A + Gerakan dance keren dari video B)")
        
        if len(st.session_state.reference_videos) >= 2:
            st.success(f"✅ Kamu punya {len(st.session_state.reference_videos)} video. Pilih yang ingin digabungkan:")
            
            col1, col2 = st.columns(2)
            with col1:
                video_a = st.selectbox("Video A (Face / Karakter Utama):", 
                                       range(len(st.session_state.reference_videos)), 
                                       format_func=lambda i: st.session_state.reference_videos[i]['name'] if isinstance(st.session_state.reference_videos[i], dict) else "video",
                                       key="fusion_a")
            with col2:
                video_b = st.selectbox("Video B (Dance Style / Gerakan):", 
                                       range(len(st.session_state.reference_videos)), 
                                       format_func=lambda i: st.session_state.reference_videos[i]['name'] if isinstance(st.session_state.reference_videos[i], dict) else "video",
                                       key="fusion_b")
            
            fusion_desc = st.text_area("Deskripsi Fusion (opsional):", 
                                       value="Gunakan wajah dan outfit dari Video A, tapi gunakan gaya dance dan energi dari Video B. Pertahankan lighting dan background dari Video A.",
                                       height=60)
            
            if st.button("🌀 FUSE & GENERATE PROMPT", key="fusion_btn", type="primary"):
                with st.spinner("Menggabungkan 2 referensi + membuat prompt..."):
                    vid_a = st.session_state.reference_videos[video_a]
                    vid_b = st.session_state.reference_videos[video_b]
                    
                    # For simplicity, we'll use Gemini to fuse descriptions
                    name_a = vid_a['name'] if isinstance(vid_a, dict) else "Video A"
                    name_b = vid_b['name'] if isinstance(vid_b, dict) else "Video B"
                    
                    fusion_prompt = f"""Create a powerful Grok AI image-to-video prompt that fuses two reference videos:

VIDEO A ({name_a}): Use this as the main character reference (face, body, outfit, lighting, background).
VIDEO B ({name_b}): Use this as the movement and energy reference (dance style, timing, personality, dynamics).

Fusion Instruction: {fusion_desc}

Create a single, highly detailed prompt that combines the best of both videos for maximum realism and accuracy in Grok AI."""

                    response = safe_generate_content(fusion_prompt)
                    fused_prompt = f"""GROK AI MULTI-REFERENCE FUSION PROMPT

{response.text}

[CRITICAL] Use Video A as the exact visual reference for face, body, outfit, and environment.
[PERFORMANCE] Replicate the exact dance style, energy, and timing from Video B.
[TECHNICAL] 24fps, perfect consistency with Video A visuals, maximum realism."""

                    st.success("✅ Fusion Prompt berhasil dibuat!")
                    st.code(fused_prompt)
                    if st.button("📋 Copy Fused Prompt", key="copy_fused"):
                        st.toast("✅ Fused Prompt disalin!")
        else:
            st.warning("⚠️ Fitur ini membutuhkan minimal 2 video referensi. Tambahkan lebih banyak video di 'Ready to Generate'.")

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown("<p style='text-align:center; color:#666; font-size:0.85rem;'>GROK APEX V5 • Built specifically for Grok AI Image-to-Video • Universal Dance Prompt Engine • Powered by Gemini + OpenCV + MoviePy</p>", unsafe_allow_html=True)
