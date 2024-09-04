import os
from openai import OpenAI
from notion_client import Client
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# 환경 변수에서 API 키 및 데이터베이스 ID 불러오기
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
DATABASE_ID = os.getenv('NOTION_DATABASE_ID')

# OpenAI 클라이언트 설정
client = OpenAI(api_key=OPENAI_API_KEY)

# 노션 API 클라이언트 설정
notion = Client(auth=NOTION_API_KEY)

def extract_youtube_video_id(youtube_url):
    """
    유튜브 URL에서 비디오 ID를 추출
    """
    if "v=" in youtube_url:
        return youtube_url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in youtube_url:
        return youtube_url.split("youtu.be/")[1]
    else:
        raise ValueError("Invalid YouTube URL")

def get_transcript(video_id):
    """
    유튜브 비디오 ID에서 영어 자막을 추출
    """
    transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
    transcript_text = ' '.join([entry['text'] for entry in transcript_list])
    return transcript_text

def translate_and_format_text(text):
    """
    OpenAI GPT를 사용해 텍스트를 자연스럽게 한국어로 번역하고, 노션에 적합한 형식으로 정리
    """
    prompt = (
        f"당신은 20년차 컴퓨터 과학 및 프로그래밍 전문가입니다."
        "다음 문서를 한국어로 자연스럽게 번역해 주시되, 노션에 적합한 형식으로 깔끔하게 정리해 주세요. "
        "1. 문서의 주요 내용과 섹션을 명확하게 구분하고, 제목과 소제목을 사용하여 구조화해 주세요. "
        "2. 각 섹션은 필요한 경우 체크리스트, 표, 태그 등 노션의 다양한 기능을 활용하여 정리해 주시면 좋겠습니다. "
        "3. 문서의 각 부분은 논리적이고 일관되게 배열해 주세요."
        "4. 또한 세부적인 내용을 너무 요약하지말고 직관적으로 개념을 알 수 있게 자세히 써주세요.\n\n"
        f"{text}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2048,
            temperature=0.5
        )
        formatted_text = response.choices[0].message.content.strip()
        return formatted_text
    except Exception as e:
        print(f"번역 중 오류 발생: {e}")
        return None

def split_text(text, max_length=2000):
    """
    긴 텍스트를 지정된 최대 길이로 나누는 함수
    """
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]

def markdown_to_notion_blocks(markdown_text):
    """
    마크다운 텍스트를 노션 블록 형식으로 변환
    """
    blocks = []
    lines = markdown_text.split('\n')
    
    for line in lines:
        if line.startswith('# '):  # h1
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"text": {"content": line[2:]}}]
                }
            })
        elif line.startswith('## '):  # h2
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": line[3:]}}]
                }
            })
        elif line.startswith('### '):  # h3
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"text": {"content": line[4:]}}]
                }
            })
        elif line.startswith('- '):  # 목록
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"text": {"content": line[2:]}}]
                }
            })
        elif line.startswith('1. '):  # 번호 매기기 목록
            blocks.append({
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [{"text": {"content": line[3:]}}]
                }
            })
        elif line.strip() == '':  # 빈 줄은 패스
            continue
        else:  # 일반 텍스트
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": line}}]
                }
            })
    return blocks

def upload_to_notion(title, content):
    """
    노션에 번역된 자막을 업로드
    """
    if not content:
        content = "No content available"  # 빈 내용에 대한 기본값 설정

    # 긴 텍스트를 나누기
    chunks = split_text(content)
    
    for idx, chunk in enumerate(chunks):
        # 마크다운 포맷을 노션 블록으로 변환
        notion_blocks = markdown_to_notion_blocks(chunk)

        new_page = {
            "parent": {"database_id": DATABASE_ID},
            "properties": {
                "title": [
                    {
                        "text": {
                            "content": f"{title} - Part {idx + 1}"
                        }
                    }
                ]
            },
            "children": notion_blocks
        }

        try:
            notion.pages.create(**new_page)
            print(f"노션에 성공적으로 업로드되었습니다: {title} - Part {idx + 1}")
        except Exception as e:
            print(f"노션 업로드 중 오류 발생: {e}")

def main(youtube_url):
    try:
        # 1. 유튜브 비디오 ID 추출
        video_id = extract_youtube_video_id(youtube_url)

        # 2. 영어 자막 추출
        transcript = get_transcript(video_id)

        # 3. 자막을 한국어로 번역하고 포매팅
        formatted_transcript = translate_and_format_text(transcript)

        # 4. 노션에 업로드 (노션 페이지 제목은 비디오 ID로)
        if formatted_transcript:
            upload_to_notion(f"Translation of {video_id}", formatted_transcript)
        else:
            print("번역 결과가 없습니다.")

    except Exception as e:
        print(f"오류 발생: {e}")

# 유튜브 URL 입력
youtube_url = input("유튜브 URL을 입력하세요: ")
main(youtube_url)