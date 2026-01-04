import os
from openai import OpenAI
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

def get_best_free_script():
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    # 🌟 [2026년 기준] 성능 순위별 무료 모델 리스트
    # 1. Gemini 1.5 Flash (가장 범용적이고 영리함)
    # 2. Llama 3.3 70B Instruct (오픈소스 최강급 성능)
    # 3. Qwen 2.5 72B (창의적이고 방대한 지식)
    # 4. MiMo-V2-Flash (최신 무료 고성능 모델)
    models = [
        "google/gemini-flash-1.5-exp:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "qwen/qwen-2.5-72b-instruct:free",
        "xiaomi/mimo-v2-flash:free"
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
            print(f"⚠️ {model_name} 실패 (할당량 초과 또는 에러): {e}")
            continue
            
    return None

def run_reels_bot():
    script = get_best_free_script()
    
    if not script:
        print("❌ 모든 무료 모델의 할당량이 소진되었습니다. 잠시 후 다시 시도하세요.")
        return

    if not os.path.exists("background.mp4"):
        print("❌ background.mp4 파일이 없습니다.")
        return

    try:
        print(f"🎬 영상 제작 시작: {script}")
        video = VideoFileClip("background.mp4").subclip(0, 5).colorx(0.3)
        
        # 자막 설정
        txt = TextClip(script, fontsize=45, color='white', size=(video.w*0.8, None), 
                       font='DejaVu-Sans-Bold', method='caption', stroke_color='black', stroke_width=1).set_duration(5).set_pos('center')
        
        final = CompositeVideoClip([video, txt])
        final.write_videofile("final_reels.mp4", fps=24, codec="libx264", audio=False)
        print("--- ★ 영상 제작 완료! ★ ---")
    except Exception as e:
        print(f"❌ 영상 편집 에러: {e}")

if __name__ == "__main__":
    run_reels_bot()
