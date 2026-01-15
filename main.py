# main.py
import os
import random
import time
import json
import traceback
import requests
import subprocess
from openai import OpenAI
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import moviepy.video.fx.all as vfx

# optional AWS helper (있으면 사용)
try:
    from aws_upload import upload_file_to_s3
except Exception:
    upload_file_to_s3 = None

# --- 설정 (레포에 이미 존재하던 시크릿/환경변수 이름 유지) ---
GITHUB_ID = "Junpyodo"
REPO_NAME = "Auto-reels"

TOPIC_FILE = "topics.txt"
EMERGENCY_FILE = "emergency_scripts.txt"
USED_SCRIPTS_FILE = "used_scripts.json"

ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Actions에서 자동 제공 가능

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
        try:
            return json.load(f)
        except Exception:
            return default

def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def safe_extract_text_from_openai_response(resp):
    try:
        if isinstance(resp, dict):
            if "choices" in resp and len(resp["choices"]) > 0:
                ch0 = resp["choices"][0]
                if "message" in ch0 and isinstance(ch0["message"], dict) and "content" in ch0["message"]:
                    return ch0["message"]["content"].strip()
                if "text" in ch0 and ch0["text"]:
                    return ch0["text"].strip()
        if hasattr(resp, "choices") and len(resp.choices) > 0:
            ch0 = resp.choices[0]
            if hasattr(ch0, "message") and hasattr(ch0.message, "content"):
                return ch0.message.content.strip()
            if hasattr(ch0, "text"):
                return ch0.text.strip()
    except Exception:
        pass
    return ""

# -------------- AI 관련 --------------
def update_emergency_scripts(used_script=None):
    scripts = get_list_from_file(EMERGENCY_FILE, ["Work in silence.", "Success is the best revenge."])
    if used_script and used_script in scripts:
        scripts.remove(used_script)

    if not OPENROUTER_API_KEY:
        save_list_to_file(EMERGENCY_FILE, scripts)
        print("⚠️ OPENROUTER_API_KEY가 없습니다 — emergency 업데이트 건너뜀")
        return

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
    prompt = "Generate 10 powerful, viral 20-word dark psychology scripts for Instagram Reels. One per line. No numbers."

    for model in AI_MODELS:
        try:
            time.sleep(1)
            resp = client.chat.completions.create(model=model, messages=[{"role":"user","content":prompt}])
            text = safe_extract_text_from_openai_response(resp)
            if not text:
                continue
            new_list = [line.strip().replace('"','') for line in text.split("\n") if line.strip()]
            if new_list:
                combined = list(dict.fromkeys(scripts + new_list))
                save_list_to_file(EMERGENCY_FILE, combined)
                print(f"✅ 비상 대본 리스트 보충 완료 ({model})")
                return
        except Exception as e:
            print(f"⚠️ update_emergency_scripts: {model} 실패: {e}")
            continue
    save_list_to_file(EMERGENCY_FILE, scripts)
    print("⚠️ 모든 모델 실패 — emergency 리스트는 유지됨")

def update_topics_list(used_topic):
    if not OPENROUTER_API_KEY:
        print("⚠️ OPENROUTER_API_KEY가 없습니다 — 주제 업데이트 건너뜀")
        return

    topics = get_list_from_file(TOPIC_FILE, ["Wealth psychology"])
    if used_topic in topics:
        topics.remove(used_topic)

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
    prompt = f"Based on {used_topic}, generate 10 new Instagram Reel topics about dark psychology and wealth. Newlines only."

    for model in AI_MODELS:
        try:
            time.sleep(1)
            resp = client.chat.completions.create(model=model, messages=[{"role":"user","content":prompt}])
            text = safe_extract_text_from_openai_response(resp)
            if not text:
                continue
            new_topics = [line.strip() for line in text.split("\n") if line.strip()]
            if new_topics:
                combined = list(dict.fromkeys(topics + new_topics))
                save_list_to_file(TOPIC_FILE, combined)
                print(f"✅ 주제 리스트 업데이트 완료 ({model})")
                return
        except Exception as e:
            print(f"⚠️ update_topics_list: {model} 실패: {e}")
            continue
    print("⚠️ 모든 모델 실패 — 주제 리스트 변경 안됨")

