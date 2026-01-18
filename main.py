import os
import random
import time
import json
import requests
import subprocess
from openai import OpenAI
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
import moviepy.video.fx.all as vfx

# --- 설정 ---
GITHUB_ID = "Junpyodo"
REPO_NAME = "Auto-reels"
TOPIC_FILE = "topics.txt"
EMERGENCY_FILE = "emergency_scripts.txt"
USED_SCRIPTS_FILE = "used_scripts.json"

ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

AI_MODELS = [
    "google/gemini-2.0-flash-exp:free",
    "google/gemini-flash-1.5-8b:free",
    "openai/gpt-4o-mini-2024-07-18:free",
    "meta-llama/llama-3.1-8b-instruct:free"
]

# -------------- 유틸 --------------
def get_list_from_file(file_path):
    if not os.path.exists(file_path): return []
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def save_list_to_file(file_path, items):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(items))

def load_json(path, default):
    if not os.path.exists(path): return default
    with open(path, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return default

def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def safe_extract_text_from_openai_response(resp):
    try: return resp.choices[0].message.content.strip()
    except: return ""

# -------------- 핵심 로직 --------------
def get_best_sales_script(selected_topic):
    used_scripts = load_json(USED_SCRIPTS_FILE, [])
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
    
    prompt = (
        f"Role: High-status Dark Psychology master.\nTopic: {selected_topic}.\n"
        "Format: [Script] | [Caption] | [Hashtags]"
    )

    for attempt in range(3):
        try:
            resp = client.chat.completions.create(model=random.choice(AI_MODELS), messages=[{"role":"user","content":prompt}], timeout=30)
            raw = safe_extract_text_from_openai_response(resp)
            parts = raw.split('|')
            if len(parts) >= 3:
                script = parts[0].strip().replace('"','')
                if script not in used_scripts:
                    used_scripts.append(script)
                    save_json(USED_SCRIPTS_FILE, used_scripts)
                    return script, parts[1].strip(), parts[2].strip()
        except: time.sleep(2)

    # 비상 대본 로직
    print("🚨 비상 대본 사용")
    emergency_list = get_list_from_file(EMERGENCY_FILE)
    if not emergency_list: return "Master your mind.", "Hunter or prey?", "#success"
    
    chosen = random.choice(emergency_list)
    e_parts = chosen.split('|')
    script = e_parts[0].strip().replace('"','')
    
    # 중복 방지 기록 및 파일에서 삭제
    used_scripts.append(script)
    save_json(USED_SCRIPTS_FILE, used_scripts)
    emergency_list.remove(chosen)
    save_list_to_file(EMERGENCY_FILE, emergency_list)
    
    return script, e_parts[1].strip(), e_parts[2].strip()

def create_video(script):
    try:
        video = VideoFileClip("background.mp4").subclip(0, 8).fx(vfx.colorx, 0.25)
        # 폰트를 리눅스 서버 기본 폰트인 'NanumGothic-Bold'로 설정
        txt = TextClip(script, fontsize=45, color='white', size=(int(video.w * 0.85), None),
                       font='NanumGothic-Bold', method='caption', align='center',
                       interline=12, stroke_color='black', stroke_width=1.5).set_duration(8).set_pos('center')
        
        final = CompositeVideoClip([video, txt])
        if os.path.exists("music.mp3"):
            final = final.set_audio(AudioFileClip("music.mp3").subclip(0, 8))
            
        final.write_videofile("reels_video.mp4", fps=24, codec="libx264")
        return "reels_video.mp4"
    except Exception as e:
        print(f"❌ 에러: {e}"); return None

# (나머지 업로드 관련 함수 gh_pages_publish, post_to_instagram, run_reels_bot은 기존과 동일)
# ... [기존 업로드 코드 유지] ...

if __name__ == "__main__":
    run_reels_bot()