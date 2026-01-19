import os
import random
import time
import json
import traceback
import requests
import subprocess
import re
from openai import OpenAI
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
import moviepy.video.fx.all as vfx

# optional AWS helper
try:
    from aws_upload import upload_file_to_s3
except Exception:
    upload_file_to_s3 = None

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

HASHTAGS = "#wealth #success #darkpsychology #motivation #millionaire #mindset"
MENTIONS = "@instagram"

AI_MODELS = [
    "google/gemini-2.0-flash-exp:free",
    "google/gemini-flash-1.5-8b:free",
    "openai/gpt-4o-mini-2024-07-18:free",
    "meta-llama/llama-3.1-8b-instruct:free"
]

# -------------- 유틸리티 (normalize를 최상단으로 이동) --------------
def normalize(text):
    """텍스트에서 특수문자를 제거하고 소문자로 변환하여 중복 체크 정확도를 높임"""
    return re.sub(r'[^a-zA-Z0-9]', '', text).lower()

def get_list_from_file(file_path, default_values):
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(default_values))
        return default_values[:]
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def save_list_to_file(file_path, items):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(items))

def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return default

def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def safe_extract_text_from_openai_response(resp):
    try:
        if hasattr(resp, "choices") and len(resp.choices) > 0:
            return resp.choices[0].message.content.strip()
    except: pass
    return ""

# -------------- 핵심 로직: 대본 가져오기 (이 부분이 중복을 결정함) --------------
def get_best_sales_script(selected_topic):
    # 이미 사용한 대본 목록 불러오기
    used_scripts = load_json(USED_SCRIPTS_FILE, [])
    normalized_used = [normalize(s) for s in used_scripts]
    
    script = None
    is_emergency = False

    # 1. AI 모델들에게 신규 대본 요청
    if OPENROUTER_API_KEY:
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
        prompt = f"Create ONE viral Instagram Reel script about {selected_topic}. Dark psychology style. Provide ONLY the script text. No quotes."
        
        for model in AI_MODELS:
            try:
                print(f"🤖 {model} 모델로 신규 대본 생성 시도 중...")
                resp = client.chat.completions.create(model=model, messages=[{"role":"user","content":prompt}], timeout=45)
                raw = safe_extract_text_from_openai_response(resp)
                
                if raw:
                    clean_script = raw.replace('"', '').strip()
                    if normalize(clean_script) not in normalized_used and len(clean_script) > 10:
                        script = clean_script
                        print(f"✨ 신규 대본 생성 성공: {script}")
                        break
                    else:
                        print(f"🚫 {model}: 중복된 대본이 생성됨. 다음 모델로 이동.")
            except Exception as e:
                print(f"⚠️ {model} 실패: {e}")
                continue

    # 2. AI가 모두 실패했을 경우 비상 대본 파일에서 가져오기
    if not script:
        print("🆘 모든 AI 모델 실패. 비상 대본 리스트에서 미사용 대본 탐색...")
        e_scripts = get_list_from_file(EMERGENCY_FILE, ["Work in silence.", "Success is the best revenge."])
        
        # 아직 안 쓴 비상 대본만 필터링
        fresh_emergency = [s for s in e_scripts if normalize(s) not in normalized_used]
        
        if fresh_emergency:
            script = random.choice(fresh_emergency)
            is_emergency = True
            print(f"⚠️ 비상 대본 선택됨: {script}")
        else:
            # 비상 대본까지 다 썼다면 강제로 리스트 초기화 후 아무거나 선택 (최후의 수단)
            script = random.choice(e_scripts) if e_scripts else "Privacy is ultimate power."
            is_emergency = True
            print(f"🚨 모든 대본 소진! 중복 허용 선택: {script}")

    # 최종 선택된 대본을 '사용됨' 목록에 저장
    used_scripts.append(script)
    save_json(USED_SCRIPTS_FILE, used_scripts)
    
    return script, is_emergency

# -------------- 업데이트 함수들 --------------
def update_emergency_scripts(current_topic=None, used_script=None):
    """비상 대본 리스트를 풍성하게 채워넣는 함수"""
    scripts = get_list_from_file(EMERGENCY_FILE, ["Work in silence."])
    if used_script and used_script in scripts:
        scripts.remove(used_script)

    if OPENROUTER_API_KEY:
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
        prompt = f"Generate 10 different viral short quotes about {current_topic or 'wealth'}. One per line. No quotes."
        for model in AI_MODELS:
            try:
                resp = client.chat.completions.create(model=model, messages=[{"role":"user","content":prompt}])
                text = safe_extract_text_from_openai_response(resp)
                if text:
                    new_lines = [l.strip().replace('"','') for l in text.split('\n') if len(l.strip()) > 5]
                    combined = list(dict.fromkeys(scripts + new_lines))
                    save_list_to_file(EMERGENCY_FILE, combined)
                    return
            except: continue

def update_topics_list(used_topic):
    topics = get_list_from_file(TOPIC_FILE, ["Wealth secrets"])
    if used_topic in topics:
        topics.remove(used_topic)
    save_list_to_file(TOPIC_FILE, topics)

# -------------- 영상 제작 및 업로드 (기존 동일) --------------
# (post_to_instagram, upload_video_and_get_public_url 등은 기존의 작동하는 코드를 그대로 유지하세요)

def run_reels_bot():
    if not os.path.exists("background.mp4"):
        print("❌ background.mp4가 없습니다.")
        return

    # 1. 주제 선정
    topics = get_list_from_file(TOPIC_FILE, ["Dark psychology"])
    selected_topic = random.choice(topics)
    print(f"🎯 오늘의 주제: {selected_topic}")

    # 2. 대본 선정 (이 함수가 script와 캡션에 들어갈 내용을 결정)
    script, is_emergency = get_best_sales_script(selected_topic)
    
    # 3. 캡션 제작 (영상 글귀인 script가 캡션 맨 위로 가도록 설정)
    final_caption = f"{script}\n\n{MENTIONS}\n\n{HASHTAGS}"

    # 4. 영상 편집
    try:
        print("🎬 영상 제작 중...")
        video = VideoFileClip("background.mp4").subclip(0, 8).fx(vfx.colorx, 0.25)
        txt = TextClip(script, fontsize=45, color='white', size=(int(video.w*0.85), None),
                       font='DejaVu-Sans-Bold', method='caption', align='center',
                       interline=12, stroke_color='black', stroke_width=1.5).set_duration(8).set_pos('center')
        final = CompositeVideoClip([video, txt])
        
        audio_success = False
        if os.path.exists("music.mp3"):
            music = AudioFileClip("music.mp3").subclip(0, 8)
            final = final.set_audio(music)
            audio_success = True

        final.write_videofile("reels_video.mp4", fps=24, codec="libx264", audio=audio_success)
        print("✅ 영상 파일 생성 완료")
    except Exception as e:
        print(f"❌ 영상 제작 실패: {e}")
        return

    # 5. 업로드 및 마무리
    public_url = upload_video_and_get_public_url("reels_video.mp4")
    if public_url:
        print("⏳ 인스타그램 업로드 대기 중 (60초)...")
        time.sleep(60)
        if post_to_instagram(public_url, final_caption):
            print("🚀 인스타그램 게시 성공!")
            update_topics_list(selected_topic)
            update_emergency_scripts(selected_topic, script if is_emergency else None)

if __name__ == "__main__":
    run_reels_bot()
