import streamlit as st
import os
import urllib.request
import numpy as np

# --- 1. MONKEY PATCH PILLOW (Wajib diletakkan sebelum import MoviePy) ---
from PIL import Image, ImageDraw, ImageFont
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS
# -----------------------------------------------------------------------

# 2. Import library lainnya setelah patch aman
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip, concatenate_videoclips
from gtts import gTTS

# Konfigurasi halaman utama
st.set_page_config(page_title="Free AI Voiceover & Auto-Caption", layout="centered")
st.title("🎬 AI Voiceover & Word-by-Word Caption")
st.write("Ubah teks menjadi suara Google dengan caption otomatis yang muncul per kata!")

# Komponen Upload Video & Teks
uploaded_video = st.file_uploader("Pilih file video (MP4/MOV)", type=["mp4", "mov", "avi"])
text_input = st.text_area("Masukkan teks narasi:", placeholder="Halo, selamat datang di video ini...")

# Pilihan Bahasa Suara
language = st.selectbox(
    "Pilih Bahasa Suara AI:", 
    [("Indonesia", "id"), ("Inggris", "en"), ("Jepang", "ja"), ("Korea", "ko")], 
    format_func=lambda x: x[0]
)

# Pilihan Posisi Caption
caption_position = st.radio(
    "Pilih Posisi Letak Caption:",
    [("Bawah", "bottom"), ("Tengah", "center"), ("Atas", "top")],
    format_func=lambda x: x[0],
    horizontal=True
)

# Fungsi Khusus Pengganti ImageMagick (Render Teks dengan Pillow)
def create_caption_clip(text, duration, video_width):
    # Agar pas untuk satu kata, ukuran kotak disesuaikan secara proporsional
    box_width = int(video_width * 0.8)
    box_height = 90 # Sedikit lebih ramping karena hanya menampilkan satu kata
    
    # Buat kanvas hitam solid
    img = Image.new('RGB', (box_width, box_height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Otomatis download font Roboto jika belum ada di server
    font_path = "Roboto-Bold.ttf"
    if not os.path.exists(font_path):
        urllib.request.urlretrieve("https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf", font_path)
    
    try:
        font = ImageFont.truetype(font_path, 42) # Ukuran font sedikit diperbesar agar jelas
    except:
        font = ImageFont.load_default()
        
    # Kalkulasi ukuran teks agar posisinya tepat di tengah kotak hitam
    if hasattr(draw, 'textbbox'):
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    else:
        text_w, text_h = draw.textsize(text, font=font)
        
    x = (box_width - text_w) / 2
    y = (box_height - text_h) / 2
    
    # Gambar teks warna putih di atas kanvas hitam
    draw.text((x, y), text, font=font, fill='white')
    
    # Ubah gambar menjadi format array Numpy agar bisa dibaca MoviePy
    return ImageClip(np.array(img)).set_duration(duration)

# Tombol Eksekusi
if st.button("⚡ Proses Video & Caption Sekarang"):
    if uploaded_video is None or text_input.strip() == "":
        st.warning("⚠️ Mohon unggah file video dan isi teks narasinya terlebih dahulu!")
    else:
        with st.spinner("Sedang memproses suara AI dan menyinkronkan caption per kata..."):
            try:
                # Simpan video mentah
                temp_video_path = "temp_input_video.mp4"
                with open(temp_video_path, "wb") as f:
                    f.write(uploaded_video.read())
                
                # Generate Audio via gTTS
                temp_audio_path = "temp_generated_audio.mp3"
                tts = gTTS(text=text_input, lang=language[1], slow=False)
                tts.save(temp_audio_path)
                
                # Load Video dan Audio
                video_clip = VideoFileClip(temp_video_path)
                audio_clip = AudioFileClip(temp_audio_path)
                
                # PENGAMAN RESOLUSI
                w, h = video_clip.size
                w_safe = w if w % 2 == 0 else w - 1
                h_safe = h if h % 2 == 0 else h - 1
                video_clip = video_clip.resize((w_safe, h_safe))
                
                # --- LOGIKA BARU: PROSES CAPTION PER KATA ---
                words = text_input.split()
                time_per_word = audio_clip.duration / max(len(words), 1)
                
                subtitle_clips = []
                
                # Looping langsung per kata (tanpa digabung menjadi kalimat panjang)
                for word in words:
                    # Bersihkan spasi kosong jika ada
                    word = word.strip()
                    if word:
                        txt_clip = create_caption_clip(word, time_per_word, w_safe)
                        subtitle_clips.append(txt_clip)
                # --------------------------------------------
                
                # Gabungkan seluruh potongan kata secara berurutan
                pilihan_posisi = caption_position[1]
                final_subtitle_clip = concatenate_videoclips(subtitle_clips).set_position(('center', pilihan_posisi))
                
                # Tumpuk video asli dengan teks subtitle per kata
                composite_video = CompositeVideoClip([video_clip, final_subtitle_clip])
                
                # Pasang audio ke video gabungan
                final_clip = composite_video.set_audio(audio_clip)
                
                # Export Hasil Akhir
                output_video_path = "video_hasil_gratis.mp4"
                final_clip.write_videofile(
                    output_video_path, 
                    codec="libx264", 
                    audio_codec="aac",
                    fps=24,
                    logger=None
                )
                
                # Bersihkan memori sistem
                video_clip.close()
                audio_clip.close()
                final_clip.close()
                composite_video.close()
                
                # Tampilkan Hasil
                st.success("🎉 Video dengan gaya caption per kata berhasil dibuat!")
                st.video(output_video_path)
                
                # Download File
                with open(output_video_path, "rb") as file:
                    st.download_button(
                        label="📥 Download Video Hasil",
                        data=file,
                        file_name="video_per_kata.mp4",
                        mime="video/mp4"
                    )
                
                # Hapus file mentah lokal
                os.remove(temp_video_path)
                os.remove(temp_audio_path)
                
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")
