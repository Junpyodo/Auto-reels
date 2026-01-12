import os
import random
import time
import requests
from openai import OpenAI
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import moviepy.video.fx.all as vfx
import json
import traceback

# --- [필수 설정 항목] ---
GITHUB_ID = "Junpyodo"
REPO_NAME = "Auto-reels"
# -----------------------

TOPIC_FILE = "topics.txt"
EMERGENCY_FILE = "emergency_scripts.txt"

# 환경 변수에서 읽어오기
ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

HASHTAGS = "#wealth #success #darkpsychology #motivation #millionaire #mindset"
MENTIONS = "@instagram"

# AI 모델 리스트 (openrouter에서 사용 가능한 모델 ID들)
AI_MODELS = [
    "google/gemini-2.0-flash-exp:free",
    "google/gemini-flash-1.5-8b:free",
    "openai/gpt-4o-mini-2024-07-18:free",
    "meta-llama/llama-3.1-8b-instruct:free"
]

# ---------------- 유틸 ----------------
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

def safe_extract_text_from_openai_response(resp):
    """
    openrouter / openai 응답 형식이 다양할 수 있어서 여러 경로를 시도합니다.
    """
    try:
        # 경우1: choices[0].message.content
        if isinstance(resp, dict):
            if "choices" in resp and len(resp["choices"]) > 0:
                ch0 = resp["choices"][0]
                # openai v1 chat style
                if "message" in ch0 and isinstance(ch0["message"], dict) and "content" in ch0["message"]:
                    return ch0["message"]["content"].strip()
                # text 속성 사용
                if "text" in ch0 and ch0["text"]:
                    return ch0["text"].strip()
        # 객체형 응답일 경우(라이브러리 반환)
        if hasattr(resp, "choices") and len(resp.choices) > 0:
            ch0 = resp.choices[0]
            # message.content
            if hasattr(ch0, "message") and hasattr(ch0.message, "content"):
                return ch0.message.content.strip()
            if hasattr(ch0, "text"):
                return ch0.text.strip()
    except Exception:
        pass
    return ""

# ---------------- AI 관련 ----------------
def update_emergency_scripts(used_script=None):
    scripts = get_list_from_file(EMERGENCY_FILE, ["Work in silence.", "Success is the best revenge."])
    if used_script and used_script in scripts:
        scripts.remove(used_script)

    if not OPENROUTER_API_KEY:
        print("⚠️ OPENROUTER_API_KEY가 설정되어 있지 않습니다. 비상 스크립트 업데이트를 건너뜁니다.")
        save_list_to_file(EMERGENCY_FILE, scripts)
        return

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
    prompt = "Generate 10 powerful, viral 20-word dark psychology scripts for Instagram Reels. One per line. No numbers."

    for model in AI_MODELS:
        try:
            time.sleep(2)
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            text = safe_extract_text_from_openai_response(resp)
            if not text:
                continue
            new_list = [line.strip().replace('"', '') for line in text.split("\n") if line.strip()]
            if new_list:
                combined = list(dict.fromkeys(scripts + new_list))  # 순서 보존, 중복 제거
                save_list_to_file(EMERGENCY_FILE, combined)
                print(f"✅ 비상 대본 리스트 보충 완료 ({model})")
                return
        except Exception as e:
            print(f"⚠️ update_emergency_scripts: 모델 {model} 시도 중 예외: {e}")
            continue
    # 모든 모델 실패 시 기존 파일은 유지
    save_list_to_file(EMERGENCY_FILE, scripts)
    print("⚠️ 모든 모델 실패, 비상 스크립트 리스트는 변경되지 않았습니다.")

def update_topics_list(used_topic):
    if not OPENROUTER_API_KEY:
        print("⚠️ OPENROUTER_API_KEY가 설정되어 있지 않습니다. 주제 업데이트를 건너뜁니다.")
        return

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
    topics = get_list_from_file(TOPIC_FILE, ["Wealth psychology"])
    if used_topic in topics:
        topics.remove(used_topic)

    prompt = f"Based on {used_topic}, generate 10 new Instagram Reel topics about dark psychology and wealth. Newlines only."

    for model in AI_MODELS:
        try:
            time.sleep(1)
            resp = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}])
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
            print(f"⚠️ update_topics_list: 모델 {model} 예외: {e}")
            continue
    print("⚠️ 모든 모델 실패: 주제 리스트 업데이트하지 못함.")

