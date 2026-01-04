import os
import random
import google.generativeai as genai
from google.cloud import texttospeech
from moviepy.editor import VideoFileClip, TextClip, AudioFileClip, CompositeVideoClip

# 1. 환경 설정 및 보안 키 연결
# GitHub Secrets에 GEMINI_API_KEY가 등록되어 있어야 하고, google_key.json 파일이 저장소에 있어야 합니다.
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_key.json"
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def run_reels_bot():
    print("--- 프로세스 시작: 영어 다크 모티베이션 모드 ---")
    
    # 2. 글로벌 타겟 아이템 및 주제 설정
    items = ["High-purity Maca Supplement", "Zero-Capital Startup Guide", "Luxury Men's Fragrance", "Deep Focus Nootropics"]
    topics = ["Ancient Stoic Wisdom", "Modern Laws of Success", "The Essence of Masculinity", "Habits of the 1%", "The Cost of Greatness"]
    
    item = random.choice(items)
    topic = random.choice(topics)
    
    # 3. 제미나이 AI 대본 생성 (미스터리 & 궁금증 유발)
    model = genai.GenerativeModel('gemini-pro')
    
    # 심리적 트리거와 신비로움을 강조한 영어 프롬프트
    prompt = f"""
    Act as a mysterious, high-status philosophical marketer. 
    Topic: {topic} / Hidden Product: {item}
    
    [Rules]
    1. Start with a heavy, soul-piercing sentence about life and success.
    2. Hint at the secret of '{item}' without naming it. Use metaphors like "the silent edge" or "the unseen ritual."
    3. Make the audience feel a "void" that only this secret can fill.
    4. Tone: Masculine, dark, authoritative, and slow.
    5. Length: Maximum 250 characters.
    6. Language: Powerful English.
    7. Closing: Must end with "The secret is in the bio."
    """
    
    try:
        response = model.generate_content(prompt)
        script = response.text
        print(f"생성된 영어 대본: {script}")
    except Exception as e:
        print(f"대본 생성 실패: {e}")
        return

    # 4. 구글 클라우드 TTS (깊고 웅장한 영어 남성 목소리)
    tts_client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=script)
    
    # en-US-Neural2-J는 신뢰감 있고 깊은 저음의 미국 성인 남성 목소리입니다.
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", 
        name="en-US-Neural2-J", 
        ssml_gender=texttospeech.SsmlVoiceGender.MALE
    )
    
    # 피치(Pitch)를 낮추고 속도(Rate)를 늦춰서 무거운 분위기를 극대화합니다.
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        pitch=-4.0, 
        speaking_rate=0.85
    )
    
    res = tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    with open("voice.mp3", "wb") as out:
        out.write(res.audio_content)

    # 5. MoviePy를 이용한 영상 편집
    # 영상을 어둡게(밝기 40% 수준) 보정하여 묵직한 느낌을 줍니다.
    video = VideoFileClip("background.mp4").subclip(0, 10)
    video = video.fx(lambda v: v.multiply_speed(1)).colorx(0.4) 
    
    audio = AudioFileClip("voice.mp3")
    video = video.set_audio(audio)
    
    # 미니멀한 자막 설정: 회색빛 흰색, 중앙 배치
    txt = TextClip(script, fontsize=30, color='gray90', font='Liberation-Sans-Bold', 
                   method='caption', size=(video.w*0.75, None))
    txt = txt.set_duration(video.duration).set_pos(('center', 'center'))
    
    final = CompositeVideoClip([video, txt])
    
    # 인스타그램 최적화 코덱으로 저장
    final.write_videofile("final_reels.mp4", fps=24, codec="libx264", audio_codec="aac")
    print("--- 영상 제작 성공: final_reels.mp4 생성 완료 ---")

if __name__ == "__main__":
    run_reels_bot()
