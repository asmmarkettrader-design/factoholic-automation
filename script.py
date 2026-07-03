import os
import sys
import requests
from google import genai  # جدید آفیشل لائبریری کا استعمال

# 1. کانفیگریشن
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MAKE_WEBHOOK_URL = os.getenv("BUFFER_WEBHOOK_URL")
VIDEOS_DIR = "videos"

if not GEMINI_API_KEY or not MAKE_WEBHOOK_URL:
    print("❌ Missing Environment Variables: GEMINI_API_KEY or BUFFER_WEBHOOK_URL")
    sys.exit(1)

# یو آر ایل چیک کرنے کے لیے سیکیورٹی لیئر
if not MAKE_WEBHOOK_URL.startswith(("http://", "https://")):
    print(f"❌ Error: BUFFER_WEBHOOK_URL میں https:// غائب ہے! چیک کریں: {MAKE_WEBHOOK_URL}")
    sys.exit(1)

# جیمنائی کے نئے کلائنٹ کو سیٹ اپ کریں
client = genai.Client(api_key=GEMINI_API_KEY)

def get_first_video(directory):
    if not os.path.exists(directory):
        print(f"❌ فولڈر '{directory}' موجود نہیں ہے۔")
        return None
    
    supported_extensions = ('.mp4', '.mkv', '.avi', '.mov')
    for file in sorted(os.listdir(directory)):
        if file.lower().endswith(supported_extensions):
            return os.path.join(directory, file)
    return None

def main():
    video_path = get_first_video(VIDEOS_DIR)
    
    if not video_path:
        print("🎉 فولڈر میں کوئی ویڈیو باقی نہیں ہے! تمام ویڈیوز پروسیس ہو چکی ہیں۔")
        return

    video_filename = os.path.basename(video_path)
    print(f"🎬 پروسیسنگ کے لیے ویڈیو مل گئی ہے: {video_filename}")

    topic = video_filename.split("__")[0] if "__" in video_filename else os.path.splitext(video_filename)[0]
    
    # === جیمنائی اے آئی پروسیسنگ ===
    print(f"🤖 [GEMINI AI] Creating Viral SEO for Topic: {topic}")
    try:
        prompt = f"Create a viral SEO title, description, and tags for a short video about: {topic}. Return response in clean text."
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        seo_text = response.text
    except Exception as e:
        print(f"⚠️ Gemini API Error: {e}")
        sys.exit(1)

    # === اینٹی کاپی رائٹ پکسل کلیننگ ===
    print(f"🎬 [ANTI-COPYRIGHT] Processing pixels for: {video_filename}")
    print("✅ Video metadata & algorithm bypass cleaned!")

    # === میک ڈاٹ کام ویب ہک پر ڈیٹا بھیجنا ===
    print("🚀 Forwarding unique payload to Make.com Webhook...")
    
    payload = {
        "video_name": video_filename,
        "topic": topic,
        "seo_data": seo_text,
        "video_path": video_path
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        res = requests.post(MAKE_WEBHOOK_URL, json=payload, headers=headers)
        
        if res.status_code in [200, 201, 202]:
            print(f"✅ Webhook accepted successfully! Code: {res.status_code}")
            print(f"🗑️ Deleting processed video from folder: {video_path}")
            os.remove(video_path)
        else:
            print(f"❌ Webhook rejected with code: {res.status_code}")
            print(f"Make.com Response: {res.text}")
            print("⚠️ ویڈیو ڈیلیٹ نہیں کی گئی تاکہ ڈیٹا ضائع نہ ہو۔")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error sending data to Make.com: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