def get_best_sales_script(selected_topic, max_attempts_per_model=2):
    """AI 대본 생성: 모델을 순회하면서 성공하면 반환. 실패 시 emergency에서 랜덤 선택."""
    if not OPENROUTER_API_KEY:
        print("⚠️ OPENROUTER_API_KEY가 설정되어 있지 않습니다. 비상 대본 사용.")
        e_scripts = get_list_from_file(EMERGENCY_FILE, ["The 1% don't sleep until the job is done."])
        return random.choice(e_scripts), True

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
    prompt_content = f"Topic: {selected_topic}\nCreate a powerful 20-word dark psychology script for an Instagram Reel. No intro. Provide exactly one line."

    print("🤖 AI 대본 생성 시도 중...")
    for model in AI_MODELS:
        for attempt in range(max_attempts_per_model):
            try:
                time.sleep(2 + attempt)  # 재시도 시 약간의 대기
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt_content}],
                    # timeout 등 필요하면 추가
                )
                script = safe_extract_text_from_openai_response(resp).replace('"', '')
                # 보수적 검증: 너무 짧거나 불완전하면 다음 시도
                if script and len(script) >= 10:
                    # 한 줄만 빼오도록
                    script_line = script.split("\n")[0].strip()
                    if len(script_line) >= 6:
                        print(f"✨ [AI 생성 성공] 사용 모델: {model}")
                        return script_line, False
            except Exception as e:
                print(f"⚠️ {model} 모델 생성 실패 (시도 {attempt+1}): {e}")
                # 다음 시도 또는 모델로 넘어감
                continue

    print("🆘 [AI 생성 실패] 모든 AI 모델이 응답하지 않습니다. 비상 대본을 사용합니다.")
    e_scripts = get_list_from_file(EMERGENCY_FILE, ["The 1% don't sleep until the job is done."])
    return random.choice(e_scripts), True

# ---------------- 파일 호스팅(임시 공개 URL 만들기) ----------------
def upload_to_0x0(file_path, max_attempts=3):
    """
    0x0.st API에 업로드 (간단). 실패하면 None 반환.
    """
    url = "https://0x0.st"
    for attempt in range(max_attempts):
        try:
            with open(file_path, "rb") as f:
                files = {'file': (os.path.basename(file_path), f)}
                r = requests.post(url, files=files, timeout=60)
            if r.status_code in (200,201) and r.text.strip().startswith("http"):
                return r.text.strip()
            else:
                print(f"⚠️ 0x0.st 업로드 실패({r.status_code}): {r.text}")
        except Exception as e:
            print(f"⚠️ 0x0.st 업로드 예외: {e}")
        time.sleep(2 * (attempt + 1))
    return None

def upload_to_transfersh(file_path, max_attempts=3):
    """
    transfer.sh에 PUT으로 업로드 시도. 실패하면 None 반환.
    """
    for attempt in range(max_attempts):
        try:
            url = f"https://transfer.sh/{os.path.basename(file_path)}"
            with open(file_path, "rb") as f:
                r = requests.put(url, data=f, timeout=120)
            if r.status_code in (200,201):
                return r.text.strip()
            else:
                print(f"⚠️ transfer.sh 업로드 실패({r.status_code}): {r.text}")
        except Exception as e:
            print(f"⚠️ transfer.sh 업로드 예외: {e}")
        time.sleep(2 * (attempt + 1))
    return None

def upload_video_and_get_public_url(file_path):
    """
    순차적으로 외부 호스팅에 업로드 시도하여 공개 URL을 반환.
    (0x0.st 우선, 실패 시 transfer.sh)
    """
    print("🔼 영상 업로드: 0x0.st 시도...")
    url = upload_to_0x0(file_path)
    if url:
        print("🔗 업로드 성공:", url)
        return url
    print("🔼 0x0.st 실패 — transfer.sh 시도...")
    url = upload_to_transfersh(file_path)
    if url:
        print("🔗 업로드 성공:", url)
        return url
    print("❌ 모든 공개 호스팅 업로드 실패.")
    return None

