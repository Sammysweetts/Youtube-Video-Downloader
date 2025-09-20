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
        extract_opts = {
            'quiet': True,
            'no_warnings': True,
            'headers': CUSTOM_HEADERS,
        }

        with yt_dlp.YoutubeDL(extract_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

        # --- Step 2: Filter for video-only formats and create UI choices ---
        video_formats = []
        for f in info.get('formats', []):
            # Filter for formats that have video but no audio
            if f.get('vcodec') != 'none' and f.get('acodec') == 'none' and f.get('height') is not None:
                video_formats.append(f)
        
        # Sort by height (resolution) in descending order
        video_formats = sorted(video_formats, key=lambda x: x.get('height', 0), reverse=True)

        format_labels = []
        format_map = {} # Maps a display label to the video height

        # Use a set to keep track of resolutions we've already added
        added_resolutions = set()

        for f in video_formats:
            height = f.get('height')
            if height in added_resolutions:
                continue # Skip if we already have this resolution

            ext = f.get('ext')
            size = f.get('filesize') or f.get('filesize_approx')
            size_text = f"{round(size / 1024 / 1024, 2)} MB" if size else "Unknown size"
            
            label = f"{height}p ({ext}) - {size_text}"
            format_labels.append(label)
            format_map[label] = height # Map the user-friendly label to the resolution height
            added_resolutions.add(height)

        if not format_labels:
            st.warning("No video-only formats found. This might be a live stream or a different kind of video.")
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
                            status_text.text(f"Downloading... {d['_percent_str']} of {d['_total_bytes_str']} at {d['_speed_str']}")
                        except (ValueError, TypeError):
                            pass # Ignore if percentage is not a number
                    elif d['status'] == 'finished':
                        progress_bar.progress(1.0)
                        status_text.text("Download finished, merging files...")

                # --- Step 3: Download using a format selector, not a fixed ID ---
                # This is the key change to fix the 403 error.
                # It tells yt-dlp to find the best video of the selected height and the best audio,
                # then merge them. This way, yt-dlp fetches fresh URLs at the time of download.
                download_opts = {
                    'format': f'bestvideo[height={selected_height}]+bestaudio/best',
                    'outtmpl': f'/tmp/{info["title"]}.%(ext)s',
                    'merge_output_format': 'mp4',
                    'quiet': True,
                    'no_warnings': True,
                    'headers': CUSTOM_HEADERS,
                    'progress_hooks': [progress_hook],
                }

                filepath = None
                with yt_dlp.YoutubeDL(download_opts) as ydl:
                    # We run extract_info again, but this time with download=True
                    # This gets us the final, correct filename after merging
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
                    
                    # Clean up the file from the server's temporary storage
                    os.remove(filepath)
                else:
                    st.warning("⚠️ File not found after download. It might be a DRM-protected video.")

    except Exception as e:
        st.error(f"❌ Error: {e}")
        if "HTTP Error 403" in str(e):
            st.error("This 403 error might be due to YouTube's restrictions. The video could be private, age-restricted, or region-locked.")
