from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import requests
from openai import OpenAIError
from bs4 import BeautifulSoup
import logging
import json
import re
from datetime import datetime
app = Flask(__name__)
CORS(app)

# OpenAI API 키 설정
openai.api_key = '-'

# 공공급식데이터 API 키와 기본 URL 설정
API_KEY = '037b1bc78c19428494ca85e1360445a7'  # 발급받은 API 키로 교체
BASE_URL = 'http://open.neis.go.kr/hub/mealServiceDietInfo'
SCHOOL_SEARCH_URL = 'http://open.neis.go.kr/hub/schoolInfo'

# 교육청 코드 및 학교 코드 목록을 가져오는 API
@app.route('/api/education-codes', methods=['GET'])
def get_education_codes():
    # 실제로 이 정보를 외부 API나 데이터베이스에서 가져오는 방법을 추가
    education_codes = [
        {"code": "B10", "name": "서울특별시교육청"},
        {"code": "C10", "name": "부산광역시교육청"},
        {"code": "D10", "name": "대구광역시교육청"},
        {"code": "E10", "name": "인천광역시교육청"},
        {"code": "F10", "name": "광주광역시교육청"},
        {"code": "G10", "name": "대전광역시교육청"},
        {"code": "H10", "name": "울산광역시교육청"},
        {"code": "I10", "name": "세종특별자치시교육청"},
        {"code": "J10", "name": "경기도교육청"},
        {"code": "K10", "name": "강원도교육청"},
        {"code": "M10", "name": "충청북도교육청"},
        {"code": "N10", "name": "충청남도교육청"},
        {"code": "P10", "name": "전북특별자치도교육청"},
        {"code": "Q10", "name": "전라남도교육청"},
        {"code": "R10", "name": "경상북도교육청"},
        {"code": "S10", "name": "경상남도교육청"},
        {"code": "T10", "name": "제주특별자치도교육청"}
    ]
    return jsonify(education_codes), 200

# 학교 이름을 통해 학교 코드(SD_SCHUL_CODE)와 교육청 코드(ATPT_OFCDC_SC_CODE) 가져오기
@app.route('/api/schools', methods=['POST'])
def get_schools():
    app.logger.debug("Received POST request for /api/schools")
    data = request.json
    education_code = data.get('education_code')

    if not education_code:
        app.logger.error("교육청 코드가 제공되지 않았습니다.")
        return jsonify({'error': '교육청 코드를 제공해야 합니다.'}), 400

    all_schools = []  # 모든 학교를 저장할 리스트

    # 페이지네이션을 고려하여 여러 페이지에서 데이터를 받아옵니다.
    page = 1
    while True:
        params = {
            'KEY': API_KEY,
            'Type': 'json',
            'pIndex': page,  # 페이지 번호
            'pSize': 1000,  # 한 페이지에 최대 1000개 학교
            'ATPT_OFCDC_SC_CODE': education_code  # 교육청 코드로 학교 목록 요청
        }

        app.logger.debug(f"Sending request to external API with params: {params}")

        response = requests.get(SCHOOL_SEARCH_URL, params=params)

        # 외부 API 응답 상태 코드 및 본문 확인
        app.logger.debug(f"External API response status: {response.status_code}")
        app.logger.debug(f"External API response body: {response.text}")

        if response.status_code != 200:
            app.logger.error(f"External API request failed with status code: {response.status_code}")
            return jsonify({'error': '학교 데이터를 가져오는 데 실패했습니다.'}), 500

        # 응답 데이터 처리
        data = response.json()
        app.logger.debug(f"Received response from school API: {data}")

        # 데이터 확인
        if 'schoolInfo' not in data or 'row' not in data['schoolInfo'][1]:
            app.logger.error("학교 정보를 찾을 수 없습니다.")
            return jsonify({'error': '학교 정보를 찾을 수 없습니다.'}), 404

        schools = data['schoolInfo'][1]['row']
        # 초등학교만 필터링
        elementary_schools = [school for school in schools if school['SCHUL_KND_SC_NM'] == '초등학교']

        # 초등학교를 전체 목록에 추가
        all_schools.extend(elementary_schools)

        # 만약 받은 학교 수가 pSize 이상이라면, 다음 페이지로 넘어갑니다.
        if len(schools) < 1000:
            break  # 더 이상 데이터가 없으면 종료

        page += 1  # 다음 페이지로 이동

    # 반환할 데이터 확인 (샘플 로그)
    app.logger.debug(f"Returning schools data: {all_schools[:5]}")  # 상위 5개 항목만 로그에 출력

    return jsonify(all_schools), 200