def get_best_sales_script(selected_topic, max_attempts_per_model=2):
    if not OPENROUTER_API_KEY:
        e_scripts = get_list_from_file(EMERGENCY_FILE, ["The 1% don't sleep until the job is done."])
        return random.choice(e_scripts), True

    used_scripts = load_json(USED_SCRIPTS_FILE, [])
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
    prompt_content = f"Topic: {selected_topic}\nCreate a powerful 20-word dark psychology script for an Instagram Reel. No intro. Provide exactly one line."

    print("🤖 AI 대본 생성 시도 중...")
    for model in AI_MODELS:
        for attempt in range(max_attempts_per_model):
            try:
                time.sleep(1 + attempt)
                resp = client.chat.completions.create(model=model, messages=[{"role":"user","content":prompt_content}])
                script = safe_extract_text_from_openai_response(resp).replace('"','').strip()
                if not script:
                    continue
                script_line = script.split("\n")[0].strip()
                if len(script_line) < 6:
                    continue
                if script_line in used_scripts:
                    print("⚠️ 생성된 스크립트는 이미 사용됨 — 건너뜀")
                    continue
                print(f"✨ [AI 생성 성공] 모델: {model}")
                used_scripts.append(script_line)
                save_json(USED_SCRIPTS_FILE, used_scripts)
                return script_line, False
            except Exception as e:
                print(f"⚠️ {model} 실패 (시도 {attempt+1}): {e}")
                continue

    print("🆘 모든 모델 실패 — 비상 대본 사용")
    e_scripts = get_list_from_file(EMERGENCY_FILE, ["The 1% don't sleep until the job is done."])
    chosen = random.choice(e_scripts)
    used = load_json(USED_SCRIPTS_FILE, [])
    used.append(chosen)
    save_json(USED_SCRIPTS_FILE, used)
    return chosen, True

# -------------- 외부 업로드(공개 URL 확보) --------------
def upload_to_0x0(file_path, max_attempts=2):
    url = "https://0x0.st"
    for attempt in range(max_attempts):
        try:
            with open(file_path,"rb") as f:
                files={'file':(os.path.basename(file_path), f)}
                r = requests.post(url, files=files, timeout=60)
            if r.status_code in (200,201) and r.text.strip().startswith("http"):
                return r.text.strip()
            else:
                print(f"⚠️ 0x0.st 실패({r.status_code}):{r.text}")
        except Exception as e:
            print("⚠️ 0x0.st 예외:", e)
        time.sleep(2*(attempt+1))
    return None

def upload_to_transfersh(file_path, max_attempts=2):
    for attempt in range(max_attempts):
        try:
            url = f"https://transfer.sh/{os.path.basename(file_path)}"
            with open(file_path,"rb") as f:
                r = requests.put(url, data=f, timeout=120)
            if r.status_code in (200,201):
                return r.text.strip()
            else:
                print(f"⚠️ transfer.sh 실패({r.status_code}): {r.text}")
        except Exception as e:
            print("⚠️ transfer.sh 예외:", e)
        time.sleep(2*(attempt+1))
    return None

def gh_pages_publish(file_path):
    """
    [에러 해결 버전] Git 사용자 정보 설정 및 gh-pages 브랜치 자동 생성 기능 추가
    """
    if not GITHUB_TOKEN:
        print("ℹ️ GITHUB_TOKEN이 없어 gh-pages 배포 불가.")
        return None
    try:
        dest_path = os.path.basename(file_path)
        repo_url = f"https://x-access-token:{GITHUB_TOKEN}@github.com/{GITHUB_ID}/{REPO_NAME}.git"
        workdir = "/tmp/auto-reels-ghpages"
        
        subprocess.run(["rm", "-rf", workdir], check=False)
        subprocess.run(["git", "clone", repo_url, workdir], check=True)
        
        # Git Identity 설정 (에러 방지 핵심)
        subprocess.run(["git", "config", "user.name", "github-actions[bot]"], cwd=workdir, check=True)
        subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], cwd=workdir, check=True)

        # gh-pages 브랜치 없으면 생성
        ret = subprocess.run(["git", "checkout", "gh-pages"], cwd=workdir, capture_output=True)
        if ret.returncode != 0:
            print("🌱 gh-pages 브랜치를 새로 생성합니다.")
            subprocess.run(["git", "checkout", "--orphan", "gh-pages"], cwd=workdir, check=True)
            subprocess.run(["git", "rm", "-rf", "."], cwd=workdir, check=True)

        dest = os.path.join(workdir, dest_path)
        subprocess.run(["cp", file_path, dest], check=True)
        subprocess.run(["git", "add", dest_path], cwd=workdir, check=True)
        subprocess.run(["git", "commit", "-m", "🚀 Add latest reel video"], cwd=workdir, check=True)
        subprocess.run(["git", "push", "origin", "gh-pages"], cwd=workdir, check=True)
        
        public_url = f"https://{GITHUB_ID}.github.io/{REPO_NAME}/{dest_path}"
        print("🔗 gh-pages 업로드 완료:", public_url)
        return public_url
    except Exception as e:
        print("❌ gh-pages 업로드 실패:", e)
        return None

