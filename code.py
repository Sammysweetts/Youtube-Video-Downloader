# streamlit_app.py

import streamlit as st
import yt_dlp
import os

# 🌍 Setup custom headers to avoid 403 Forbidden
CUSTOM_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/115.0 Safari/537.36'
    )
}

st.set_page_config(page_title="YouTube Downloader", page_icon="📹")
st.title("📥 YouTube Video Downloader")

video_url = st.text_input("🎬 Enter YouTube video URL:")

if video_url:
    try:
        st.info("🔍 Extracting available formats...")

        info_extract_opts = {
            'quiet': True,
            'headers': CUSTOM_HEADERS,
        }

        # ⚡ Extract video & audio formats
        with yt_dlp.YoutubeDL(info_extract_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

        video_formats = []
        audio_formats = []

        for f in info['formats']:
            if (
                f.get('vcodec') != 'none'
                and f.get('acodec') == 'none'
                and f.get('height') is not None
            ):
                video_formats.append(f)
            elif f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                audio_formats.append(f)

        # 📊 Sort video formats by quality
        video_formats = sorted(video_formats, key=lambda x: x.get('height', 0), reverse=True)

        format_labels = []
        format_map = {}

        for f in video_formats:
            height = f.get('height')
            ext = f.get('ext')
            size = f.get('filesize') or f.get('filesize_approx')
            size_mb = f"{(size / 1024 / 1024):.1f}MB" if size else "Unknown"
            fmt_id = f.get('format_id')
            label = f"{height}p | {ext} | {size_mb}"
            format_labels.append(label)
            format_map[label] = fmt_id

        selected_label = st.selectbox("🎞 Select video resolution to download:", format_labels)

        if selected_label and st.button("⬇️ Start Download"):
            selected_video_format = format_map[selected_label]

            # 🥇 Pick best audio automatically
            best_audio_format = sorted(audio_formats, key=lambda x: x.get('abr', 0), reverse=True)[0]
            selected_audio_format = best_audio_format["format_id"]

            ydl_merge_opts = {
                'format': f'{selected_video_format}+{selected_audio_format}',
                'outtmpl': '/tmp/%(title)s.%(ext)s',
                'merge_output_format': 'mp4',
                'quiet': True,
                'headers': CUSTOM_HEADERS,
            }

            st.info("📥 Downloading and merging video + audio...")

            with yt_dlp.YoutubeDL(ydl_merge_opts) as ydl:
                ydl.download([video_url])

            # 🧾 Find downloaded file
            downloaded_files = [f for f in os.listdir("/tmp") if f.endswith(".mp4")]
            if downloaded_files:
                video_path = os.path.join("/tmp", downloaded_files[0])
                st.success(f"✅ Downloaded: {downloaded_files[0]}")

                with open(video_path, "rb") as f:
                    st.download_button(
                        label="📁 Click to Download MP4",
                        data=f,
                        file_name=downloaded_files[0],
                        mime="video/mp4",
                    )
            else:
                st.error("❌ Download failed or file not found.")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
