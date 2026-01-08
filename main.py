import os
from openai import OpenAI
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import moviepy.video.fx.all as vfx

def get_best_sales_script():
    """
    마케팅 심리학을 적용하여 아마존 상품 클릭을 유도하는 대본 생성
    """
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    # 모델 리스트 (가장 똑똑한 모델 순서)
    models = [
        "openai/gpt-4o-mini", 
        "google/gemini-2.0-flash-exp:free",
        "meta-llama/llama-3.3-70b-instruct:free"
    ]

    # 세일즈를 위한 고도화된 프롬프트
    # '길이 제한'을 명시적으로 빼고, 자연스러운 세일즈 흐름을 강조했습니다.
    prompt_content = """
    Create a powerful, 3-part psychological sales script for an Instagram Reel. 
    The goal is to trigger intense curiosity and urge the viewer to check the 'Success Secret' link in my bio (Amazon Affiliate).

    Structure:
    1. Hook: Start with a hard-hitting truth about why most people never get rich.
    2. Insight: Explain the hidden psychological advantage or secret tool that the top 1% use.
    3. Call to Action: Direct them to the "Secret Blueprint" or "Elite Toolkit" in my bio link to change their life today.

    Style Guidelines:
    - Language: English
    - Tone: Authoritative, Dark, Wealth-focused, and slightly Mysterious.
    - Format: Use newlines (\\n) between each part. 
    - No strict character limit, but keep it punchy and impactful for a 7-second video.
    - Example: 
      Most people trade their time for a paycheck.\\nThe 1% trade their mindset for an empire.\\nAccess the elite blueprint in my bio.
    """

    for model_name in models:
        try:
            print(f"[{model_name}] 대본 생성 중...")
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a master of psychological copywriting and wealth attraction."},
                    {"role": "user", "content": prompt_content}
                ],
                timeout=30
            )
            script = response.choices[0].message.content.strip()
            if script:
                # 불필요한 따옴표 제거
                script = script.replace('"', '')
                print(f"✅ 대본 생성 성공 ({model_name})")
                return script
        except Exception as e:
            print(f"⚠️ {model_name} 시도 중 에러: {e}")
            continue
    return None

def run_reels_bot():
    script = get_best_sales_script()
    if not script:
        print("❌ 대본 생성 실패: 모든 모델이 응답하지 않습니다.")
        return

    if not os.path.exists("background.mp4"):
        print("❌ background.mp4 파일이 없습니다. 영상을 준비해주세요.")
        return

    try:
        print(f"🎬 영상 제작 시작:\n{script}")
        
        # 1. 배경 영상 로드 및 어둡게 처리 (글자가 잘 보이도록)
        # 세일즈 문구가 길어질 수 있으므로 길이를 7~8초로 설정
        video = VideoFileClip("background.mp4").subclip(0, 8).fx(vfx.colorx, 0.25)
        
        # 2. 자막 설정 (줄바꿈 반영 및 중앙 정렬)
        txt = TextClip(
            script, 
            fontsize=50,             # 글자 크기
            color='white', 
            size=(video.w * 0.9, None), # 화면 너비의 90% 사용
            font='DejaVu-Sans-Bold', 
            method='caption', 
            align='center',          # 텍스트 중앙 정렬
            interline=15,            # 줄 간격 넉넉히
            stroke_color='black', 
            stroke_width=2           # 가독성을 위한 외곽선
        ).set_duration(8).set_pos('center')
        
        # 3. 영상 합성 및 출력
        final = CompositeVideoClip([video, txt])
        output_name = "final_reels.mp4"
        final.write_videofile(output_name, fps=24, codec="libx264", audio=False)
        
        print(f"--- ★ 제작 완료: {output_name} ★ ---")
        
    except Exception as e:
        print(f"❌ 영상 편집 과정에서 에러 발생: {e}")

if __name__ == "__main__":
    run_reels_bot()