# ---------------- Instagram 업로드 ----------------
def post_to_instagram(video_url, caption, api_version="v19.0"):
    """
    Instagram Graph API를 사용해 업로드.
    video_url은 공개적으로 Facebook 서버가 접근 가능해야 함.
    1) media container 생성 (/account/media)
    2) 처리가 완료될 때까지 대기(poll)
    3) /account/media_publish로 publish
    """
    if not ACCESS_TOKEN or not ACCOUNT_ID:
        print("❌ INSTAGRAM_ACCESS_TOKEN 또는 INSTAGRAM_ACCOUNT_ID가 설정되어 있지 않습니다.")
        return False

    print(f"📤 인스타그램 릴스 업로드 시도... video_url={video_url}")

    post_url = f"https://graph.facebook.com/{api_version}/{ACCOUNT_ID}/media"
    payload = {
        'media_type': 'VIDEO',  # 일반적으로 ACCEPTS 'VIDEO' (Reels 별도 권한 필요할 수 있음)
        'video_url': video_url,
        'caption': caption,
        'access_token': ACCESS_TOKEN
    }

    try:
        r = requests.post(post_url, data=payload, timeout=30)
        try:
            res = r.json()
        except Exception:
            res = {"raw_text": r.text}
        print("▶ container create response:", res)
        if r.status_code != 200 and "id" not in res:
            print(f"❌ 컨테이너 생성 실패 (HTTP {r.status_code}): {r.text}")
            return False

        creation_id = res.get("id")
        if not creation_id:
            print("❌ 컨테이너 생성 응답에 id가 없습니다.")
            return False

        # Polling: container 상태 확인 (최대 타임아웃)
        print("⏳ 인스타그램 서버 처리 대기 및 상태 확인 중...")
        status_url = f"https://graph.facebook.com/{api_version}/{creation_id}"
        params = {'fields': 'status_code,progress,video_id', 'access_token': ACCESS_TOKEN}
        total_wait = 0
        max_wait = 300  # 최대 5분
        poll_interval = 5
        while total_wait < max_wait:
            rr = requests.get(status_url, params=params, timeout=30)
            try:
                status_res = rr.json()
            except Exception:
                status_res = {"raw_text": rr.text}
            if rr.status_code == 200:
                # status_code가 있으면 확인 (Graph API 문서에 따라 필드가 다를 수 있음)
                # 예: status_code == 'FINISHED' 또는 progress 100
                prog = status_res.get("progress")
                st = status_res.get("status_code") or status_res.get("status")
                print("▶ 상태 조회:", status_res)
                if st and (str(st).upper() in ("FINISHED","PUBLISHED") or (isinstance(st, str) and "finished" in st.lower())):
                    break
                if prog and int(prog) >= 100:
                    break
            else:
                print("⚠️ 상태 조회 실패:", rr.status_code, rr.text)
            time.sleep(poll_interval)
            total_wait += poll_interval

        # publish
        publish_url = f"https://graph.facebook.com/{api_version}/{ACCOUNT_ID}/media_publish"
        r_pub = requests.post(publish_url, data={'creation_id': creation_id, 'access_token': ACCESS_TOKEN}, timeout=30)
        try:
            pub_res = r_pub.json()
        except Exception:
            pub_res = {"raw_text": r_pub.text}
        print("▶ publish response:", pub_res)
        if r_pub.status_code == 200 and 'id' in pub_res:
            print("🎉 🎉 인스타그램 릴스 업로드 최종 성공! 게시물 ID:", pub_res.get("id"))
            return True
        else:
            print(f"❌ 최종 발행 실패 (HTTP {r_pub.status_code}): {r_pub.text}")
            return False

    except Exception as e:
        print("❌ API 요청 중 오류:", e)
        traceback.print_exc()
        return False

# ---------------- 메인 로직 ----------------
def run_reels_bot():
    # 사전 체크
    if not os.path.exists("background.mp4"):
        print("❌ background.mp4 파일이 없습니다. 같은 디렉터리에 background.mp4를 두세요.")
        return

    topics = get_list_from_file(TOPIC_FILE, ["Dark psychology of wealth"])
    selected_topic = random.choice(topics)
    print(f"🎯 선택된 주제: {selected_topic}")

    script, is_emergency = get_best_sales_script(selected_topic)
    final_caption = f"{script}\n\n{MENTIONS}\n\n{HASHTAGS}"
    # 영상 제작
    try:
        print("🎬 영상 편집 시작...")
        video = VideoFileClip("background.mp4").subclip(0, 8).fx(vfx.colorx, 0.25)
        txt = TextClip(script, fontsize=45, color='white', size=(int(video.w * 0.85), None),
                       font='DejaVu-Sans-Bold', method='caption', align='center',
                       interline=12, stroke_color='black', stroke_width=1.5).set_duration(8).set_pos('center')

        final = CompositeVideoClip([video, txt])
        final_video_name = "reels_video.mp4"
        final.write_videofile(final_video_name, fps=24, codec="libx264", audio=False, threads=2)
    except Exception as e:
        print("❌ 영상 제작 중 오류:", e)
        traceback.print_exc()
        return

    # 업로드: 외부 공개 URL 마련 → Instagram API 호출
    public_url = upload_video_and_get_public_url(final_video_name)
    if not public_url:
        print("❌ 공개 URL 생성 실패 — 업로드 중단.")
        return

    success = post_to_instagram(public_url, final_caption)
    # 사후 처리
    try:
        if success:
            if is_emergency:
                update_emergency_scripts(used_script=script)
            else:
                update_topics_list(used_topic=selected_topic)
                update_emergency_scripts()
        else:
            print("⚠️ 업로드 실패: 비상 대본을 업데이트하거나 로그를 확인하세요.")
            # 실패 시 emergency 리스트 보충 시도
            update_emergency_scripts()
    except Exception as e:
        print("⚠️ 사후 처리 중 오류:", e)

if __name__ == "__main__":
    run_reels_bot()