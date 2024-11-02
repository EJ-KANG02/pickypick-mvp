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

@app.route('/api/recommendation', methods=['POST'])
def recommendation():
    try:
        data = request.json
        print(f"Received data: {data}")
        user_age = data.get('age')
        dislikes = data.get('dislikes', [])
        allergies = data.get('allergies', [])

        if not user_age or not isinstance(dislikes, list) or not isinstance(allergies, list):
            print("Invalid input data")
            return jsonify({'error': 'Invalid input data'}), 400

        dislikes_text = ', '.join(dislikes) if dislikes else '없음'
        allergies_text = ', '.join(allergies) if allergies else '없음'

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
                        f"나이가 {user_age}세인 아이의 맞춤 식단 3개를 추천해주세요. "
                        f"이 아이는 {dislikes_text}을/를 싫어하고, {allergies_text}에 알러지가 있습니다. "
                        "한국인에게 추천하는 식단이므로 한국인이 자주 먹는 식단으로 구성해주세요."
                        "한 식단에는 하나의 음식만 추천해주세요."
                        "편식하거나 알러지 있는 재료의 영양분을 대체할 수 있는 재료가 주 재료로 들어간 음식이어야 합니다."
                        "각 식단에 대해 재료, 칼로리, 탄수화물, 단백질, 지방, 비타민을 포함해 주세요. "
                        "그리고 메뉴마다 편식 음식, 알러지에서 어떤 점을 대체했는지 (대체 영양소 사용 등) 간단하게 한줄로 설명해주세요. 이때 반드시 description 형식을 지켜서 써주세요. 형식은 편식하는 재료 or 알러지있는 재료 이름 (~~ 영양소 대체) 이래야 합니다."
                        "응답을 다음 JSON 형식으로 제공해 주세요: "
                        '{"meal_1": {"name": "식단 이름", "description": "편식하는 재료 or 알러지 있는 재료 이름 (~~ 영양소 대체)", '
                        '"nutrients": {"calories": "300kcal", "carbs": "50g", "protein": "20g", "fat": "10g", "vitamins": "비타민 정보"}}, '
                        '"meal_2": {...}, "meal_3": {...}}'
                    )
                }
            ]
        )
        print("OpenAI API response received")

        ai_reply = response['choices'][0]['message']['content']
        recommendations = eval(ai_reply)

        detailed_recommendations = {}
        for meal_key, meal_data in recommendations.items():
            recipe_name = meal_data["name"]
            print(f"Fetching recipe details for: {recipe_name}")

            # 만개의레시피에서 레시피 정보 검색
            recipe_details = fetch_recipe_from_mangae(recipe_name)
            if recipe_details:
                detailed_recommendations[meal_key] = {
                    "name": recipe_name,
                    "description": meal_data["description"],
                    "nutrients": meal_data["nutrients"],
                    "ingredients": recipe_details["ingredients"],
                    "difficulty": recipe_details["difficulty"],
                    "cooking_time": recipe_details["cooking_time"],
                    "recipe_link": recipe_details["recipe_link"]
                }
            else:
                detailed_recommendations[meal_key] = {
                    "name": recipe_name,
                    "description": meal_data["description"],
                    "nutrients": meal_data["nutrients"],
                    "ingredients": "레시피 정보를 찾을 수 없습니다.",
                    "difficulty": "정보 없음",
                    "cooking_time": "정보 없음",
                    "recipe_link": "링크 없음"
                }

        return jsonify({'recommendation': detailed_recommendations}), 200, {'Content-Type': 'application/json; charset=utf-8'}

    except OpenAIError as e:
        print(f"OpenAI API error: {str(e)}")
        return jsonify({'error': f"OpenAI API error: {str(e)}"}), 500
    except Exception as e:
        print(f"General error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
