import os
import random
from openai import OpenAI
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import moviepy.video.fx.all as vfx

def get_best_sales_script():
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    # 기존 심리학 주제 + 새로운 리스트형/습관 주제 통합
    topics = [
        # --- 기존 심리학/전략 테마 ---
        "Dark psychology of wealth and power",
        "Hidden psychological advantages of the 1%",
        "The stoic approach to financial dominance",
        "Social engineering secrets for success",
        "The forbidden rules of money mindset",
        "Why 99% of people stay trapped in the rat race",
        # --- 새로운 리스트/습관/체크리스트 테마 ---
        "3 Habits of Self-Made Millionaires you can start today",
        "The 'Poor vs Rich' Morning Routine comparison",
        "Stop Doing These 3 Things to attract wealth",
        "The 1% Wealth Checklist: Do you have these?",
        "How to Reprogram Your Mind for ultimate success",
        "What schools never taught you about making money",
        "3 Psychological Triggers that make people say YES",
        "The brutal truth about financial freedom"
    ]
    selected_topic = random.choice(topics)

    models = [
        "openai/gpt-4o-mini", 
        "google/gemini-2.0-flash-exp:free",
        "meta-llama/llama-3.3-70b-instruct:free"
    ]

    # 에러 방지를 위해 '딱 1개 세트'와 '단어 수 제한'을 엄격히 적용
    prompt_content = f"""
    Topic: {selected_topic}
    Create ONE powerful 3-line psychological script for an Instagram Reel. 
    Make the viewer desperate to click the link in my bio for the full solution.

    Structure:
    Line 1 (Hook): A shocking truth, a list, or a bold claim.
    Line 2 (Insight): A high-value tip or secret the elite use.
    Line 3 (CTA): Direct them to the 'Secret Blueprint' or 'Guide' in my bio link.

    Constraints:
    - Language: English.
    - Format: Separate each line with a newline (\\n).
    - MAX 25 WORDS total. (Very important to avoid rendering errors)
    - Tone: Dark, Elite, Authoritative.
    - No intro/outro like "Here is your script".
    """

    for model_name in models:
        try:
            print(f"[{model_name}] '{selected_topic}' 주제로 생성 중...")
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a master of high-conversion sales copy. You never repeat yourself."},
                    {"role": "user", "content": prompt_content}
                ],
                temperature=0.9, 
                timeout=30
            )
            script = response.choices[0].message.content.strip()
            if script:
                script = script.replace('"', '')
                # 안전장치: 3줄까지만 자르기
                lines = [l for l in script.split('\n') if l.strip()][:3]
                final_script = "\n".join(lines)
                print(f"✅ 대본 생성 성공")
                return final_script
        except Exception as e:
            print(f"⚠️ {model_name} 에러: {e}")
            continue
    return None

def run_reels_bot():
    script = get_best_sales_script()
    if not script: return

    if not os.path.exists("background.mp4"):
        print("❌ background.mp4 파일이 없습니다.")
        return

    try:
        print(f"🎬 영상 제작 시작:\n{script}")
        
        # 배경 영상 8초 사용
        video = VideoFileClip("background.mp4").subclip(0, 8).fx(vfx.colorx, 0.25)
        
        # 자막 설정 (폰트 크기와 줄간격 최적화)
        txt = TextClip(
            script, 
            fontsize=45, 
            color='white', 
            size=(video.w * 0.85, None), 
            font='DejaVu-Sans-Bold', 
            method='caption', 
            align='center',
            interline=12,
            stroke_color='black', 
            stroke_width=1.5
        ).set_duration(8).set_pos('center')
        
        final = CompositeVideoClip([video, txt])
        final.write_videofile("final_reels.mp4", fps=24, codec="libx264", audio=False)
        print("--- ★ 통합 주제 영상 제작 완료! ★ ---")
        
    except Exception as e:
        print(f"❌ 영상 편집 에러: {e}")

if __name__ == "__main__":
    run_reels_bot()
