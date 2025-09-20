# streamlit_app.py

import streamlit as st
import yt_dlp
import os

# ✅ Headers to mimic a real browser, crucial for avoiding 403 Forbidden errors
CUSTOM_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.google.com',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'cross-site',
    'Sec-Fetch-User': '?1',
    'TE': 'trailers',
}

st.set_page_config(page_title="YouTube Downloader", page_icon="📹")
st.title("📥 YouTube Video Downloader")

video_url = st.text_input("🔗 Enter a YouTube video URL:")

if video_url:
    try:
        st.info("🔍 Fetching available formats...")

        # --- Step 1: Get video info without downloading ---
        # ✅ Added 'cachedir': False to prevent using stale info
        extract_opts = {
            'quiet': True,
            'no_warnings': True,
            'headers': CUSTOM_HEADERS,
            'cachedir': False, 
        }

        with yt_dlp.YoutubeDL(extract_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            title = info.get('title', 'video')

        # --- Step 2: Filter for video-only formats and create UI choices ---
        video_formats = []
        for f in info.get('formats', []):
            if f.get('vcodec') != 'none' and f.get('acodec') == 'none' and f.get('height') is not None:
                video_formats.append(f)
        
        video_formats = sorted(video_formats, key=lambda x: x.get('height', 0), reverse=True)

        format_labels = []
        format_map = {} 
        added_resolutions = set()

        for f in video_formats:
            height = f.get('height')
            if height in added_resolutions:
                continue 

            ext = f.get('ext')
            size = f.get('filesize') or f.get('filesize_approx')
            size_text = f"{round(size / 1024 / 1024, 2)} MB" if size else "Unknown size"
            
            label = f"{height}p ({ext}) - {size_text}"
            format_labels.append(label)
            format_map[label] = height
            added_resolutions.add(height)

        if not format_labels:
            st.warning("No suitable video formats found. This could be a live stream or a protected video.")
        else:
            selected_label = st.selectbox("🎞 Choose video quality:", format_labels)

            if st.button("⬇️ Download Video"):
                selected_height = format_map[selected_label]
                
                st.info(f"📥 Download starting for {selected_height}p...")
                progress_bar = st.progress(0)
                status_text = st.empty()

                def progress_hook(d):
                    if d['status'] == 'downloading':
                        percentage = d.get('_percent_str', '0%').strip().replace('%', '')
                        try:
                            progress_bar.progress(float(percentage) / 100.0)
                            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                            if total_bytes:
                                total_bytes_str = f"{total_bytes / 1024 / 1024:.2f} MB"
                                status_text.text(f"Downloading... {d['_percent_str']} of {total_bytes_str} at {d.get('_speed_str', '')}")
                        except (ValueError, TypeError):
                             status_text.text("Processing...")
                    elif d['status'] == 'finished':
                        progress_bar.progress(1.0)
                        status_text.text("Download finished, merging files...")

                # --- Step 3: Download using a format selector ---
                # This tells yt-dlp to find the best streams at the time of download.
                # ✅ Added 'cachedir': False here as well for maximum reliability
                download_opts = {
                    'format': f'bestvideo[height={selected_height}]+bestaudio/best',
                    'outtmpl': f'/tmp/{title}.%(ext)s',
                    'merge_output_format': 'mp4',
                    'quiet': True,
                    'no_warnings': True,
                    'headers': CUSTOM_HEADERS,
                    'progress_hooks': [progress_hook],
                    'cachedir': False,
                }

                filepath = None
                try:
                    with yt_dlp.YoutubeDL(download_opts) as ydl:
                        download_info = ydl.extract_info(video_url, download=True)
                        filepath = ydl.prepare_filename(download_info)

                    if filepath and os.path.exists(filepath):
                        status_text.empty()
                        progress_bar.empty()
                        st.success(f"✅ Video downloaded: {os.path.basename(filepath)}")

                        with open(filepath, "rb") as f:
                            st.download_button(
                                label="📂 Click to Download MP4",
                                data=f,
                                file_name=os.path.basename(filepath),
                                mime="video/mp4"
                            )
                    else:
                        st.warning("⚠️ File not found after download process.")
                finally:
                    # ✅ Robust cleanup: Ensure the file is deleted from the server
                    if filepath and os.path.exists(filepath):
                        os.remove(filepath)

    except Exception as e:
        st.error(f"❌ An error occurred: {e}")
        if "HTTP Error 403" in str(e):
            st.error("This 403 error suggests YouTube is blocking the request. The video might be private, age-restricted, or region-locked. This tool may not work for all videos.")
