from flask import Flask, request, jsonify
from flask_cors import CORS  # CORS import
import openai
from openai import OpenAIError

app = Flask(__name__)
CORS(app)  # CORS 활성화

# OpenAI API 키 설정
openai.api_key = '-'

@app.route('/api/recommendation', methods=['POST'])
def recommendation():
    try:
        # POST 요청에서 데이터 받기
        data = request.json
        print(f"Received data: {data}")  # 데이터를 제대로 받는지 확인
        user_age = data.get('age')
        dislikes = data.get('dislikes', [])
        allergies = data.get('allergies', [])

        # 데이터 유효성 검사
        if not user_age or not isinstance(dislikes, list) or not isinstance(allergies, list):
            print("Invalid input data")  # 유효성 검사 실패 로그
            return jsonify({'error': 'Invalid input data'}), 400

        dislikes_text = ', '.join(dislikes) if dislikes else '없음'
        allergies_text = ', '.join(allergies) if allergies else '없음'

        # OpenAI API로 채팅 응답 생성 (최신 API 방식)
        print("Sending request to OpenAI API")  # OpenAI API 호출 전 로그
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 아이들의 맞춤형 식단을 제공하는 헬퍼입니다."
                },
                {
                    "role": "user",
                    "content": (
                        f"나이가 {user_age}세인 아이의 맞춤 식단 3개를 추천해주세요. "
                        f"이 아이는 {dislikes_text}을/를 싫어하고, {allergies_text}에 알러지가 있습니다. "
                        "각 식단에 대해 재료, 칼로리, 탄수화물, 단백질, 지방, 비타민을 포함해 주세요. "
                        "한국인을 위한 추천입니다. 한국인이 자주 먹는 재료, 음식으로 구성해주고, 아이의 연령대를 고려해주세요. 한번더 강조하지만, 아이의 연령대가 반드시 고려되어야 합니다."
                        "그리고 메뉴마다 편식 음식, 알러지에서 어떤 점을 대체했는지 (대체 영양소 사용 등) 간단하게 한줄로 설명해주세요. 이때 반드시 description 형식을 지켜서 써주세요. 형식은 가지,생선 ☞ 대체한 재료의 이름 (~~ 영양소 대체) 이래야 합니다. 이때, 대체하지 않은 재료는 굳이 안쓰셔도 됩니다."
                        "응답을 다음 JSON 형식으로 제공해 주세요: "
                        '{"meal_1": {"name": "식단 이름", "ingredients": ["재료 1", "재료 2"], "calories": 500, "description": "가지,생선 ☞ 대체한 재료의 이름 (~~ 영양소 대체)",'
                        '"nutrients": {"carbs": "50g", "protein": "20g", "fat": "10g", "vitamins": "비타민 정보"}, '
                        '"difficulty": "쉬움", "cooking_time": "30분", "recipe_link": "https://example.com/recipe"}, '
                        '"meal_2": {...}, "meal_3": {...}}'

                    )
                }
            ]
        )
        print("OpenAI API response received")  # 응답 받은 후 로그

        ai_reply = response['choices'][0]['message']['content']
        return jsonify({'recommendation': ai_reply}), 200, {'Content-Type': 'application/json; charset=utf-8'}

    except OpenAIError as e:
        print(f"OpenAI API error: {str(e)}")  # OpenAI API 오류 로그
        return jsonify({'error': f"OpenAI API error: {str(e)}"}), 500
    except Exception as e:
        print(f"General error: {str(e)}")  # 일반적인 오류 로그
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
