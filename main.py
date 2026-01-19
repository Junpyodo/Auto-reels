import os
import random
import time
import json
import requests
import subprocess
import re
from openai import OpenAI
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
import moviepy.video.fx.all as vfx

# --- [고정 설정] ---
GITHUB_ID = "Junpyodo"
REPO_NAME = "Auto-reels"
TOPIC_FILE = "topics.txt"
EMERGENCY_FILE = "emergency_scripts.txt"
USED_SCRIPTS_FILE = "used_scripts.json"

ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

MY_IDENTITY_CAPTION = "\n.\n💡 Follow for more dark psychology secrets.\n🚀 Join the 1% mindset today.\n🔗 Link in bio to start your journey."
HASHTAGS = "#wealth #success #darkpsychology #motivation #millionaire #mindset"
AI_MODELS = ["google/gemini-2.0-flash-exp:free", "google/gemini-flash-1.5-8b:free", "openai/gpt-4o-mini-2024-07-18:free"]

# --- [유틸리티 함수] ---
def normalize(text): return re.sub(r'[^a-zA-Z0-9]', '', text).lower()

def get_list_from_file(path, default):
    if not os.path.exists(path): return default
    with open(path, "r", encoding="utf-8") as f:
        return [l.strip() for l in f.readlines() if l.strip()]

def load_json(path, default):
    if not os.path.exists(path): return default
    with open(path, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return default

def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def safe_extract_text(resp):
    try: return resp.choices[0].message.content.strip()
    except: return ""

# --- [AI 및 대본 로직] ---
def get_best_sales_script(selected_topic):
    used_scripts = load_json(USED_SCRIPTS_FILE, [])
    norm_used = [normalize(s) for s in used_scripts]
    
    if not OPENROUTER_API_KEY:
        return "Focus on your goals, not your obstacles.", True

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
    prompt = f"Topic: {selected_topic}. Create ONE viral script for Instagram Reels about dark psychology and wealth. NO quotes."

    for model in AI_MODELS:
        try:
            resp = client.chat.completions.create(model=model, messages=[{"role":"user","content":prompt}])
            script = safe_extract_text(resp).split('\n')[0].strip().replace('"', '')
            if normalize(script) not in norm_used and len(script) > 10:
                used_scripts.append(script)
                save_json(USED_SCRIPTS_FILE, used_scripts)
                return script, False
        except: continue
    return "Privacy is power. Keep them guessing.", True

# --- [업로드 및 삭제 로직] ---
def gh_pages_publish(file_path):
    if not GITHUB_TOKEN: return None
    try:
        dest_name = os.path.basename(file_path)
        repo_url = f"https://x-access-token:{GITHUB_TOKEN}@github.com/{GITHUB_ID}/{REPO_NAME}.git"
        workdir = "/tmp/ghpages"
        subprocess.run(["rm", "-rf", workdir], check=False)
        subprocess.run(["git", "clone", "--depth", "1", "-b", "gh-pages", repo_url, workdir], check=True)
        subprocess.run(["cp", file_path, os.path.join(workdir, dest_name)], check=True)
        subprocess.run(["git", "config", "user.name", "github-actions[bot]"], cwd=workdir)
        subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], cwd=workdir)
        subprocess.run(["git", "add", "."], cwd=workdir)
        subprocess.run(["git", "commit", "-m", f"🚀 Upload {dest_name}"], cwd=workdir)
        subprocess.run(["git", "push", "origin", "gh-pages"], cwd=workdir, check=True)
        return f"https://{GITHUB_ID}.github.io/{REPO_NAME}/{dest_name}"
    except Exception as e:
        print(f"❌ GitHub 업로드 에러: {e}"); return None

def delete_from_gh_pages(file_name):
    try:
        workdir = "/tmp/ghpages_del"
        repo_url = f"https://x-access-token:{GITHUB_TOKEN}@github.com/{GITHUB_ID}/{REPO_NAME}.git"
        subprocess.run(["rm", "-rf", workdir], check=False)
        subprocess.run(["git", "clone", "--depth", "1", "-b", "gh-pages", repo_url, workdir], check=True)
        target = os.path.join(workdir, file_name)
        if os.path.exists(target):
            subprocess.run(["git", "rm", file_name], cwd=workdir)
            subprocess.run(["git", "config", "user.name", "github-actions[bot]"], cwd=workdir)
            subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], cwd=workdir)
            subprocess.run(["git", "commit", "-m", "🗑️ Cleanup temporary video"], cwd=workdir)
            subprocess.run(["git", "push", "origin", "gh-pages"], cwd=workdir)
            print(f"🗑️ {file_name} 삭제 완료")
    except: pass