def upload_video_and_get_public_url(file_path):
    if upload_file_to_s3:
        try:
            print("🔼 S3 업로드 시도...")
            s3_url = upload_file_to_s3(file_path)
            if s3_url:
                print("🔗 S3 업로드 성공:", s3_url)
                return s3_url
        except Exception as e:
            print("⚠️ S3 업로드 예외:", e)

    gh_url = gh_pages_publish(file_path)
    if gh_url:
        return gh_url

    print("🔼 0x0.st 업로드 시도...")
    url = upload_to_0x0(file_path)
    if url: return url

    print("🔼 transfer.sh 업로드 시도...")
    url = upload_to_transfersh(file_path)
    if url: return url

    print("❌ 공개 URL 생성 실패")
    return None

# -------------- Instagram 업로드 --------------
def post_to_instagram(video_url, caption, api_version="v19.0"):
    if not ACCESS_TOKEN or not ACCOUNT_ID:
        print("❌ INSTAGRAM_ACCESS_TOKEN 또는 INSTAGRAM_ACCOUNT_ID가 설정되어 있지 않습니다.")
        return False

    print("📤 인스타 업로드 시도. URL:", video_url)
    post_url = f"https://graph.facebook.com/{api_version}/{ACCOUNT_ID}/media"
    payload = {
        'media_type':'REELS',  # [수정 완료] VIDEO -> REELS
        'video_url': video_url,
        'caption': caption,
        'access_token': ACCESS_TOKEN
    }
    try:
        r = requests.post(post_url, data=payload, timeout=30)
        res = r.json() if r.status_code != 204 else {}
        print("▶ container create response:", res)
        
        if r.status_code != 200 or "id" not in res:
            print("❌ 컨테이너 생성 실패:", r.text)
            return False
            
        creation_id = res.get("id")

        # Polling
        print("⏳ 인스타그램 처리 대기...")
        status_url = f"https://graph.facebook.com/{api_version}/{creation_id}"
        params = {'fields':'status_code,progress,video_id','access_token':ACCESS_TOKEN}
        
        for _ in range(60): # 최대 5분
            rr = requests.get(status_url, params=params, timeout=30)
            status_res = rr.json()
            st = status_res.get("status_code", "").upper()
            if st in ("FINISHED", "PUBLISHED"): break
            time.sleep(5)

        # Publish
        publish_url = f"https://graph.facebook.com/{api_version}/{ACCOUNT_ID}/media_publish"
        r_pub = requests.post(publish_url, data={'creation_id':creation_id,'access_token':ACCESS_TOKEN}, timeout=30)
        pub_res = r_pub.json()
        
        if r_pub.status_code == 200 and 'id' in pub_res:
            print("🎉 업로드 성공! ID:", pub_res.get("id"))
            return True
        else:
            print("❌ publish 실패:", r_pub.text)
            return False
    except Exception as e:
        print("❌ API 예외:", e)
        return False

# -------------- 메인 흐름 --------------
def run_reels_bot():
    if not os.path.exists("background.mp4"):
        print("❌ background.mp4 파일이 필요합니다.")
        return

    topics = get_list_from_file(TOPIC_FILE, ["Dark psychology of wealth"])
    selected_topic = random.choice(topics)
    print("🎯 주제:", selected_topic)

    script, is_emergency = get_best_sales_script(selected_topic)
    final_caption = f"{script}\n\n{MENTIONS}\n\n{HASHTAGS}"

    try:
        print("🎬 영상 편집 시작...")
        video = VideoFileClip("background.mp4").subclip(0,8).fx(vfx.colorx, 0.25)
        txt = TextClip(script, fontsize=45, color='white', size=(int(video.w*0.85), None),
                       font='DejaVu-Sans-Bold', method='caption', align='center',
                       interline=12, stroke_color='black', stroke_width=1.5).set_duration(8).set_pos('center')
        final = CompositeVideoClip([video, txt])
        final_video_name = "reels_video.mp4"
        final.write_videofile(final_video_name, fps=24, codec="libx264", audio=False)
    except Exception as e:
        print("❌ 영상 제작 오류:", e)
        return

    public_url = upload_video_and_get_public_url(final_video_name)
    if not public_url:
        print("❌ 공개 URL 생성 실패.")
        return

    # [핵심 수정] 영상이 웹에 완전히 뿌려질 때까지 90초 대기
    print("⏳ GitHub Pages 배포 완료를 위해 90초간 대기합니다. 잠시만 기다려주세요...")
    time.sleep(120)
    success = post_to_instagram(public_url, final_caption)

    if success:
        if is_emergency: update_emergency_scripts(used_script=script)
        else:
            update_topics_list(used_topic=selected_topic)
            update_emergency_scripts()
    else:
        update_emergency_scripts()

if __name__ == "__main__":
    run_reels_bot()