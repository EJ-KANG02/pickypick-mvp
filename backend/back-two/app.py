from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import requests
from openai import OpenAIError
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# OpenAI API 키 설정
openai.api_key = '-'

# 만개의 레시피에서 레시피 세부 정보 크롤링
def fetch_recipe_from_mangae(recipe_name):
    search_url = f"https://www.10000recipe.com/recipe/list.html?q={recipe_name}"
    print(f"Searching for recipe with name: {recipe_name}")
    search_response = requests.get(search_url)
    soup = BeautifulSoup(search_response.text, 'html.parser')

    # 가장 첫 번째 검색 결과를 선택
    recipe_links = soup.select('.common_sp_list_ul .common_sp_list_li a.common_sp_link')
    if recipe_links:
        first_recipe_url = "https://www.10000recipe.com" + recipe_links[0]['href']
        print(f"Found recipe link: {first_recipe_url}")

        # 해당 레시피 상세 페이지 크롤링
        recipe_response = requests.get(first_recipe_url)
        recipe_soup = BeautifulSoup(recipe_response.text, 'html.parser')

        ingredients = [ing.get_text(strip=True) for ing in recipe_soup.select('.ingre_list_name')]

        # `difficulty`와 `cooking_time` 가져오기
        difficulty_element = recipe_soup.select_one('.view2_summary_info .view2_summary_info3')
        cooking_time_element = recipe_soup.select_one('.view2_summary_info .view2_summary_info2')

        # 요소가 존재할 때만 `get_text()` 호출
        difficulty = difficulty_element.get_text(strip=True) if difficulty_element else "정보 없음"
        cooking_time = cooking_time_element.get_text(strip=True) if cooking_time_element else "정보 없음"

        print(f"Fetched ingredients: {ingredients}")
        print(f"Fetched difficulty: {difficulty}")
        print(f"Fetched cooking time: {cooking_time}")

        return {
            "recipe_link": first_recipe_url,
            "ingredients": ingredients,
            "difficulty": difficulty,
            "cooking_time": cooking_time
        }
    else:
        print("No recipe found on 만개의레시피")
    return None


# 카카오톡 챗봇의 Webhook 엔드포인트
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        # 사용자 발화 내용 가져오기
        user_request = data['userRequest']
        utterance = user_request.get('utterance', '').strip()

        # 현재 블록에서 저장된 변수들 가져오기
        bot_context = data.get('action', {}).get('params', {})
        age = bot_context.get('age')
        dislikes = bot_context.get('dislikes')
        allergies = bot_context.get('allergies')

        # 사용자의 입력 단계에 따라 처리 분기
        # 예를 들어, age, dislikes, allergies 중 없는 값이 있으면 해당 값을 물어봅니다.
        if not age:
            response_text = "아이의 나이는 몇 살인가요?"
            return make_response(response_text)
        if not dislikes:
            response_text = "아이의 편식하는 음식을 알려주세요. 없으면 '없음'이라고 입력해주세요."
            return make_response(response_text)
        if not allergies:
            response_text = "아이의 알러지 정보를 알려주세요. 없으면 '없음'이라고 입력해주세요."
            return make_response(response_text)

        # 모든 정보를 입력받았으므로 추천 식단을 생성합니다.
        # dislikes와 allergies를 리스트로 변환
        dislikes_list = [item.strip() for item in dislikes.split(',')]
        allergies_list = [item.strip() for item in allergies.split(',')]

        # OpenAI API 호출
        print("Sending request to OpenAI API")
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
                        f"나이가 {age}세인 아이의 맞춤 식단 1개를 추천해주세요. "
                        f"이 아이는 {', '.join(dislikes_list)}을/를 싫어하고, {', '.join(allergies_list)}에 알러지가 있습니다. "
                        "한국인에게 추천하는 식단이므로 한국인이 자주 먹는 식단으로 구성해주세요. "
                        "한 식단에는 하나의 음식만 추천해주세요. "
                        "편식하거나 알러지 있는 재료의 영양분을 대체할 수 있는 재료가 주 재료로 들어간 음식이어야 합니다. "
                        "식단에 대해 재료, 칼로리, 탄수화물, 단백질, 지방, 비타민을 포함해 주세요. "
                        "그리고 메뉴에서 편식 음식, 알러지에서 어떤 점을 대체했는지 (대체 영양소 사용 등) 간단하게 한줄로 설명해주세요. "
                        "응답을 다음 JSON 형식으로 제공해 주세요: "
                        '{"name": "식단 이름", "description": "설명", '
                        '"nutrients": {"calories": "300kcal", "carbs": "50g", "protein": "20g", "fat": "10g", "vitamins": "비타민 정보"}}'
                    )
                }
            ]
        )
        print("OpenAI API response received")

        ai_reply = response['choices'][0]['message']['content']
        meal_data = eval(ai_reply)

        recipe_name = meal_data["name"]
        print(f"Fetching recipe details for: {recipe_name}")

        # 만개의레시피에서 레시피 정보 검색
        recipe_details = fetch_recipe_from_mangae(recipe_name)
        if recipe_details:
            detailed_recommendation = {
                "name": recipe_name,
                "description": meal_data["description"],
                "nutrients": meal_data["nutrients"],
                "ingredients": recipe_details["ingredients"],
                "difficulty": recipe_details["difficulty"],
                "cooking_time": recipe_details["cooking_time"],
                "recipe_link": recipe_details["recipe_link"]
            }
        else:
            detailed_recommendation = {
                "name": recipe_name,
                "description": meal_data["description"],
                "nutrients": meal_data["nutrients"],
                "ingredients": "레시피 정보를 찾을 수 없습니다.",
                "difficulty": "정보 없음",
                "cooking_time": "정보 없음",
                "recipe_link": "링크 없음"
            }

        # 응답 생성
        response_text = (
            f"추천 식단: {detailed_recommendation['name']}\n"
            f"설명: {detailed_recommendation['description']}\n"
            f"난이도: {detailed_recommendation['difficulty']} | 요리 시간: {detailed_recommendation['cooking_time']}\n"
            f"재료: {', '.join(detailed_recommendation['ingredients'])}\n"
            f"칼로리: {detailed_recommendation['nutrients'].get('calories', '정보 없음')}\n"
            f"탄수화물: {detailed_recommendation['nutrients'].get('carbs', '정보 없음')}\n"
            f"단백질: {detailed_recommendation['nutrients'].get('protein', '정보 없음')}\n"
            f"지방: {detailed_recommendation['nutrients'].get('fat', '정보 없음')}\n"
            f"비타민: {detailed_recommendation['nutrients'].get('vitamins', '정보 없음')}\n"
            f"레시피 보기: {detailed_recommendation['recipe_link']}"
        )

        return make_response(response_text)

    except OpenAIError as e:
        print(f"OpenAI API error: {str(e)}")
        return make_response("죄송합니다. 식단 추천 중 오류가 발생했습니다.")
    except Exception as e:
        print(f"General error: {str(e)}")
        return make_response("죄송합니다. 처리 중 오류가 발생했습니다.")

def make_response(text):
    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": text
                    }
                }
            ]
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
