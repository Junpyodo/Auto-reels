import os
import random
import time
import json
import traceback
import requests
import subprocess
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
        save_json(path, default)
        return default
    with open(path, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return default

def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def safe_extract_text_from_openai_response(resp):
    try:
        if hasattr(resp, "choices") and len(resp.choices) > 0:
            return resp.choices[0].message.content.strip()
    except: pass
    return ""

# -------------- AI 핵심 로직 (중복될 경우 무한 재시도) --------------
def get_best_sales_script(selected_topic):
    if not OPENROUTER_API_KEY:
        return random.choice(get_list_from_file(EMERGENCY_FILE, ["Power is silent."])), True

    used_scripts = load_json(USED_SCRIPTS_FILE, [])
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
    
    prompt_content = (
        f"Role: High-status Dark Psychology master for the elite 1%.\n"
        f"Topic: {selected_topic}.\n\n"
        "Task: Write a viral 15-word Instagram Reel script.\n"
        "1. Hook: Start with a 'gut-punch' that shatters ego.\n"
        "2. Paradoxical Hope: Reveal a 'forbidden' psychological weapon.\n"
        "3. Tone: Cold, superior, predatory.\n"
        "4. Constraint: Exactly one sentence. No emojis. No hashtags.\n"
        "5. Originality: Avoid cliches. Be lethal and unique."
    )

    print(f"🤖 AI 대본 생성 시작 (주제: {selected_topic})")
    
    while True:
        model = random.choice(AI_MODELS)
        try:
            resp = client.chat.completions.create(model=model, messages=[{"role":"user","content":prompt_content}])
            script = safe_extract_text_from_openai_response(resp).replace('"','').strip()
            
            if script and len(script) > 12:
                if script not in used_scripts:
                    used_scripts.append(script)
                    save_json(USED_SCRIPTS_FILE, used_scripts)
                    print(f"✨ 새 대본 확정: {script} (모델: {model})")
                    return script, False
                else:
                    print(f"🔄 중복 감지: 다시 생성 중... (모델: {model})")
            
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ {model} 에러 발생, 재시도합니다.")
            time.sleep(2)

# -------------- 영상 제작 (자막 스타일 및 음악 1개 고정) --------------
def create_video(script):
    try:
        print("🎬 영상 편집 및 음악 합성 시작...")
        video = VideoFileClip("background.mp4").subclip(0, 8).fx(vfx.colorx, 0.25)
        
        # [자막 설정] 흰색 글자 + 검정 테두리
        txt = TextClip(script, 
                       fontsize=45, 
                       color='white', 
                       size=(int(video.w * 0.85), None),
                       font='DejaVu-Sans-Bold', 
                       method='caption', 
                       align='center', 
                       interline=12,
                       stroke_color='black', 
                       stroke_width=1.5).set_duration(8).set_pos('center')
        
        final_clip = CompositeVideoClip([video, txt])
        
        # [음악 설정] music.mp3 하나만 사용
        music_file = "music.mp3"
        
        if os.path.exists(music_file):
            audio = AudioFileClip(music_file).subclip(0, 8)
            final_clip = final_clip.set_audio(audio)
            print(f"🎵 음악 적용 완료: {music_file}")
        else:
            print(f"ℹ️ {music_file} 파일이 없어 묵음으로 진행합니다.")

        final_video_name = "reels_video.mp4"
        final_clip.write_videofile(final_video_name, fps=24, codec="libx264", audio=True if os.path.exists(music_file) else False)
        return final_video_name
    except Exception as e:
        print(f"❌ 영상 제작 에러: {e}")
        return None

# -------------- 업로드 로직 --------------
def gh_pages_publish(file_path):
    if not GITHUB_TOKEN: return None
    try:
        dest_path = os.path.basename(file_path)
        repo_url = f"https://x-access-token:{GITHUB_TOKEN}@github.com/{GITHUB_ID}/{REPO_NAME}.git"
        workdir = "/tmp/auto-reels-ghpages"
        subprocess.run(["rm", "-rf", workdir], check=False)
        subprocess.run(["git", "clone", repo_url, workdir], check=True)
        subprocess.run(["git", "config", "user.name", "github-actions[bot]"], cwd=workdir, check=True)
        subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], cwd=workdir, check=True)
        
        ret = subprocess.run(["git", "checkout", "gh-pages"], cwd=workdir, capture_output=True)
        if ret.returncode != 0:
            subprocess.run(["git", "checkout", "--orphan", "gh-pages"], cwd=workdir, check=True)
            subprocess.run(["git", "rm", "-rf", "."], cwd=workdir, check=True)

        subprocess.run(["cp", file_path, os.path.join(workdir, dest_path)], check=True)
        subprocess.run(["git", "add", "."], cwd=workdir, check=True)
        subprocess.run(["git", "commit", "-m", "🚀 Add Reel"], cwd=workdir, check=True)
        subprocess.run(["git", "push", "origin", "gh-pages"], cwd=workdir, check=True)
        return f"https://{GITHUB_ID}.github.io/{REPO_NAME}/{dest_path}"
    except: return None

def post_to_instagram(video_url, caption):
    api_url = f"https://graph.facebook.com/v19.0/{ACCOUNT_ID}/media"
    payload = {'media_type': 'REELS', 'video_url': video_url, 'caption': caption, 'access_token': ACCESS_TOKEN}
    try:
        r = requests.post(api_url, data=payload).json()
        if "id" not in r: return False
        creation_id = r["id"]
        for _ in range(20):
            time.sleep(10)
            status = requests.get(f"https://graph.facebook.com/v19.0/{creation_id}?fields=status_code&access_token={ACCESS_TOKEN}").json()
            if status.get("status_code") == "FINISHED": break
        
        publish = requests.post(f"https://graph.facebook.com/v19.0/{ACCOUNT_ID}/media_publish", data={'creation_id': creation_id, 'access_token': ACCESS_TOKEN}).json()
        return "id" in publish
    except: return False

# -------------- 메인 실행 --------------
def run_reels_bot():
    if not os.path.exists("background.mp4"): return
    topics = get_list_from_file(TOPIC_FILE, ["Dark psychology of wealth"])
    selected_topic = random.choice(topics)
    
    script, is_e = get_best_sales_script(selected_topic)
    final_video = create_video(script)

    if final_video:
        p_url = gh_pages_publish(final_video)
        if p_url:
            time.sleep(60)
            success = post_to_instagram(p_url, f"{script}\n\n{HASHTAGS}")
            if success: print("✅ 업로드 완료!")

if __name__ == "__main__":
    run_reels_bot()