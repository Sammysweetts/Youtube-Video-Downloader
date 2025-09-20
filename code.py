# streamlit_app.py

import streamlit as st
import yt_dlp
import os
import tempfile
from pathlib import Path

# ✅ Enhanced configuration to avoid 403 errors
CUSTOM_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-us,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
    'Keep-Alive': '115',
    'Connection': 'keep-alive',
}

st.set_page_config(page_title="YouTube Downloader", page_icon="📹")
st.title("📥 YouTube Video Downloader")

video_url = st.text_input("🔗 Enter a YouTube video URL:")

if video_url:
    try:
        st.info("🔍 Fetching available formats...")

        # Enhanced extraction options
        extract_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'force_generic_extractor': False,
            'headers': CUSTOM_HEADERS,
            # Additional options to help with 403 errors
            'cookiefile': None,
            'nocheckcertificate': True,
            'prefer_insecure': True,
            'user_agent': CUSTOM_HEADERS['User-Agent'],
            # Use different extractors if needed
            'allowed_extractors': ['youtube', 'youtube:tab', 'youtube:playlist'],
        }

        with yt_dlp.YoutubeDL(extract_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

        # Get video title for display
        video_title = info.get('title', 'Unknown Title')
        st.success(f"📺 Found: {video_title}")

        video_formats = []
        audio_formats = []

        for format in info['formats']:
            if format.get('vcodec') != 'none' and format.get('acodec') == 'none' and format.get('height') is not None:
                video_formats.append(format)
            elif format.get('acodec') != 'none' and format.get('vcodec') == 'none':
                audio_formats.append(format)

        # Sort video formats by quality
        video_formats = sorted(video_formats, key=lambda x: x.get('height', 0), reverse=True)

        if not video_formats:
            st.error("No video formats available for this video.")
        else:
            format_labels = []
            format_map = {}

            for f in video_formats:
                height = f.get('height')
                ext = f.get('ext')
                size = f.get('filesize') or f.get('filesize_approx')
                size_text = f"{round(size / 1024 / 1024, 2)} MB" if size else "Unknown size"
                format_id = f.get('format_id')
                fps = f.get('fps', 'Unknown')
                label = f"{height}p | {fps}fps | {ext} | {size_text}"
                format_labels.append(label)
                format_map[label] = format_id

            selected_label = st.selectbox("🎞 Choose video quality:", format_labels)

            # Add format selection for audio-only download
            download_type = st.radio("📥 Download type:", ["Video + Audio", "Audio Only"])

            if st.button("⬇️ Download"):
                try:
                    # Create a temporary directory
                    with tempfile.TemporaryDirectory() as temp_dir:
                        if download_type == "Video + Audio":
                            video_format_id = format_map[selected_label]
                            
                            # Find best audio format
                            if audio_formats:
                                audio_format_id = sorted(audio_formats, key=lambda x: x.get("abr", 0), reverse=True)[0]['format_id']
                                format_string = f'{video_format_id}+{audio_format_id}/best[ext=mp4]/best'
                            else:
                                format_string = f'{video_format_id}/best'
                            
                            output_ext = 'mp4'
                        else:
                            # Audio only
                            if audio_formats:
                                audio_format_id = sorted(audio_formats, key=lambda x: x.get("abr", 0), reverse=True)[0]['format_id']
                                format_string = f'{audio_format_id}/bestaudio'
                            else:
                                format_string = 'bestaudio'
                            output_ext = 'mp3'

                        # Safe filename
                        safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                        output_filename = f"{safe_title}.{output_ext}"
                        output_path = os.path.join(temp_dir, output_filename)

                        st.info("📥 Download in progress... This may take a few moments.")

                        # Enhanced download options
                        download_opts = {
                            'format': format_string,
                            'outtmpl': output_path,
                            'quiet': True,
                            'no_warnings': True,
                            'headers': CUSTOM_HEADERS,
                            'user_agent': CUSTOM_HEADERS['User-Agent'],
                            'nocheckcertificate': True,
                            'prefer_insecure': True,
                            # Additional options for better compatibility
                            'ignoreerrors': False,
                            'no_color': True,
                            'no_call_home': True,
                            'no_check_certificate': True,
                            # Post-processing options
                            'postprocessors': [{
                                'key': 'FFmpegVideoConvertor',
                                'preferedformat': output_ext,
                            }] if download_type == "Video + Audio" else [{
                                'key': 'FFmpegExtractAudio',
                                'preferredcodec': 'mp3',
                                'preferredquality': '192',
                            }],
                            # Retry options
                            'retries': 10,
                            'fragment_retries': 10,
                            'skip_unavailable_fragments': True,
                        }

                        # Progress bar placeholder
                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        def progress_hook(d):
                            if d['status'] == 'downloading':
                                percent = d.get('downloaded_bytes', 0) / d.get('total_bytes', 1)
                                progress_bar.progress(min(percent, 1.0))
                                status_text.text(f"Downloading: {percent*100:.1f}%")
                            elif d['status'] == 'finished':
                                progress_bar.progress(1.0)
                                status_text.text("Processing...")

                        download_opts['progress_hooks'] = [progress_hook]

                        with yt_dlp.YoutubeDL(download_opts) as ydl:
                            ydl.download([video_url])

                        # Check if file was created
                        if os.path.exists(output_path):
                            st.success(f"✅ Download complete: {output_filename}")
                            
                            # Read file and provide download button
                            with open(output_path, "rb") as f:
                                file_data = f.read()
                                
                            st.download_button(
                                label=f"📂 Click to Download {output_ext.upper()}",
                                data=file_data,
                                file_name=output_filename,
                                mime=f"video/{output_ext}" if download_type == "Video + Audio" else f"audio/{output_ext}"
                            )
                        else:
                            st.error("⚠️ File not found after download.")
                            
                except Exception as e:
                    st.error(f"❌ Download error: {str(e)}")
                    st.info("💡 Try selecting a different quality or format.")
                    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        if "HTTP Error 403" in str(e):
            st.warning("⚠️ YouTube is blocking the request. This might be due to:")
            st.write("• Regional restrictions")
            st.write("• Age-restricted content")
            st.write("• Private videos")
            st.write("• YouTube's anti-bot measures")
            st.info("💡 Try again in a few moments or with a different video.")
        else:
            st.info("💡 Please check if the URL is valid and try again.")

# Add information section
with st.expander("ℹ️ How to use"):
    st.write("""
    1. Copy a YouTube video URL
    2. Paste it in the input field above
    3. Select your preferred video quality
    4. Choose between Video+Audio or Audio only
    5. Click Download and wait for processing
    6. Click the download button to save the file
    """)

# Footer
st.markdown("---")
st.markdown("⚠️ Please respect copyright laws and YouTube's Terms of Service.")
