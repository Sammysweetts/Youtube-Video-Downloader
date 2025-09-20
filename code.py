import streamlit as st
import yt_dlp
import os

# ✅ Custom headers to avoid 403 Forbidden by simulating a browser
CUSTOM_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/115.0.0.0 Safari/537.36 Edg/115.0.0.0'
    )
}

st.set_page_config(page_title="YouTube Downloader", page_icon="📹")
st.title("📥 YouTube Video Downloader")

video_url = st.text_input("🔗 Enter a YouTube video URL:")

if video_url:
    try:
        st.info("🔍 Fetching available formats...")

        extract_opts = {
            'quiet': True,
            'no_warnings': True,
            'headers': CUSTOM_HEADERS,
        }

        with yt_dlp.YoutubeDL(extract_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

        video_formats = []
        audio_formats = []

        for format in info['formats']:
            if (
                format.get('vcodec') != 'none'
                and format.get('acodec') == 'none'
                and format.get('height') is not None
            ):
                video_formats.append(format)
            elif (
                format.get('acodec') != 'none'
                and format.get('vcodec') == 'none'
            ):
                audio_formats.append(format)

        video_formats = sorted(video_formats, key=lambda x: x.get('height', 0), reverse=True)

        format_labels = []
        format_map = {}

        for f in video_formats:
            height = f.get('height')
            ext = f.get('ext')
            size = f.get('filesize') or f.get('filesize_approx')
            size_text = f"{round(size / 1024 / 1024, 2)} MB" if size else "Unknown"
            format_id = f.get('format_id')
            label = f"{height}p | {ext} | {size_text}"
            format_labels.append(label)
            format_map[label] = format_id

        selected_label = st.selectbox("🎞 Choose video quality:", format_labels)

        if st.button("⬇️ Download Video"):
            video_format_id = format_map[selected_label]
            audio_format_id = sorted(audio_formats, key=lambda x: x.get("abr", 0), reverse=True)[0]['format_id']

            st.info("📥 Download in progress...")

            download_opts = {
                'format': f'{video_format_id}+{audio_format_id}',
                'outtmpl': '/tmp/%(title)s.%(ext)s',
                'merge_output_format': 'mp4',
                'quiet': True,
                'no_warnings': True,
                'headers': CUSTOM_HEADERS,
            }

            with yt_dlp.YoutubeDL(download_opts) as ydl:
                ydl.download([video_url])

            downloaded_files = [f for f in os.listdir("/tmp") if f.endswith(".mp4")]
            if downloaded_files:
                filepath = os.path.join("/tmp", downloaded_files[0])
                st.success(f"✅ Video downloaded: {downloaded_files[0]}")

                with open(filepath, "rb") as f:
                    st.download_button(
                        label="📂 Click to Download MP4",
                        data=f,
                        file_name=downloaded_files[0],
                        mime="video/mp4"
                    )
            else:
                st.warning("⚠️ File not found after download.")
 
    except Exception as e:
        st.error(f"❌ Error: {e}")