# 오늘 날짜를 기준으로 급식 정보만 필터링하는 함수
def get_today_meal_info(data):
    today = datetime.today().strftime('%Y%m%d')  # 오늘 날짜 (YYYYMMDD 형식)
    app.logger.debug(f"Today's date: {today}")

    meals = []

    # 'mealServiceDietInfo' 안에 급식 정보가 들어있다는 가정
    for meal_info in data['mealServiceDietInfo']:
        # 'row' 배열에서 오늘 날짜와 일치하는 급식 메뉴를 찾기
        for meal in meal_info.get('row', []):
            meal_date = meal.get('MLSV_YMD', '')
            app.logger.debug(f"Meal date: {meal_date}")

            # 급식 날짜가 오늘 날짜와 같으면 필터링
            if meal_date == today:
                meals.append({
                    'date': meal_date,
                    'menu': meal.get('DDISH_NM', '정보 없음'),  # 급식 메뉴
                    'info': {
                        'calories' : meal.get('CAL_INFO', '정보 없음'), # 급식 칼로리
                        'nutrients' : meal.get('NTR_INFO', '정보 없음') # 급식 영양소
                    }
                })


    app.logger.debug(f"Filtered meals for today: {meals}")
    return meals

# 급식 정보 요청 (오늘의 급식만 필터링)
@app.route('/api/school-menu', methods=['POST'])
def school_menu():
    data = request.json
    school_code = data.get('school_code')
    education_code = data.get('education_code')

    # 로그 확인용
    app.logger.debug(f"Received school_code: {school_code}, education_code: {education_code}")

    if not school_code or not education_code:
        return jsonify({'error': '학교 코드와 교육청 코드가 필요합니다.'}), 400

    page = 1
    while page < 3:
        params = {
            'KEY': API_KEY,
            'Type': 'json',
            'pIndex': page,
            'pSize': 1000,
            'ATPT_OFCDC_SC_CODE': education_code,
            'SD_SCHUL_CODE': school_code,
            'MMEAL_SC_CODE': '2'  # 급식 정보 (중식)
        }

        # 요청 보내기 전에 URL 및 파라미터 확인
        app.logger.debug(f"Making GET request to: {BASE_URL} with params: {params}")

        response = requests.get(BASE_URL, params=params)
        app.logger.debug(f"Response status code: {response.status_code}")  # 응답 상태 코드
        app.logger.debug(f"Response body: {response.text}")  # 응답 본문(전체 데이터)

        data = response.json()

        # 응답 데이터에 급식 정보가 있는지 확인
        if 'mealServiceDietInfo' not in data:
            app.logger.error('급식 정보를 찾을 수 없습니다.')
            return jsonify({'error': '급식 정보를 찾을 수 없습니다.'}), 404

        # 오늘의 급식만 필터링
        meals = get_today_meal_info(data)
        # 만약 meals 가 값이 도출됐다면 while 문 빠져나오도록 코드 달아줘
        if len(meals) > 0:
            break

        page += 1

    # 오늘의 급식 정보가 없을 경우
    if len(meals) == 0:
        return jsonify({'error': '오늘의 급식 정보가 없습니다.'}), 404

    return jsonify({'menu': meals}), 200

# 레시피 크롤링 기능
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

