# streamlit_app.py

import streamlit as st
import yt_dlp
import os

# ✅ Custom headers to avoid 403 Forbidden by simulating a browser
CUSTOM_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/115.0.0.0 Safari/537.36 Edg/115.0.0.0'
    ),
    'Accept-Language': 'en-US,en;q=0.9',
}

st.set_page_config(page_title="YouTube Downloader", page_icon="📹")
st.title("📥 YouTube Video Downloader")

video_url = st.text_input("🔗 Enter a YouTube video URL:")

if video_url:
    try:
        st.info("🔍 Fetching available formats...")

        # Force IPv4 to avoid potential YouTube blocks on IPv6 addresses
        extract_opts = {
            'quiet': True,
            'no_warnings': True,
            'headers': CUSTOM_HEADERS,
            'force_ipv4': True,
        }

        with yt_dlp.YoutubeDL(extract_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

        video_formats = []
        audio_formats = []

        for f in info.get('formats', []):
            # Filter for video-only formats with a specified height
            if (
                f.get('vcodec') != 'none'
                and f.get('acodec') == 'none'
                and f.get('height') is not None
            ):
                video_formats.append(f)
            # Filter for audio-only formats
            elif (
                f.get('acodec') != 'none'
                and f.get('vcodec') == 'none'
            ):
                audio_formats.append(f)

        # Sort video formats by height in descending order
        video_formats = sorted(video_formats, key=lambda x: x.get('height', 0), reverse=True)

        format_labels = []
        format_map = {}

        for f in video_formats:
            height = f.get('height')
            ext = f.get('ext')
            size = f.get('filesize') or f.get('filesize_approx')
            size_text = f"{round(size / 1024 / 1024, 2)} MB" if size else "Unknown size"
            format_id = f.get('format_id')
            label = f"{height}p | {ext} | {size_text}"
            format_labels.append(label)
            format_map[label] = format_id

        selected_label = st.selectbox("🎞 Choose video quality:", format_labels)

        if st.button("⬇️ Download Video"):
            if not audio_formats:
                st.error("❌ No audio formats found to merge with the video.")
            else:
                video_format_id = format_map[selected_label]
                # Select the best available audio format
                audio_format_id = sorted(audio_formats, key=lambda x: x.get("abr", 0), reverse=True)[0]['format_id']

                st.info("📥 Download in progress...")

                # Define the output path and filename
                output_template = f"/tmp/{info.get('title', 'video')}.%(ext)s"

                download_opts = {
                    'format': f'{video_format_id}+{audio_format_id}',
                    'outtmpl': output_template,
                    'merge_output_format': 'mp4',
                    'quiet': True,
                    'no_warnings': True,
                    'headers': CUSTOM_HEADERS,
                    'force_ipv4': True,
                }

                with yt_dlp.YoutubeDL(download_opts) as ydl:
                    ydl.download([video_url])

                # Determine the expected filename after merging
                expected_filename = f"{info.get('title', 'video')}.mp4"
                filepath = os.path.join("/tmp", expected_filename)

                if os.path.exists(filepath):
                    st.success(f"✅ Video downloaded: {expected_filename}")

                    with open(filepath, "rb") as f:
                        st.download_button(
                            label="📂 Click to Download MP4",
                            data=f,
                            file_name=expected_filename,
                            mime="video/mp4"
                        )
                else:
                    st.warning("⚠️ File not found after download.")
 
    except Exception as e:
        st.error(f"❌ Error: {e}")
