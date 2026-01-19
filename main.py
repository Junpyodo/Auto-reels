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

# -------------- 유틸 --------------
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
        try: return json.load(f)
        except Exception: return default

def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def safe_extract_text_from_openai_response(resp):
    try:
        if hasattr(resp, "choices") and len(resp.choices) > 0:
            return resp.choices[0].message.content.strip()
    except: pass
    return ""

# -------------- AI 관련 --------------
def get_best_sales_script(selected_topic, max_attempts_per_model=2):
    def normalize(text): return re.sub(r'[^a-zA-Z0-9]', '', text).lower()
    used_scripts = load_json(USED_SCRIPTS_FILE, [])
    normalized_used_scripts = [normalize(s) for s in used_scripts]
    
    if not OPENROUTER_API_KEY:
        e_scripts = get_list_from_file(EMERGENCY_FILE, ["The 1% don't sleep."])
        return random.choice(e_scripts), True

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
    prompt_content = f"Topic: {selected_topic}. Create a viral Reels script about dark psychology/wealth. No quotes."

    for model in AI_MODELS:
        for attempt in range(max_attempts_per_model):
            try:
                time.sleep(1.2)
                resp = client.chat.completions.create(model=model, messages=[{"role":"user","content":prompt_content}], temperature=0.95)
                script = safe_extract_text_from_openai_response(resp).split('\n')[0].strip().replace('"', '')
                if normalize(script) not in normalized_used_scripts and len(script) > 10:
                    used_scripts.append(script)
                    save_json(USED_SCRIPTS_FILE, used_scripts)
                    return script, False
            except: continue
    return "Privacy is power.", True

# -------------- 업로드 및 삭제 로직 --------------
def gh_pages_publish(file_path):
    if not GITHUB_TOKEN: return None
    try:
        dest_name = os.path.basename(file_path)
        repo_url = f"https://x-access-token:{GITHUB_TOKEN}@github.com/{GITHUB_ID}/{REPO_NAME}.git"
        workdir = "/tmp/auto-reels-ghpages"
        subprocess.run(["rm", "-rf", workdir], check=False)
        subprocess.run(["git", "clone", repo_url, workdir], check=True)
        subprocess.run(["git", "config", "user.name", "github-actions[bot]"], cwd=workdir)
        subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], cwd=workdir)
        
        # gh-pages 브랜치 체크아웃
        ret = subprocess.run(["git", "checkout", "gh-pages"], cwd=workdir, capture_output=True)
        if ret.returncode != 0:
            subprocess.run(["git", "checkout", "--orphan", "gh-pages"], cwd=workdir, check=True)
            subprocess.run(["git", "rm", "-rf", "."], cwd=workdir, check=True)

        dest = os.path.join(workdir, dest_name)
        subprocess.run(["cp", file_path, dest], check=True)
        subprocess.run(["git", "add", "."], cwd=workdir, check=True)
        subprocess.run(["git", "commit", "-m", f"🚀 Upload {dest_name}"], cwd=workdir, check=True)
        subprocess.run(["git", "push", "origin", "gh-pages"], cwd=workdir, check=True)
        
        return f"https://{GITHUB_ID}.github.io/{REPO_NAME}/{dest_name}"
    except Exception as e:
        print("❌ gh-pages 업로드 실패:", e)
        return None

def delete_from_gh_pages(file_name):
    try:
        workdir = "/tmp/ghpages_del"
        repo_url = f"https://x-access-token:{GITHUB_TOKEN}@github.com/{GITHUB_ID}/{REPO_NAME}.git"
        subprocess.run(["rm", "-rf", workdir], check=False)
        subprocess.run(["git", "clone", "--depth", "1", "-b", "gh-pages", repo_url, workdir], check=True)
        if os.path.exists(os.path.join(workdir, file_name)):
            subprocess.run(["git", "rm", file_name], cwd=workdir)
            subprocess.run(["git", "config", "user.name", "github-actions[bot]"], cwd=workdir)
            subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], cwd=workdir)
            subprocess.run(["git", "commit", "-m", "🗑️ Cleanup"], cwd=workdir)
            subprocess.run(["git", "push", "origin", "gh-pages"], cwd=workdir)
            print(f"🗑️ {file_name} 삭제 완료")
    except: pass

# -------------- Instagram 업로드 --------------
def post_to_instagram(video_url, caption):
    ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
    if not ACCESS_TOKEN or not ACCOUNT_ID: return False
    
    url = f"https://graph.facebook.com/v19.0/{ACCOUNT_ID}/media"
    payload = {'media_type': 'REELS', 'video_url': video_url, 'caption': caption, 'share_to_feed': 'true', 'access_token': ACCESS_TOKEN}
    
    try:
        r = requests.post(url, data=payload, timeout=30).json()
        if "id" not in r: return False
        c_id = r.get("id")
        for i in range(25):
            time.sleep(10)
            status = requests.get(f"https://graph.facebook.com/v19.0/{c_id}", params={'fields': 'status_code', 'access_token': ACCESS_TOKEN}).json()
            code = status.get("status_code", "").upper()
            print(f"   - 상태 확인 ({i+1}/25): {code}")
            if code == "FINISHED":
                res = requests.post(f"https://graph.facebook.com/v19.0/{ACCOUNT_ID}/media_publish", data={'creation_id': c_id, 'access_token': ACCESS_TOKEN}).json()
                return "id" in res
            elif code == "ERROR": return False
    except: return False
    return False

# -------------- 메인 흐름 --------------
def run_reels_bot():
    if not os.path.exists("background.mp4"): return

    used_scripts = load_json(USED_SCRIPTS_FILE, [])
    current_idx = len(used_scripts) + 1
    timestamp = int(time.time())
    # [수정] 일련번호와 고유숫자를 결합한 파일명
    final_video_name = f"reels_{current_idx}_{timestamp}.mp4"

    topics = get_list_from_file(TOPIC_FILE, ["Dark psychology"])
    selected_topic = random.choice(topics)
    script, is_emergency = get_best_sales_script(selected_topic)
    final_caption = f"{script}\n\n{MENTIONS}\n\n{HASHTAGS}"

    try:
        print(f"🎬 {current_idx}번째 영상 제작 중...")
        video = VideoFileClip("background.mp4").subclip(0,8).fx(vfx.colorx, 0.25)
        txt = TextClip(script, fontsize=45, color='white', size=(int(video.w*0.85), None),
                       font='DejaVu-Sans-Bold', method='caption', align='center',
                       interline=12, stroke_color='black', stroke_width=1.5).set_duration(8).set_pos('center')
        final = CompositeVideoClip([video, txt])
        
        audio_success = False
        if os.path.exists("music.mp3"):
            try:
                music = AudioFileClip("music.mp3").subclip(0, 8) 
                final = final.set_audio(music)
                audio_success = True
            except: pass

        final.write_videofile(final_video_name, fps=24, codec="libx264", audio=audio_success, audio_codec="aac")
    except Exception as e:
        print("❌ 제작 오류:", e); return

    # 업로드
    public_url = gh_pages_publish(final_video_name)
    if not public_url: return

    print(f"⏳ 배포 안정화 대기 (120초)... {public_url}")
    time.sleep(120)

    # 포스팅 및 성공 시 삭제
    if post_to_instagram(public_url, final_caption):
        print("✅ 성공! 깃허브 파일을 삭제합니다.")
        delete_from_gh_pages(final_video_name)
    else:
        print("⚠️ 업로드 실패")

if __name__ == "__main__":
    run_reels_bot()
