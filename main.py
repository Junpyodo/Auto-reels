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

# --- [고정 설정] 내 계정 아이덴티티 문구 ---
MY_IDENTITY_CAPTION = """
.
💡 Follow for more dark psychology secrets.
🚀 Join the 1% mindset today.
🔗 Link in bio to start your journey.
"""

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

# -------------- 유틸 (에러 방지를 위해 위쪽 배치) --------------
def normalize(text):
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
        except Exception:
            return default

def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def safe_extract_text_from_openai_response(resp):
    try:
        if hasattr(resp, "choices") and len(resp.choices) > 0:
            ch0 = resp.choices[0]
            if hasattr(ch0, "message") and hasattr(ch0.message, "content"):
                return ch0.message.content.strip()
    except Exception:
        pass
    return ""

# -------------- AI 관련 --------------
def update_emergency_scripts(current_topic=None, used_script=None):
    scripts = get_list_from_file(EMERGENCY_FILE, ["Work in silence.", "Success is the best revenge."])
    if used_script:
        scripts = [s for s in scripts if normalize(s) != normalize(used_script)]

    if not OPENROUTER_API_KEY:
        save_list_to_file(EMERGENCY_FILE, scripts)
        return

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
    topic_str = f"based on the topic '{current_topic}'" if current_topic else "about dark psychology and wealth"
    prompt = f"Generate 10 powerful, viral 20-word scripts for Instagram Reels {topic_str}. One per line. No numbers, no quotes."

    for model in AI_MODELS:
        try:
            time.sleep(1)
            resp = client.chat.completions.create(model=model, messages=[{"role":"user","content":prompt}])
            text = safe_extract_text_from_openai_response(resp)
            if not text: continue
            new_list = [line.strip().replace('"','') for line in text.split("\n") if len(line.strip()) > 5]
            if new_list:
                combined = list(dict.fromkeys(scripts + new_list))
                save_list_to_file(EMERGENCY_FILE, combined)
                print(f"✅ 비상 대본 업데이트 완료 ({model})")
                return
        except: continue

def update_topics_list(used_topic):
    if not OPENROUTER_API_KEY: return
    topics = get_list_from_file(TOPIC_FILE, ["Wealth psychology"])
    if used_topic in topics: topics.remove(used_topic)

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
    prompt = f"Based on {used_topic}, generate 10 new Instagram Reel topics. Newlines only."

    for model in AI_MODELS:
        try:
            time.sleep(1)
            resp = client.chat.completions.create(model=model, messages=[{"role":"user","content":prompt}])
            text = safe_extract_text_from_openai_response(resp)
            if not text: continue
            new_topics = [line.strip() for line in text.split("\n") if line.strip()]
            if new_topics:
                combined = list(dict.fromkeys(topics + new_topics))
                save_list_to_file(TOPIC_FILE, combined)
                print(f"✅ 주제 리스트 업데이트 완료 ({model})")
                return
        except: continue

def get_best_sales_script(selected_topic, max_attempts_per_model=2):
    if not OPENROUTER_API_KEY:
        e_scripts = get_list_from_file(EMERGENCY_FILE, ["The 1% don't sleep."])
        return random.choice(e_scripts), True

    used_scripts = load_json(USED_SCRIPTS_FILE, [])
    normalized_used_scripts = [normalize(s) for s in used_scripts]
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
    
    prompt_content = f"Topic: {selected_topic}. Create ONE viral script for Instagram Reels about dark psychology and wealth. NO quotes."

    for model in AI_MODELS:
        for _ in range(max_attempts_per_model):
            try:
                time.sleep(1.2)
                resp = client.chat.completions.create(model=model, messages=[{"role":"user","content":prompt_content}], temperature=0.9)
                script = safe_extract_text_from_openai_response(resp).split('\n')[0].strip().replace('"', '')
                if normalize(script) not in normalized_used_scripts and len(script) > 15:
                    used_scripts.append(script)
                    save_json(USED_SCRIPTS_FILE, used_scripts)
                    print(f"✨ 신규 대본 확정: {script}")
                    return script, False
            except: continue
    
    # 비상 대본 로직
    e_scripts = get_list_from_file(EMERGENCY_FILE, ["Work in silence."])
    fresh = [s for s in e_scripts if normalize(s) not in normalized_used_scripts]
    chosen = random.choice(fresh) if fresh else "Privacy is power."
    used_scripts.append(chosen)
    save_json(USED_SCRIPTS_FILE, used_scripts)
    return chosen, True

# -------------- 업로드 관련 (S3 제거 및 깃허브 중심) --------------
def gh_pages_publish(file_path):
    if not GITHUB_TOKEN: return None
    try:
        dest_name = os.path.basename(file_path)
        repo_url = f"https://x-access-token:{GITHUB_TOKEN}@github.com/{GITHUB_ID}/{REPO_NAME}.git"
        workdir = "/tmp/ghpages"
        
        subprocess.run(["rm", "-rf", workdir], check=False)
        subprocess.run(["git", "clone", repo_url, workdir], check=True)
        
        # gh-pages 브랜치 세팅
        ret = subprocess.run(["git", "checkout", "gh-pages"], cwd=workdir, capture_output=True)
        if ret.returncode != 0:
            subprocess.run(["git", "checkout", "--orphan", "gh-pages"], cwd=workdir, check=True)
            subprocess.run(["git", "rm", "-rf", "."], cwd=workdir, check=True)

        subprocess.run(["cp", file_path, os.path.join(workdir, dest_name)], check=True)
        subprocess.run(["git", "config", "user.name", "github-actions[bot]"], cwd=workdir)
        subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], cwd=workdir)
        subprocess.run(["git", "add", "."], cwd=workdir)
        subprocess.run(["git", "commit", "-m", "🚀 Update Reel Video"], cwd=workdir)
        subprocess.run(["git", "push", "origin", "gh-pages"], cwd=workdir, check=True)
        
        return f"https://{GITHUB_ID}.github.io/{REPO_NAME}/{dest_name}"
    except Exception as e:
        print(f"❌ GitHub Pages 업로드 실패: {e}")
        return None