def post_to_instagram(video_url, caption, api_version="v19.0"):
    # 1. 환경 변수 로드 (함수 내 정의로 안전성 확보)
    ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")

    if not ACCESS_TOKEN or not ACCOUNT_ID:
        print("❌ INSTAGRAM_ACCESS_TOKEN 또는 INSTAGRAM_ACCOUNT_ID가 설정되어 있지 않습니다.")
        return False

    print("📤 인스타 업로드 시도. URL:", video_url)
    
    # 2. 미디어 컨테이너 생성 주소
    container_url = f"https://graph.facebook.com/{api_version}/{ACCOUNT_ID}/media"

    payload = {
        'media_type': 'REELS',
        'video_url': video_url,
        'caption': caption,
        'share_to_feed': 'true', 
        'access_token': ACCESS_TOKEN
    }
    
    try:
        # 3. 컨테이너 생성
        r = requests.post(container_url, data=payload, timeout=30)
        res = r.json()
        print("▶ container create response:", res)
        
        if "id" not in res:
            print("❌ 컨테이너 생성 실패:", res)
            return False
            
        creation_id = res.get("id")

        # 4. 폴링(Polling): 인스타그램 서버의 영상 처리 상태 확인
        print("⏳ 인스타그램 서버에서 영상 처리 상태 확인 중...")
        status_url = f"https://graph.facebook.com/{api_version}/{creation_id}"
        status_params = {'fields': 'status_code', 'access_token': ACCESS_TOKEN}
        
        for i in range(20): # 최대 100초 (5초 * 20번)
            time.sleep(5)
            check_r = requests.get(status_url, params=status_params, timeout=30)
            status_res = check_r.json()
            status_code = status_res.get("status_code", "").upper()
            
            print(f"   - 상태 확인 ({i+1}/20): {status_code}")
            if status_code == "FINISHED":
                break
            elif status_code == "ERROR":
                print("❌ 영상 처리 중 에러 발생:", status_res)
                return False

        # 5. 최종 게시 (Publish)
        print("🚀 영상 처리 완료. 최종 게시 중...")
        publish_url = f"https://graph.facebook.com/{api_version}/{ACCOUNT_ID}/media_publish"
        publish_payload = {
            'creation_id': creation_id,
            'access_token': ACCESS_TOKEN
        }
        
        r_pub = requests.post(publish_url, data=publish_payload, timeout=30)
        pub_res = r_pub.json()
        
        if 'id' in pub_res:
            print("🎉 업로드 성공! 게시물 ID:", pub_res.get("id"))
            return True
        else:
            print("❌ 최종 게시 실패:", pub_res)
            return False

    except Exception as e:
        print("❌ API 예외 발생:", e)
        return False

# --- [메인 로봇 함수] ---
def run_reels_bot():
    # 1. 일련번호 생성 (기존 대본 개수 기준)
    used_scripts = load_json(USED_SCRIPTS_FILE, [])
    current_idx = len(used_scripts) + 1
    final_video_name = f"reels_{current_idx}.mp4"
    
    for f in os.listdir("."):
        if f.startswith("reels_") and f.endswith(".mp4"):
            try: os.remove(f)
            except: pass

    if not os.path.exists("background.mp4"): return

    # 2. 대본 생성
    topics = get_list_from_file(TOPIC_FILE, ["Dark psychology of wealth"])
    selected_topic = random.choice(topics)
    script, is_emergency = get_best_sales_script(selected_topic)
    final_caption = f"{script}\n{MY_IDENTITY_CAPTION}\n{HASHTAGS}"

    # 3. 영상 제작
    try:
        print(f"🎬 {current_idx}번째 영상 제작 중...")
        video = VideoFileClip("background.mp4").subclip(0, 8).fx(vfx.colorx, 0.25)
        txt = TextClip(script, fontsize=45, color='white', size=(int(video.w*0.85), None),
                       font='NanumGothic-Bold', method='caption', align='center',
                       stroke_color='black', stroke_width=1.5).set_duration(8).set_pos('center')
        final = CompositeVideoClip([video, txt])
        if os.path.exists("music.mp3"):
            final = final.set_audio(AudioFileClip("music.mp3").subclip(0, 8))
        final.write_videofile(final_video_name, fps=24, codec="libx264")
    except Exception as e:
        print(f"❌ 영상 제작 에러: {e}"); return

    # 4. 업로드
    public_url = gh_pages_publish(final_video_name)
    if not public_url: return

    print(f"⏳ 60초 대기... URL: {public_url}")
    time.sleep(60)

    # 5. 인스타 포스팅
    if post_to_instagram(public_url, final_caption):
        print(f"🎉 {current_idx}번째 릴스 성공!")
        delete_from_gh_pages(final_video_name)
    else:
        print("❌ 인스타 포스팅 실패")

if __name__ == "__main__":
    run_reels_bot()
