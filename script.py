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

BUFFER_TOKEN = os.getenv("BUFFER_API_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GITHUB_USER = os.getenv("GITHUB_REPOSITORY_OWNER", "YOUR_GITHUB_USERNAME")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY", "YOUR_REPO_NAME").split("/")[-1]

if not BUFFER_TOKEN or not GEMINI_API_KEY:
    print("❌ Error: BUFFER_API_TOKEN or GEMINI_API_KEY missing in GitHub Secrets!")
    sys.exit(1)

# جیمنائی کلائنٹ انیشلائزیشن
client = genai.Client(api_key=GEMINI_API_KEY)

os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)

if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        f.write("")

# =====================================================================
# 100% Anti-Copyright Video Engine
# =====================================================================
def process_video_for_algorithm_bypass(input_path, output_path):
    print(f"🎬 [ANTI-COPYRIGHT ENGINE] Restructuring pixels for: {os.path.basename(input_path)}")
    
    video_filter = (
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "setpts=0.98*PTS,"                       # 2% تیز رفتار
        "scale=iw*1.05:-1,crop=1080:1920,"       # مائنر زوم بارڈرز چینج کرنے کے لیے
        "eq=brightness=0.02:contrast=1.04:saturation=1.05," # ہلکی ڈیجیٹل کلر گریڈنگ
        "noise=alls=2:allf=t"                    # الگورتھم بائی پاس کرنے کے لیے پکسل نوائس
    )
    
    audio_filter = "asetrate=44100*1.02,atempo=1/1.02,atempo=1.02"

    cmd = [
        'ffmpeg', '-y',
        '-ss', '00:00:00', '-t', '57',          # فکسڈ 00:00 اسٹارٹ (تھمب نیل سیف)
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
        print("✅ Footprint cleaned! Thumbnail maintained safely.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg Processing Error: {e.stderr.decode('utf-8', errors='ignore')}")
        return False

# =====================================================================
# جیمنائی انڈپیک آٹو ماڈل سلیکشن ایس ای او انجن
# =====================================================================
def generate_viral_metadata(original_title):
    print(f"🤖 [GEMINI AI] Generating High-CTR SEO via Auto-Model Selection for: {original_title}")
    
    prompt = f"""
    You are an elite YouTube Shorts & Facebook Reels algorithm specialist optimizing facts content for the Indian, Pakistani, and South Asian markets (Factoholic style, Hindi/Urdu audience).
    
    The raw topic is: "{original_title}"
    
    Generate psychological click-triggers:
    1. "title": Create a high-suspense, curiosity-inducing hook title based on viral trends. Use exactly 1 shock emoji (e.g., 😱, 🤯, 🚨, 🤔). End strictly with `#shorts`. Keep it under 55 characters. Do not output 'Factoholic' in the title itself.
    2. "description": Write an advanced SEO block.
       - A highly engaging, suspenseful opening paragraph regarding "{original_title}" without spoiling the climax.
       - A dedicated section titled "Trending Searches:" injecting these high-volume analytics terms: "amazing facts", "interesting facts", "mind blowing facts in hindi", "random facts", "psychology facts", "facts short video".
       - End strictly with these hashtags: `#shorts`, `#viral`, `#reels`, `#factoholic`, `#facts`, `#trending`.
    3. "tags": ["factoholic", "facts", "amazing facts", "interesting facts", "shorts", "viral", "reels", "mind blowing facts", "random facts", "hindi facts"]

    Output strictly in this JSON format without markdown wrappers (Strictly NO ```json or backticks):
    {{
        "title": "Suspenseful Hook Title Emoji #shorts",
        "description": "Engaging text. Trending Searches: amazing facts, mind blowing facts in hindi. #shorts #viral #reels #factoholic #facts #trending",
        "tags": ["factoholic", "facts", "amazing facts", "viral", "shorts"]
    }}
    """
    try:
        # آٹو ماڈل سلیکشن (gemini-2.5-flash) بہترین رزلٹ اور ہائی اسپیڈ کے لیے
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        clean_text = response.text.strip()
        if clean_text.startswith("```"):
            clean_text = clean_text.replace("```json", "").replace("```", "").strip()
        
        metadata = json.loads(clean_text)
        
        if "#shorts" not in metadata["title"]:
            metadata["title"] += " #shorts"
        for tag in ["#shorts", "#factoholic", "#facts", "#viral", "#reels", "#trending"]:
            if tag not in metadata["description"]:
                metadata["description"] += f" {tag}"
                
        return metadata
    except Exception as e:
        print(f"⚠️ Gemini Fallback Triggered due to error: {e}")
        return {
            "title": f"This Will Shock You! 😱 #shorts",
            "description": f"Mind blowing facts regarding {original_title}. Trending Searches: amazing facts. #shorts #viral #reels #factoholic #facts #trending",
            "tags": ["factoholic", "facts", "amazing facts"]
        }

# =====================================================================
# بفر اے پی آئی انجن
# =====================================================================
def get_buffer_profiles():
    url = f"https://api.bufferapp.com/1/profiles.json?access_token={BUFFER_TOKEN}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            profiles = response.json()
            return [p["id"] for p in profiles]
        print(f"❌ Cannot retrieve Buffer profiles: {response.text}")
        return []
    except Exception as e:
        print(f"❌ Buffer Connection Error: {e}")
        return []

def upload_via_buffer(profile_ids, video_url, metadata):
    url = f"https://api.bufferapp.com/1/updates/create.json?access_token={BUFFER_TOKEN}"
    full_text = f"{metadata['title']}\n\n{metadata['description']}\nTags: {', '.join(metadata['tags'])}"
    
    payload = {
        "text": full_text,
        "media[video]": video_url,
        "shorten": False
    }
    for i, profile_id in enumerate(profile_ids):
        payload[f"profile_ids[{i}]"] = profile_id

    print("🚀 Pushing unique video payload directly to Buffer...")
    try:
        res = requests.post(url, data=payload)
        if res.status_code == 200:
            print("🎉 Success! Buffer has queued the video for YouTube Shorts & FB Reels.")
            return True
        print(f"❌ Buffer rejected payload: {res.text}")
        return False
    except Exception as e:
        print(f"❌ Buffer API Call Error: {e}")
        return False

def is_already_uploaded(video_name):
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        return video_name in f.read().splitlines()

def mark_as_uploaded(video_name):
    with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{video_name}\n")

# =====================================================================
# ورک فلو کنٹرولر
# =====================================================================
def main():
    video_files = glob.glob(os.path.join(VIDEOS_DIR, "*.mp4"))
    if not video_files:
        print(f"📁 '{VIDEOS_DIR}' folder is empty. No videos to process.")
        return
        
    profiles = get_buffer_profiles()
    if not profiles:
        print("❌ No active channels found on Buffer dashboard. Stopping.")
        return

    print(f"📦 Found {len(video_files)} video(s) ready in queue.")
    
    for video_path in video_files:
        raw_filename = os.path.basename(video_path)
        
        if is_already_uploaded(raw_filename):
            print(f"♻️ Skipping '{raw_filename}' (Already processed).")
            if os.path.exists(video_path):
                os.remove(video_path)
            continue
            
        clean_title_raw = os.path.splitext(raw_filename)[0].split("__")[0].replace("_", " ")
        metadata = generate_viral_metadata(clean_title_raw)
        processed_video_path = os.path.join(PROCESSED_DIR, f"ready_{raw_filename}")
        
        if process_video_for_algorithm_bypass(video_path, processed_video_path):
            public_video_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/videos/{raw_filename}"
            uploaded = upload_via_buffer(profiles, public_video_url, metadata)
            
            if uploaded:
                mark_as_uploaded(raw_filename)
                if os.path.exists(processed_video_path):
                    os.remove(processed_video_path)
                if os.path.exists(video_path):
                    os.remove(video_path)
                    print(f"🗑️ Clean-up Action: Original video '{raw_filename}' deleted.")
                print("🏁 Slot completed successfully!")
                break  
        else:
            print(f"⚠️ Error processing framework for {raw_filename}")

if __name__ == "__main__":
    main()