def upload_video_and_get_public_url(file_path):
    # S3 시도 코드 삭제 (NameError 원인)
    print("🔼 GitHub Pages 업로드 시도...")
    url = gh_pages_publish(file_path)
    if url: return url

    # 실패 대비 0x0.st 시도
    try:
        with open(file_path, "rb") as f:
            r = requests.post("https://0x0.st", files={'file': f})
            if r.status_code == 200: return r.text.strip()
    except: pass
    
    return None

# -------------- Instagram 업로드 --------------
def post_to_instagram(video_url, caption):
    if not ACCESS_TOKEN or not ACCOUNT_ID: return False
    container_url = f"https://graph.facebook.com/v19.0/{ACCOUNT_ID}/media"
    payload = {'media_type': 'REELS', 'video_url': video_url, 'caption': caption, 'access_token': ACCESS_TOKEN}
    
    try:
        r = requests.post(container_url, data=payload).json()
        creation_id = r.get("id")
        if not creation_id: return False
        
        for _ in range(20):
            time.sleep(10)
            res = requests.get(f"https://graph.facebook.com/v19.0/{creation_id}", params={'fields':'status_code','access_token':ACCESS_TOKEN}).json()
            if res.get("status_code") == "FINISHED":
                pub = requests.post(f"https://graph.facebook.com/v19.0/{ACCOUNT_ID}/media_publish", data={'creation_id':creation_id, 'access_token':ACCESS_TOKEN}).json()
                return "id" in pub
    except: pass
    return False

# -------------- 메인 흐름 (문구 교체 핵심 수정 버전) --------------
def run_reels_bot():
    # 1. 파일명 고유화 (가장 중요!)
    # 매 실행마다 reels_17123456.mp4 처럼 이름이 달라져야 인스타 캐시를 피합니다.
    timestamp = int(time.time())
    final_video_name = f"reels_{timestamp}.mp4"
    
    # 작업 시작 전, 혹시 남아있을지 모르는 mp4 파일들 모두 삭제
    for f in os.listdir("."):
        if f.startswith("reels_") and f.endswith(".mp4"):
            try: os.remove(f)
            except: pass

    if not os.path.exists("background.mp4"): 
        print("❌ background.mp4 파일이 없습니다.")
        return

    # 2. 주제 선정 및 대본 생성
    topics = get_list_from_file(TOPIC_FILE, ["Dark psychology of wealth"])
    selected_topic = random.choice(topics)
    script, is_emergency = get_best_sales_script(selected_topic)
    
    # 캡션 구성 (대본 + 고정문구 + 해시태그)
    final_caption = f"{script}\n{MY_IDENTITY_CAPTION}\n{HASHTAGS}"

    # 3. 영상 편집 (영상의 '글귀'를 새로 생성)
    try:
        print(f"🎬 새 문구로 영상 제작 중: {script[:20]}...")
        video = VideoFileClip("background.mp4").subclip(0, 8).fx(vfx.colorx, 0.25)
        
        # 여기서 script 변수가 영상 중앙에 박힙니다.
        txt = TextClip(script, fontsize=45, color='white', size=(int(video.w*0.85), None),
                       font='DejaVu-Sans-Bold', method='caption', align='center',
                       stroke_color='black', stroke_width=1.5).set_duration(8).set_pos('center')
        
        final = CompositeVideoClip([video, txt])
        if os.path.exists("music.mp3"):
            final = final.set_audio(AudioFileClip("music.mp3").subclip(0, 8))
        
        # 고유한 파일명으로 저장
        final.write_videofile(final_video_name, fps=24, codec="libx264")
    except Exception as e:
        print(f"❌ 영상 제작 에러: {e}")
        return

    # 4. 깃허브 업로드 (고유한 파일명이 깃허브에 올라감)
    # 예: https://Junpyodo.github.io/Auto-reels/reels_17123456.mp4
    public_url = upload_video_and_get_public_url(final_video_name)
    if not public_url:
        print("❌ 업로드 URL 생성 실패")
        return

    print(f"🔗 새로운 영상 URL: {public_url}")
    print("⏳ 60초 대기 (인스타 서버가 새 영상을 안정적으로 가져가도록 시간 확보)...")
    time.sleep(60)

    # 5. 인스타그램 포스팅
    if post_to_instagram(public_url, final_caption):
        print("🎉 인스타그램 업로드 성공!")
        
        # 6. 업로드 성공 후 깃허브에서 영상 삭제 (정리 로직 호출)
        delete_from_gh_pages(final_video_name)
        
        if is_emergency: 
            update_emergency_scripts(selected_topic, script)
        else:
            update_topics_list(selected_topic)
            update_emergency_scripts(selected_topic)
    else:
        print("⚠️ 인스타그램 업로드 실패.")