# 성별에 따른 하루 권장 칼로리 계산
def calculate_nutrition(age, height, weight, sex):
    # Mifflin-St Jeor 공식을 사용한 BMR 계산
    if sex == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    # 평균 활동 수준을 고려한 TDEE (대사량)
    tdee = bmr * 1.55  # 평균 활동 수준(운동을 적당히 하는 경우)

    # 하루 권장 영양소 계산 (칼로리 비율에 따라)
    client_calories = round(tdee)
    client_carbs = round(client_calories * 0.55 / 4)  # 탄수화물: 55% (4칼로리/그램)
    client_protein = round(client_calories * 0.15 / 4)  # 단백질: 15% (4칼로리/그램)
    client_fat = round(client_calories * 0.30 / 9)  # 지방: 30% (9칼로리/그램)
    client_vitamins = "비타민 A, 비타민 D, 비타민 C, 비타민 E"  # 기본 비타민 정보 (예시)

    # 결과 반환
    return {
        "client_calories": f"{client_calories} kcal",
        "client_carbs": f"{client_carbs} g",
        "client_protein": f"{client_protein} g",
        "client_fat": f"{client_fat} g",
        "client_vitamins": client_vitamins,
    }

@app.route('/api/recommendation', methods=['POST'])
def recommendation():
    try:
        data = request.json
        print(f"Received data: {data}")
        try:
            user_age = float(data.get('age'))
            user_height = float(data.get('height'))
            user_weight = float(data.get('weight'))
        except ValueError as e:
            return jsonify({'error': '나이, 키, 몸무게는 숫자여야 합니다.'}), 400
        user_sex = data.get('sex')  # 성별 (male / female)
        dislikes = data.get('dislikes', [])
        allergies = data.get('allergies', [])
        info = data.get('info', [])  # info를 받도록 수정

        if not user_age or not user_height or not user_weight or not isinstance(dislikes, list) or not isinstance(allergies, list):
            print("잘못된 입력 데이터입니다.")
            return jsonify({'error': '잘못된 입력 데이터입니다.'}), 400

        dislikes_text = ', '.join(dislikes) if dislikes else '없음'
        allergies_text = ', '.join(allergies) if allergies else '없음'

        # 권장 영양소 계산
        client_nutrition = calculate_nutrition(user_age, user_height, user_weight, user_sex)

        # 유치원생인 경우 info가 없을 수 있으므로 안전하게 처리
        meal_info_text = ""
        if info:
            for meal in info:
                calories = meal.get('calories', '정보 없음')
                nutrients = meal.get('nutrients', '정보 없음')
                meal_info_text += f"칼로리: {calories}, 영양소: {nutrients}. "
        else:
            meal_info_text = "급식 정보가 제공되지 않았습니다."

        print("Sending request to OpenAI API")
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 아이들의 맞춤형 식단을 제공하는 헬퍼입니다."
                },
                {
                    "role": "user",
                    "content": (
                        f"나이가 {user_age}세, 키 {user_height}cm, 몸무게 {user_weight}kg인 아이의 맞춤 식단 3개를 추천해주세요. "
                        f"이 아이는 {dislikes_text}을/를 싫어하고, {allergies_text}에 알러지가 있습니다. "
                        f"이 아이는 점심 동안 {meal_info_text} 만큼 섭취한 상태입니다."

                        #하루 권장 영양소 고려
                        "아이의 나이, 키, 몸무게를 고려하여 하루 권장 칼로리 및 필수 영양소를 다음 JSON 형식으로 제공해 주세요: "
                        '{"client_calories": "300kcal", "client_carbs": "50g", "client_protein": "20g", "client_fat": "10g", "client_vitamins": "비타민 정보"}'

                        #식단 추천
                        "한국인에게 추천하는 식단이므로 한국인이 자주 먹는 식단으로 구성해주세요."
                        "한 식단에는 하나의 음식만 추천해주세요."
                        "편식하거나 알러지 있는 재료의 영양분을 대체할 수 있는 재료가 주 재료로 들어간 음식이어야 합니다."
                        "점심 동안 이미 먹은 칼로리, 영양 성분을 고려해 가장 보충이 필요한 영양소 2개를 꼭 포함해야 합니다."
                        "각 식단에 대해 재료, 칼로리, 탄수화물, 단백질, 지방, 비타민을 포함해 주세요. "
                        "그리고 메뉴마다 편식 음식, 알러지에서 어떤 점을 대체했는지 (대체 영양소 사용 등) 간단하게 한줄로 설명해주세요. 이때 반드시 description 형식을 지켜서 써주세요. 형식은 편식하는 재료 or 알러지있는 재료 이름 -> 대체한 재료 이름(~~ 영양소 대체) 이래야 합니다."
                        "최종 응답을 다음 JSON 형식으로 제공해 주세요 (반드시 정확한 JSON 형식으로만 응답해주세요.): "
                        '{"client_nutrition": {"client_calories": "300kcal", "client_carbs": "50g", "client_protein": "20g", "client_fat": "10g", "client_vitamins": "비타민 정보"}, '
                        '"meal_1": {"name": "식단 이름", "description": "편식하는 재료 or 알러지 있는 재료 이름 -> 대체한 재료 이름 (~~ 영양소 대체)", '
                        '"nutrients": {"calories": "300kcal", "carbs": "50g", "protein": "20g", "fat": "10g", "vitamins": "비타민 A, 비타민 K"}}, '
                        '"meal_2": {"name": "식단 이름", "description": "편식하는 재료 or 알러지 있는 재료 이름 -> 대체한 재료 이름 (~~ 영양소 대체)", '
                        '"nutrients": {"calories": "300kcal", "carbs": "50g", "protein": "20g", "fat": "10g", "vitamins": "비타민 B"}}, '
                        '"meal_3": {"name": "식단 이름", "description": "편식하는 재료 or 알러지 있는 재료 이름 -> 대체한 재료 이름 (~~ 영양소 대체)", '
                        '"nutrients": {"calories": "300kcal", "carbs": "50g", "protein": "20g", "fat": "10g", "vitamins": "비타민 C"}}}}'
                    )
                }
            ]
        )
        print("OpenAI API response received")

        ai_reply = response['choices'][0]['message']['content']

        # 예시 응답을 로깅하여 확인
        print(f"AI Response: {ai_reply}")

        # AI 응답에서 JSON 파싱을 위한 불필요한 부분 제거
        # 응답에서 올바른 JSON만 추출
        ai_reply_cleaned = re.sub(r"^```json|```$", "", ai_reply).strip()  # '```json'과 '```' 제거

        try:
            recommendations = json.loads(ai_reply_cleaned)  # JSON으로 안전하게 파싱
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
            return jsonify({'error': 'AI 응답을 JSON 형식으로 파싱하는데 실패했습니다.'}), 500

        # recommendations에서 client_nutrition을 받지 않고, 우리가 계산한 client_nutrition을 넣습니다.
        recommendations["client_nutrition"] = client_nutrition

        # recommendation에서 식단 정보만 추출
        meals = {key: val for key, val in recommendations.items() if key.startswith("meal_")}  # 식단 추천 부분만 추출

        detailed_recommendations = {}

        for meal_key, meal_data in meals.items():
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

        # JSON 응답에서 client_nutrition과 식단 추천을 분리하여 반환
        return jsonify({
            'client_nutrition': client_nutrition,  # 하루 권장 영양소 정보
            'recommendation': detailed_recommendations  # 맞춤형 식단 추천 정보
        }), 200, {'Content-Type': 'application/json; charset=utf-8'}

    except OpenAIError as e:
        print(f"OpenAI API error: {str(e)}")
        return jsonify({'error': f"OpenAI API error: {str(e)}"}), 500
    except Exception as e:
        print(f"General error: {str(e)}")
        return jsonify({'error': str(e)}), 500



# 로깅 설정 (디버깅용)
logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    app.run(debug=True)
