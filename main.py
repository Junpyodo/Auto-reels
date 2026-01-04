import os
import random
import google.generativeai as genai
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def run_reels_bot():
    # 현재 위치를 확실히 출력하여 로그에서 확인 가능하게 함
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"현재 실행 디렉토리: {base_dir}")

    model = genai.GenerativeModel('gemini-1.5-flash')
    
    topics = ["Dark psychology to be elite", "Silence as a weapon", "Mastery of attraction"]
    topic = random.choice(topics)
    
    prompt = f"Write a powerful 2-sentence dark psychology quote about {topic}. Max 100 chars. End with 'Secret in bio.'"
    
    try:
        response = model.generate_content(prompt)
        script = response.text.replace('"', '').strip()
        print(f"생성 문구: {script}")
    except Exception as e:
        print(f"AI 실패: {e}")
        return

    # 배경 파일 경로를 절대 경로로 조합
    bg_path = os.path.join(base_dir, "background.mp4")
    if not os.path.exists(bg_path):
        print(f"에러: {bg_path} 파일을 찾을 수 없습니다.")
        return

    try:
        video = VideoFileClip(bg_path).subclip(0, 7).colorx(0.3)
        
        txt = TextClip(script, 
                       fontsize=40, 
                       color='white', 
                       font='DejaVu-Sans-Bold', 
                       method='caption', 
                       size=(video.w*0.8, None)).set_duration(video.duration).set_pos('center').fadein(2.5)
        
        final = CompositeVideoClip([video, txt])
        
        # 저장 경로 역시 절대 경로로 지정
        output_path = os.path.join(base_dir, "final_reels.mp4")
        print(f"저장 시도 경로: {output_path}")
        
        final.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
        print("--- 최종 저장 완료! ---")
    except Exception as e:
        print(f"편집 중 오류: {e}")

if __name__ == "__main__":
    run_reels_bot()
