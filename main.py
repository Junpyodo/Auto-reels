import os
# 🌟 신규 SDK를 불러오는 정확한 방법입니다.
from google import genai
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

def run_reels_bot():
    print("--- 신규 SDK 가동 시작 ---")
    api_key = os.getenv("GEMINI_API_KEY")
    
    # 클라이언트 설정
    client = genai.Client(api_key=api_key)
    
    try:
        print("대본 생성 중...")
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents="Write a short dark psychology quote. 1 sentence."
        )
        script = response.text.strip()
        print(f"생성 문구: {script}")
    except Exception as e:
        print(f"AI 에러 발생: {e}")
        return

    if not os.path.exists("background.mp4"):
        print("에러: background.mp4 파일이 없습니다.")
        return

    try:
        print("영상 편집 중...")
        video = VideoFileClip("background.mp4").subclip(0, 5).colorx(0.3)
        
        # 자막 입히기
        txt = TextClip(script, fontsize=40, color='white', size=(video.w*0.8, None), 
                       font='DejaVu-Sans-Bold', method='caption').set_duration(5).set_pos('center')
        
        final = CompositeVideoClip([video, txt])
        
        print("파일 저장 중...")
        final.write_videofile("final_reels.mp4", fps=24, codec="libx264")
        print("--- ★ 제작 성공 ★ ---")
    except Exception as e:
        print(f"편집 에러: {e}")

if __name__ == "__main__":
    run_reels_bot()
