import streamlit as st
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
from gtts import gTTS
import os

# Konfigurasi halaman utama
st.set_page_config(page_title="Free AI Voiceover & Auto-Caption", layout="centered")
st.title("🎬 AI Voiceover & Caption (Gratis 100%)")
st.write("Ubah teks menjadi suara Google dan tambahkan caption otomatis tanpa perlu API Key!")

# 1. Komponen Upload Video & Teks
uploaded_video = st.file_uploader("Pilih file video (MP4/MOV)", type=["mp4", "mov", "avi"])
text_input = st.text_area("Masukkan teks narasi (akan dijadikan suara & caption):", placeholder="Halo, selamat datang di video ini...")

# 2. Pilihan Bahasa
language = st.selectbox(
    "Pilih Bahasa Suara AI:", 
    [("Indonesia", "id"), ("Inggris", "en"), ("Jepang", "ja"), ("Korea", "ko")], 
    format_func=lambda x: x[0]
)

# Tombol Eksekusi
if st.button("⚡ Proses Video & Caption Sekarang"):
    if uploaded_video is None or text_input.strip() == "":
        st.warning("⚠️ Mohon unggah file video dan isi teks narasinya terlebih dahulu!")
    else:
        with st.spinner("Sedang membuat suara gratis, merender caption, dan menggabungkannya..."):
            try:
                # Simpan video mentah sementara ke lokal
                temp_video_path = "temp_input_video.mp4"
                with open(temp_video_path, "wb") as f:
                    f.write(uploaded_video.read())
                
                # 3. Generate Audio dari Teks menggunakan gTTS (GRATIS)
                temp_audio_path = "temp_generated_audio.mp3"
                tts = gTTS(text=text_input, lang=language[1], slow=False)
                tts.save(temp_audio_path)
                
                # Load Video dan Audio di MoviePy
                video_clip = VideoFileClip(temp_video_path)
                audio_clip = AudioFileClip(temp_audio_path)
                
                # --- LOGIKA AUTO-CAPTION ---
                
                # Memecah teks menjadi daftar kata
                words = text_input.split()
                # Menghitung perkiraan durasi (detik) per kata
                time_per_word = audio_clip.duration / max(len(words), 1)
                
                # Mengelompokkan kata menjadi potongan caption (misal 5 kata per baris)
                chunk_size = 5
                subtitle_clips = []
                
                for i in range(0, len(words), chunk_size):
                    chunk_text = " ".join(words[i:i+chunk_size])
                    chunk_duration = time_per_word * len(words[i:i+chunk_size])
                    
                    # Membuat grafis teks
                    txt_clip = TextClip(
                        chunk_text, 
                        fontsize=50, 
                        color='white', 
                        bg_color='black', # Latar belakang hitam agar teks mudah dibaca
                        font='Arial-Bold', 
                        method='caption',
                        size=(video_clip.w * 0.9, None)
                    )
                    
                    # Atur durasi dan letakkan teks di posisi bawah (bottom)
                    txt_clip = txt_clip.set_duration(chunk_duration).set_position(('center', 'bottom'))
                    subtitle_clips.append(txt_clip)
                
                # Gabungkan semua potongan caption secara berurutan
                final_subtitle_clip = concatenate_videoclips(subtitle_clips).set_position(('center', 'bottom'))
                
                # Tumpuk video asli dengan teks subtitle
                composite_video = CompositeVideoClip([video_clip, final_subtitle_clip])
                
                # --- SELESAI LOGIKA AUTO-CAPTION ---

                # Pasang audio gratis ke video gabungan
                final_clip = composite_video.set_audio(audio_clip)
                
                # Export Hasil
                output_video_path = "video_hasil_gratis.mp4"
                final_clip.write_videofile(
                    output_video_path, 
                    codec="libx264", 
                    audio_codec="aac",
                    fps=24,
                    logger=None
                )
                
                # Bersihkan memori
                video_clip.close()
                audio_clip.close()
                final_clip.close()
                composite_video.close()
                
                # 4. Tampilkan Hasil
                st.success("🎉 Video dengan Suara Gratis dan Caption berhasil dibuat!")
                st.video(output_video_path)
                
                # Tombol Download
                with open(output_video_path, "rb") as file:
                    st.download_button(
                        label="📥 Download Video Hasil",
                        data=file,
                        file_name="video_caption_gratis.mp4",
                        mime="video/mp4"
                    )
                
                # Hapus file mentah lokal
                os.remove(temp_video_path)
                os.remove(temp_audio_path)
                
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}. (Pastikan ImageMagick sudah terinstal untuk fitur teks!)")
