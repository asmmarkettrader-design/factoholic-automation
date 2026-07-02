import os
import sys
import glob
import subprocess
import json
import requests
from google import genai

# =====================================================================
# کانفیگریشن اور انوائرمنٹ سیٹ اپ
# =====================================================================
VIDEOS_DIR = "videos"
PROCESSED_DIR = "processed_videos"
HISTORY_FILE = "uploaded_history.txt"

WEBHOOK_URL = os.getenv("BUFFER_WEBHOOK_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GITHUB_USER = os.getenv("GITHUB_REPOSITORY_OWNER")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY", "").split("/")[-1]

if not WEBHOOK_URL or not GEMINI_API_KEY:
    print("❌ Error: BUFFER_WEBHOOK_URL or GEMINI_API_KEY missing in GitHub Secrets!")
    sys.exit(1)

# جیمنائی لیٹسٹ کلائنٹ (آٹو ماڈل سلیکشن کے لیے)
client = genai.Client(api_key=GEMINI_API_KEY)

os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)

if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        f.write("")

# =====================================================================
# Anti-Copyright Video Engine (FFmpeg)
# =====================================================================
def process_video_for_algorithm_bypass(input_path, output_path):
    print(f"🎬 [ANTI-COPYRIGHT] Processing pixels for: {os.path.basename(input_path)}")
    
    video_filter = (
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "setpts=0.98*PTS,"                       # 2% Speed up
        "scale=iw*1.05:-1,crop=1080:1920,"       # Minor Zoom
        "eq=brightness=0.02:contrast=1.04:saturation=1.05," # Color Grading
        "noise=alls=2:allf=t"                    # Unique Pixel Noise
    )
    audio_filter = "asetrate=44100*1.02,atempo=1/1.02,atempo=1.02"

    cmd = [
        'ffmpeg', '-y',
        '-ss', '00:00:00', '-t', '57',          # Under 60 seconds for Shorts/Reels
        '-i', input_path,
        '-async', '1',
        '-vf', video_filter,
        '-af', audio_filter,
        '-r', '30',
        '-c:v', 'libx264', '-crf', '17', '-preset', 'fast',
        '-c:a', 'aac', '-b:a', '320k', '-ar', '44100',
        output_path
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print("✅ Video metadata & algorithm bypass cleaned!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg Error: {e.stderr.decode('utf-8', errors='ignore')}")
        return False

# =====================================================================
# جیمنائی آٹو ایس ای او انجن (ٹائٹل، ہیش ٹیگز، کی ورڈز)
# =====================================================================
def generate_viral_metadata(original_title):
    print(f"🤖 [GEMINI AI] Creating Viral SEO for Topic: {original_title}")
    
    prompt = f"""
    You are an elite YouTube Shorts & Facebook Reels algorithm specialist optimizing facts content for South Asian audience (Factoholic style, Hindi/Urdu).
    The raw video topic/file name is: "{original_title}"
    
    Generate high-CTR metadata strictly in this JSON format without any markdown wrappers (Strictly NO ```json or backticks):
    {{
        "title": "Shocking Hook Title in Roman Urdu/Hindi + 1 Emoji #shorts",
        "description": "High suspense short summary of {original_title} without climax spoiler.\\n\\nTrending Searches:\\namazing facts, mind blowing facts in hindi, random facts, psychology facts, facts short video.\\n\\n#shorts #viral #reels #factoholic #facts #trending",
        "tags": "factoholic, facts, amazing facts, interesting facts, shorts, viral, reels, mind blowing facts"
    }}
    """
    try:
        # gemini-2.5-flash آٹو ماڈل سلیکشن
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        clean_text = response.text.strip()
        if clean_text.startswith("```"):
            clean_text = clean_text.replace("```json", "").replace("```", "").strip()
        
        metadata = json.loads(clean_text)
        if "#shorts" not in metadata["title"]:
            metadata["title"] += " #shorts"
        return metadata
    except Exception as e:
        print(f"⚠️ Gemini Fallback Triggered: {e}")
        return {
            "title": f"This Will Shock You! 😱 #shorts",
            "description": f"Mind blowing facts regarding {original_title}. Trending Searches: amazing facts. #shorts #viral #reels #factoholic #facts #trending",
            "tags": "factoholic, facts, amazing facts, shorts, viral, reels"
        }

# =====================================================================
# میک ڈاٹ کام ویب ہک گیٹ وے
# =====================================================================
def upload_via_webhook(video_url, metadata):
    print("🚀 Forwarding unique payload to Make.com Webhook...")
    
    payload = {
        "title": metadata["title"],
        "description": metadata["description"],
        "keywords_tags": metadata["tags"],
        "video_url": video_url
    }
    
    try:
        res = requests.post(WEBHOOK_URL, json=payload)
        if res.status_code in [200, 201, 202]:
            print("🎉 Success! Make.com accepted the data.")
            return True
        print(f"❌ Webhook rejected with code: {res.status_code}")
        return False
    except Exception as e:
        print(f"❌ Webhook Connection Error: {e}")
        return False

def is_already_uploaded(video_name):
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        return video_name in f.read().splitlines()

def mark_as_uploaded(video_name):
    with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{video_name}\n")

# =====================================================================
# مین ورک فلو کنٹرولر
# =====================================================================
def main():
    video_files = glob.glob(os.path.join(VIDEOS_DIR, "*.mp4"))
    if not video_files:
        print(f"📁 '{VIDEOS_DIR}' folder is empty. No videos to process.")
        return
        
    print(f"📦 Found {len(video_files)} video(s) in queue.")
    
    for video_path in video_files:
        raw_filename = os.path.basename(video_path)
        
        if is_already_uploaded(raw_filename):
            if os.path.exists(video_path):
                os.remove(video_path)
            continue
            
        # فائل کے نام سے صاف ستھرا ٹائٹل نکالنا
        clean_title_raw = os.path.splitext(raw_filename)[0].split("__")[0].replace("_", " ")
        
        # جیمنائی سے ایس ای او کروانا
        metadata = generate_viral_metadata(clean_title_raw)
        processed_video_path = os.path.join(PROCESSED_DIR, f"ready_{raw_filename}")
        
        if process_video_for_algorithm_bypass(video_path, processed_video_path):
            public_video_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/videos/{raw_filename}"
            
            uploaded = upload_via_webhook(public_video_url, metadata)
            
            if uploaded:
                mark_as_uploaded(raw_filename)
                if os.path.exists(processed_video_path):
                    os.remove(processed_video_path)
                if os.path.exists(video_path):
                    os.remove(video_path)
                    print(f"🗑️ Cleaned: Original video '{raw_filename}' deleted from workspace.")
                print("🏁 Slot processed successfully!")
                break  
        else:
            print(f"⚠️ Error processing framework for {raw_filename}")

if __name__ == "__main__":
    main()
