import os
import random  # 주제 랜덤 선택을 위해 추가
from openai import OpenAI
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import moviepy.video.fx.all as vfx

def get_best_sales_script():
    """
    마케팅 심리학 및 무작위성 로직을 적용하여 매번 다른 세일즈 대본 생성
    """
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    # 1. 중복 방지를 위한 랜덤 주제 리스트
    topics = [
        "Dark psychology of wealth",
        "The 1% secret morning routine",
        "Why 99% of people stay poor",
        "Elite mindset vs Employee mindset",
        "The forbidden rules of money",
        "Social engineering for success",
        "Stoic approach to financial freedom",
        "The psychological cost of being average"
    ]
    selected_topic = random.choice(topics)

    # 모델 리스트
    models = [
        "openai/gpt-4o-mini", 
        "google/gemini-2.0-flash-exp:free",
        "meta-llama/llama-3.3-70b-instruct:free"
    ]

    # 세일즈 문구 생성을 위한 고도화된 프롬프트
    prompt_content = f"""
    Topic: {selected_topic}
    Create a powerful, 3-part psychological sales script for an Instagram Reel. 
    The goal is to trigger intense curiosity for a 'Success Secret' link in my bio.

    Structure:
    1. Hook: A shocking truth about wealth or why most people are stuck.
    2. Insight: A hidden psychological edge that the elite use.
    3. Call to Action: Tell them to grab the 'Secret Blueprint' in my bio link.

    Style Guidelines:
    - Tone: Authoritative, Dark, and Urgent.
    - Format: Use newlines (\\n) between each part. 
    - Originality: DO NOT use clichés. Be provocative.
    - Max 25 words total.
    """

    for model_name in models:
        try:
            print(f"[{model_name}] '{selected_topic}' 주제로 대본 생성 중...")
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a master of psychological copywriting. You never repeat the same advice twice."},
                    {"role": "user", "content": prompt_content}
                ],
                temperature=0.9,  # 창의성 수치를 높여 중복 방지 (0.0~1.0)
                timeout=30
            )
            script = response.choices[0].message.content.strip()
            if script:
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
        print("❌ 대본 생성 실패")
        return

    if not os.path.exists("background.mp4"):
        print("❌ background.mp4 파일 없음")
        return

    try:
        print(f"🎬 영상 제작 시작:\n{script}")
        
        # 1. 배경 영상 로드 (8초)
        video = VideoFileClip("background.mp4").subclip(0, 8).fx(vfx.colorx, 0.25)
        
        # 2. 자막 설정 (줄바꿈 반영 및 중앙 정렬)
        txt = TextClip(
            script, 
            fontsize=50,
            color='white', 
            size=(video.w * 0.9, None), 
            font='DejaVu-Sans-Bold', 
            method='caption', 
            align='center',
            interline=15,
            stroke_color='black', 
            stroke_width=2
        ).set_duration(8).set_pos('center')
        
        # 3. 영상 합성 및 출력
        final = CompositeVideoClip([video, txt])
        output_name = "final_reels.mp4"
        final.write_videofile(output_name, fps=24, codec="libx264", audio=False)
        
        print(f"--- ★ 제작 완료: {output_name} ★ ---")
        
    except Exception as e:
        print(f"❌ 영상 편집 에러: {e}")

if __name__ == "__main__":
    run_reels_bot()
