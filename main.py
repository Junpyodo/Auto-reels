import os
import random
import datetime
import google.generativeai as genai
from google.cloud import texttospeech
from moviepy.editor import VideoFileClip, TextClip, AudioFileClip, CompositeVideoClip

# 1. 환경 설정 및 보안 키 연결
# GitHub Secrets에 GEMINI_API_KEY라는 이름으로 키를 저장해야 합니다.
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_key.json"
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def run_reels_bot():
    print("--- 작업 시작: 제미나이 모드 ---")
    
    # 2. 판매 타겟 아이템 리스트 (책, 영양제, 돈 버는 법)
    items = [
        "경제적 자유를 위한 필독서 '부의 추월차선'", 
        "남자의 활력을 결정하는 고함량 마카 영양제", 
        "퇴사 후 월 500 벌게 해주는 '무자본 창업 공략집'",
        "집중력을 200% 끌어올리는 뇌 영양제",
        "자면서도 돈이 들어오는 '파이프라인 구축' 비법"
    ]
    item = random.choice(items)
    
    # 3. Gemini를 이용한 카리스마 마케팅 문구 생성
    model = genai.GenerativeModel('gemini-pro')
    prompt = f"""
    당신은 100만 유튜버이자 천재 마케터입니다.
    성공을 열망하는 남성들에게 {item}을 판매해야 합니다.
    시청자의 뒤통수를 때리는 듯한 강력한 동기부여와 함께 80자 이내의 짧고 굵은 대본을 쓰세요.
    말투는 매우 단호하고 카리스마 있어야 합니다.
    마지막 문장은 반드시 '지금 프로필 링크를 확인해.'로 끝내세요.
    """
    
    try:
        response = model.generate_content(prompt)
        script = response.text
        print(f"생성된 대본: {script}")
    except Exception as e:
        print(f"Gemini 생성 실패: {e}")
        return

    # 4. Google Cloud TTS로 음성 생성 (남성 뉴스 읽기 톤)
    tts_client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=script)
    
    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR", 
        name="ko-KR-Neural2-C", # 신뢰감 있는 남성 목소리
        ssml_gender=texttospeech.SsmlVoiceGender.MALE
    )
    
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        pitch=-1.5, # 목소리 톤을 약간 낮춤
        speaking_rate=1.05 # 약간 빠르게
    )
    
    res = tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    
    with open("voice.mp3", "wb") as out:
        out.write(res.audio_content)
    print("음성 생성 완료.")

    # 5. 영상 합성 (MoviePy)
    # 반드시 저장소 메인에 background.mp4 파일이 있어야 합니다.
    bg_path = "background.mp4"
    if not os.path.exists(bg_path):
        print(f"에러: {bg_path} 파일이 없습니다. 영상을 업로드해주세요.")
        return

    video = VideoFileClip(bg_path).subclip(0, 10) # 10초 쇼츠
    audio = AudioFileClip("voice.mp3")
    video = video.set_audio(audio)
    
    # 자막 설정 (화면 80% 너비, 중앙 배치)
    txt = TextClip(script, fontsize=45, color='white', font='Liberation-Sans-Bold', 
                   method='caption', size=(video.w*0.8, None))
    txt = txt.set_duration(video.duration).set_pos('center')
    
    final = CompositeVideoClip([video, txt])
    
    # 최종 파일 저장 (인스타그램 업로드용 libx264 코덱)
    final.write_videofile("final_reels.mp4", fps=24, codec="libx264", audio_codec="aac")
    print("--- 모든 작업 완료: final_reels.mp4 생성됨 ---")

if __name__ == "__main__":
    run_reels_bot()
