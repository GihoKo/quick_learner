# quick_learner
## 설명
'딸깍'으로 유튜브 영상의 내용을 GPT로 번역하고, 마크다운으로 포메팅 후 노션으로 저장

## 요구 사항
- python
- Notion API와 Notion Database 연동 및 Notion API Key
- OpenAI API Key

## 설치
### 저장소 클론
```
git clone <저장소>
```
### 가상 환경 설정
```cmd
python -m venv env
```
### 가상 환경 활성화
```cmd
.\env\Scripts\activate
```
### 패키지 설치
```
pip install -r requirements.txt
```

## 사용법
### main.py 실행
```
python main.py
```
이후 youtube URI 넣으면 끝

## 추가 내용 및 주의 사항
### GPT에 인격 설정 및 정리 방향 제시
![image](https://github.com/user-attachments/assets/bbf2e656-371f-4bab-89eb-f20b5d01e4e2)
알잘딱하게 쓰기

### OpenAI API와 GPT 결제는 독립적
- OpenAI 결제를 해야합니다.

### 터미널
- 터미널은 cmd 기준입니다.
