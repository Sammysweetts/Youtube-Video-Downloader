# streamlit_app.py

import streamlit as st
import yt_dlp
import os
import subprocess

# 🚀 Streamlit UI
st.set_page_config(page_title="YouTube Video Downloader", page_icon="📹")

st.title("📥 YouTube Video Downloader")
video_url = st.text_input("🔗 Enter YouTube Video URL:")

if video_url:
    try:
        st.info("🔍 Fetching video formats...")
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

        video_formats = []
        audio_formats = []

        for f in info['formats']:
            if f.get('vcodec') != 'none' and f.get('acodec') == 'none' and f.get('height') is not None:
                video_formats.append(f)
            elif f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                audio_formats.append(f)

        video_formats = sorted(video_formats, key=lambda x: x.get('height', 0), reverse=True)

        format_labels = []
        format_map = {}
        for idx, f in enumerate(video_formats):
            height = f.get('height')
            ext = f.get('ext')
            size = f.get('filesize') or f.get('filesize_approx')
            size_mb = f"{(size / 1024 / 1024):.1f}MB" if size else "Unknown"
            fmt_id = f.get('format_id')
            label = f"{height}p | {ext} | {size_mb}"
            format_labels.append(label)
            format_map[label] = fmt_id

        selected_label = st.selectbox("🎞 Choose video resolution:", format_labels)

        if selected_label and st.button("⬇️ Download Video"):
            selected_video_format = format_map[selected_label]
            best_audio_format = sorted(audio_formats, key=lambda x: x.get('abr', 0), reverse=True)[0]
            selected_audio_format = best_audio_format['format_id']

            st.info('📥 Downloading selected video and audio streams...')
            ydl_merge_opts = {
                'format': f'{selected_video_format}+{selected_audio_format}',
                'outtmpl': '/tmp/%(title)s.%(ext)s',
                'merge_output_format': 'mp4',
                'quiet': True,
            }

            with yt_dlp.YoutubeDL(ydl_merge_opts) as ydl:
                result = ydl.download([video_url])

            downloaded_files = [f for f in os.listdir('/tmp') if f.endswith('.mp4')]
            if downloaded_files:
                video_path = os.path.join('/tmp', downloaded_files[0])
                st.success(f"✅ Download complete: {downloaded_files[0]}")
                with open(video_path, 'rb') as file:
                    st.download_button(
                        label="⬇️ Click to Download",
                        data=file,
                        file_name=downloaded_files[0],
                        mime="video/mp4"
                    )
            else:
                st.error("❌ Failed to download video.")
    except Exception as e:
        st.error(f"⚠️ Error: {str(e)}")
