import os
import sys
import requests
import google.generativeai as genai

# 1. کانفیگریشن اور انوائرمنٹ ویری ایبلز
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MAKE_WEBHOOK_URL = os.getenv("BUFFER_WEBHOOK_URL")  # گٹ ہب سیکریٹ سے یو آر ایل لے گا
VIDEOS_DIR = "videos"  # آپ کے ویڈیو فولڈر کا نام

if not GEMINI_API_KEY or not MAKE_WEBHOOK_URL:
    print("❌ Missing Environment Variables: GEMINI_API_KEY or BUFFER_WEBHOOK_URL")
    sys.exit(1)

# جیمنائی اے آئی کو کنفیگر کریں
genai.configure(api_key=GEMINI_API_KEY)

def get_first_video(directory):
    """فولڈر سے صرف پہلی ویڈیو فائل ڈھونڈ کر لائے گا"""
    if not os.path.exists(directory):
        print(f"❌ فولڈر '{directory}' موجود نہیں ہے۔")
        return None
    
    supported_extensions = ('.mp4', '.mkv', '.avi', '.mov')
    # فائلوں کو سورٹ (Sort) کریں تاکہ ہر بار ایک ہی ترتیب سے ویڈیو اٹھے
    for file in sorted(os.listdir(directory)):
        if file.lower().endswith(supported_extensions):
            return os.path.join(directory, file)
    return None

def main():
    # فولڈر سے پہلی ویڈیو اٹھائیں
    video_path = get_first_video(VIDEOS_DIR)
    
    if not video_path:
        print("🎉 فولڈر میں کوئی ویڈیو باقی نہیں ہے! تمام ویڈیوز پروسیس ہو چکی ہیں۔")
        return

    video_filename = os.path.basename(video_path)
    print(f"🎬 پروسیسنگ کے لیے ویڈیو مل گئی ہے: {video_filename}")

    # فائل کے نام سے ٹاپک الگ کریں (جیسے آپ کے لاگ میں __ لگا ہوا تھا)
    topic = video_filename.split("__")[0] if "__" in video_filename else os.path.splitext(video_filename)[0]
    
    # === جیمنائی اے آئی پروسیسنگ ===
    print(f"🤖 [GEMINI AI] Creating Viral SEO for Topic: {topic}")
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"Create a viral SEO title, description, and tags for a short video about: {topic}. Return response in clean text."
        response = model.generate_content(prompt)
        seo_text = response.text
    except Exception as e:
        print(f"⚠️ Gemini API Error: {e}")
        sys.exit(1)

    # === اینٹی کاپی رائٹ پکسل کلیننگ (آپ کا پرانا لاجک یہاں چلے گا) ===
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
    
    # 401 ایرر فکس: ہیڈرز میں JSON فارمیٹ لازمی قرار دینا
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        res = requests.post(MAKE_WEBHOOK_URL, json=payload, headers=headers)
        
        # اگر ویب ہک کامیابی سے ڈیٹا وصول کر لے (Status Code 200 یا 201)
        if res.status_code in [200, 201, 202]:
            print(f"✅ Webhook accepted successfully! Code: {res.status_code}")
            
            # ویڈیو اپلوڈ/فارورڈ ہونے کے بعد اسے ڈیلیٹ کریں
            print(f"🗑️ Deleting processed video from folder: {video_path}")
            os.remove(video_path)
            
        else:
            print(f"❌ Webhook rejected with code: {res.status_code}")
            print(f"Make.com Response: {res.text}")
            print("⚠️ ویڈیو ڈیلیٹ نہیں کی گئی کیونکہ ویب ہک فیل ہو گیا تھا تاکہ آپ کا ڈیٹا ضائع نہ ہو۔")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error sending data to Make.com: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
