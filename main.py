import os
from openai import OpenAI
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import moviepy.video.fx.all as vfx # fx 효과를 위한 추가

def get_best_free_script():
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    # 1순위 모델 이름을 더 정확한 명칭으로 수정했습니다.
    models = [
        "google/gemini-flash-1.5-8b",
        "meta-llama/llama-3.3-70b-instruct:free",
        "qwen/qwen-2.5-72b-instruct:free"
    ]

    for model_name in models:
        try:
            print(f"[{model_name}] 모델 사용 시도 중...")
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "user", "content": "Write a 1-sentence dark psychology quote about human nature. Max 80 chars."}
                ],
                timeout=20
            )
            script = response.choices[0].message.content.strip()
            if script:
                print(f"✅ 성공: {model_name}")
                return script
        except Exception as e:
            print(f"⚠️ {model_name} 실패: {e}")
            continue
    return None

def run_reels_bot():
    script = get_best_free_script()
    if not script:
        print("❌ 모든 모델 실패")
        return

    if not os.path.exists("background.mp4"):
        print("❌ background.mp4 없음")
        return

    try:
        print(f"🎬 영상 제작 시작: {script}")
        # 에러 수정: .colorx(0.3) 대신 .fx(vfx.colorx, 0.3) 사용
        video = VideoFileClip("background.mp4").subclip(0, 5).fx(vfx.colorx, 0.3)
        
        txt = TextClip(script, fontsize=45, color='white', size=(video.w*0.8, None), 
                       font='DejaVu-Sans-Bold', method='caption', stroke_color='black', stroke_width=1).set_duration(5).set_pos('center')
        
        final = CompositeVideoClip([video, txt])
        final.write_videofile("final_reels.mp4", fps=24, codec="libx264", audio=False)
        print("--- ★ 영상 제작 완료! ★ ---")
    except Exception as e:
        print(f"❌ 영상 편집 에러: {e}")

if __name__ == "__main__":
    run_reels_bot()
