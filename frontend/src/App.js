import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
    const [educationCodes, setEducationCodes] = useState([]);
    const [schools, setSchools] = useState([]);
    const [selectedEducationCode, setSelectedEducationCode] = useState('');
    const [selectedSchool, setSelectedSchool] = useState('');
    const [schoolCode, setSchoolCode] = useState('');
    const [educationCode, setEducationCode] = useState('');
    const [clientNutrition, setClientNutrition] = useState(null);
    const [recommendation, setRecommendation] = useState(null);
    const [menu, setMenu] = useState(null);
    const [age, setAge] = useState('');
    const [height, setHeight] = useState(''); // 아이의 키
    const [weight, setWeight] = useState(''); // 아이의 몸무게
    const [dislikes, setDislikes] = useState('');
    const [allergies, setAllergies] = useState('');
    const [noMenuMessage, setNoMenuMessage] = useState(''); // 급식 정보가 없을 경우 메시지
    const [isMenuLoading, setIsMenuLoading] = useState(false); // 급식 메뉴 로딩 상태
    const [isRecommendationLoading, setIsRecommendationLoading] = useState(false); // 추천 식단 로딩 상태
    const [isKindergarten, setIsKindergarten] = useState(false); // 유치원생 여부
    const [sex, setSex] = useState(''); // 성별 상태 추가

    useEffect(() => {
        // 교육청 목록을 가져오는 API 호출
        axios.get('http://127.0.0.1:5000/api/education-codes')
            .then(response => {
                setEducationCodes(response.data);
            })
            .catch(error => {
                console.error('Error fetching education codes:', error);
            });
    }, []);

    useEffect(() => {
        // 교육청을 선택하면 해당 교육청의 학교 목록을 가져옵니다.
        if (selectedEducationCode && !isKindergarten) {
            axios.post('http://127.0.0.1:5000/api/schools', { education_code: selectedEducationCode })
                .then(response => {
                    // 받은 학교 목록에서 초등학교만 필터링
                    const elementarySchools = response.data.filter(school => school.SCHUL_KND_SC_NM === '초등학교');
                    setSchools(elementarySchools);
                })
                .catch(error => {
                    console.error('Error fetching schools:', error);
                });
        }
    }, [selectedEducationCode, isKindergarten]);

    const handleSchoolSelection = (school) => {
        setSelectedSchool(school.SCHUL_NM);
        setSchoolCode(school.SD_SCHUL_CODE);
        setEducationCode(school.ATPT_OFCDC_SC_CODE);
    };

    // 급식 메뉴를 가져오는 함수
    const fetchSchoolMenu = async () => {
        if (!schoolCode || !educationCode) {
            console.error('학교 코드와 교육청 코드가 필요합니다.');
            return null;
        }

        setIsMenuLoading(true); // 급식 메뉴 로딩 시작

        try {
            const response = await axios.post('http://127.0.0.1:5000/api/school-menu', {
                school_code: schoolCode,
                education_code: educationCode
            });

            if (response.data.menu.length === 0) {
                setNoMenuMessage('오늘의 급식 정보가 없습니다.');
                return null;
            } else {
                setMenu(response.data.menu);
                return response.data.menu;
            }
        } catch (error) {
            console.error('Error fetching school menu:', error);
            setNoMenuMessage('급식 정보를 가져오는 데 문제가 발생했습니다.');
            return null;
        } finally {
            setIsMenuLoading(false); // 급식 메뉴 로딩 끝
        }
    };

    const handleSubmitRecommendation = async (e) => {
        e.preventDefault();

        try {
            let menuData = null;

            if (!isKindergarten) {
                // 급식 메뉴를 먼저 가져옵니다. 유치원생이 아닌 경우에만 급식 정보 요청
                menuData = await fetchSchoolMenu();
                if (!menuData) return; // 급식 메뉴를 못 가져오면 종료
            }

            setIsRecommendationLoading(true); // 추천 식단 로딩 시작

            // 유치원생인 경우 menuData는 없으므로, info는 빈 배열로 설정
            const infoData = isKindergarten ? [] : menuData.map(item => item.info);

            // 급식 정보를 포함한 추천 요청
            const response = await axios.post('http://127.0.0.1:5000/api/recommendation', {
                age,
                height,
                weight,
                sex,  // 성별 추가
                dislikes: dislikes.split(',').map(item => item.trim()),
                allergies: allergies.split(',').map(item => item.trim()),
                info: infoData
            });

            // 하루 권장 영양소 정보 (client_nutrition) 설정
            const clientNutrition = response.data.client_nutrition;

            // 맞춤형 식단 추천 정보 (recommendation) 설정
            const recommendation = response.data.recommendation;

            // 각각의 state에 할당
            setClientNutrition(clientNutrition);  // 하루 권장 영양소 정보를 상태에 저장
            setRecommendation(recommendation);    // 식단 추천 정보를 상태에 저장

        } catch (error) {
            console.error('Error fetching recommendation:', error);
        } finally {
            setIsRecommendationLoading(false); // 추천 식단 로딩 끝
        }
    };

    // 급식에서 <br> 태그 제거하고 재료 쉼표로 구분
    const cleanMenuText = (text) => {
        if (!text) return '';
        const cleanedText = text.replace(/<br\s*\/?>/gi, ', '); // <br> 태그 제거 후 쉼표로 구분
        return cleanedText.trim();
    };

    // 급식 메뉴에서 재료를 쉼표로 구분하여 표시
    const formatIngredients = (ingredients) => {
        // ingredients가 배열일 경우
        if (Array.isArray(ingredients)) {
            return ingredients.join(', ');  // 배열의 각 항목을 쉼표로 구분된 문자열로 변환
        } else {
            return ingredients;  // ingredients가 배열이 아니면 그대로 반환
        }
    };

    return (
        <div className="min-h-screen flex flex-col justify-center items-center bg-gray-100">
            <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-lg">
                <h1 className="text-2xl font-bold mb-4 text-gray-700">아이 맞춤 식단 추천</h1>

                <form onSubmit={handleSubmitRecommendation} className="space-y-4">
                    <label className="block">
                        <span className="text-gray-700">아이 나이</span>
                        <input
                            type="number"
                            value={age}
                            onChange={(e) => setAge(e.target.value)}
                            required
                            className="mt-1 p-2 border border-gray-300 rounded w-full"
                        />
                    </label>

                    <label className="block">
                        <span className="text-gray-700">성별</span>
                        <div className="mt-2">
                            <label className="mr-4">
                                <input
                                    type="radio"
                                    value="male"
                                    checked={sex === 'male'}
                                    onChange={() => setSex('male')}
                                />
                                남자
                            </label>
                            <label>
                                <input
                                    type="radio"
                                    value="female"
                                    checked={sex === 'female'}
                                    onChange={() => setSex('female')}
                                />
                                여자
                            </label>
                        </div>
                    </label>

                    <label className="block">
                        <span className="text-gray-700">아이 키 (cm)</span>
                        <input
                            type="number"
                            value={height}
                            onChange={(e) => setHeight(e.target.value)}
                            required
                            className="mt-1 p-2 border border-gray-300 rounded w-full"
                        />
                    </label>
                    <label className="block">
                        <span className="text-gray-700">아이 몸무게 (kg)</span>
                        <input
                            type="number"
                            value={weight}
                            onChange={(e) => setWeight(e.target.value)}
                            required
                            className="mt-1 p-2 border border-gray-300 rounded w-full"
                        />
                    </label>
                    <label className="block">
                        <span className="text-gray-700">편식하는 음식 (쉼표로 구분, 없으면 '없음' 기재)</span>
                        <input
                            type="text"
                            value={dislikes}
                            onChange={(e) => setDislikes(e.target.value)}
                            required
                            className="mt-1 p-2 border border-gray-300 rounded w-full"
                        />
                    </label>
                    <label className="block">
                        <span className="text-gray-700">알러지 정보 (쉼표로 구분, 없으면 '없음' 기재)</span>
                        <input
                            type="text"
                            value={allergies}
                            onChange={(e) => setAllergies(e.target.value)}
                            required
                            className="mt-1 p-2 border border-gray-300 rounded w-full"
                        />
                    </label>

                    <label className="block">
                        <span className="text-gray-700">유치원생인가요?</span>
                        <input
                            type="checkbox"
                            checked={isKindergarten}
                            onChange={(e) => setIsKindergarten(e.target.checked)}
                            className="mt-1 p-2 border border-gray-300 rounded"
                        />
                    </label>

                    {isKindergarten ? (
                        <></> // 유치원생인 경우 "유치원 이름" 입력을 받지 않음
                    ) : (
                        <>
                            <label className="block">
                                <span className="text-gray-700">교육청 선택</span>
                                <select
                                    value={selectedEducationCode}
                                    onChange={(e) => setSelectedEducationCode(e.target.value)}
                                    className="mt-1 p-2 border border-gray-300 rounded w-full"
                                >
                                    <option value="">교육청을 선택하세요</option>
                                    {educationCodes.map((education, index) => (
                                        <option key={index} value={education.code}>{education.name}</option>
                                    ))}
                                </select>
                            </label>

                            <label className="block">
                                <span className="text-gray-700">학교 이름</span>
                                <select
                                    value={selectedSchool}
                                    onChange={(e) => {
                                        setSelectedSchool(e.target.value);
                                        const selectedSchool = schools.find(school => school.SCHUL_NM === e.target.value);
                                        if (selectedSchool) {
                                            handleSchoolSelection(selectedSchool);
                                        }
                                    }}
                                    className="mt-1 p-2 border border-gray-300 rounded w-full"
                                >
                                    <option value="">학교를 선택하세요</option>
                                    {schools.map((school, index) => (
                                        <option key={index} value={school.SCHUL_NM}>
                                            {school.SCHUL_NM}
                                        </option>
                                    ))}
                                </select>
                            </label>
                        </>
                    )}

                    <button type="submit" className="w-full bg-orange-500 text-white p-2 rounded hover:bg-orange-600">
                        추천 식단 받기
                    </button>
                </form>

                {/* 하루 필수 영양소 정보 제공 */}
                {isMenuLoading && <p>하루 필수 영양소를 불러오는 중...</p>}
                {clientNutrition && (
                    <div className="section">
                        <h2 className="section-title">하루 권장 영양소</h2>
                        <div className="nutrition-grid">
                            <div className="nutrition-card">
                                <h3>칼로리</h3>
                                <p>{clientNutrition.client_calories} </p>
                            </div>
                            <div className="nutrition-card">
                                <h3>탄수화물</h3>
                                <p>{clientNutrition.client_carbs} </p>
                            </div>
                            <div className="nutrition-card">
                                <h3>단백질</h3>
                                <p>{clientNutrition.client_protein} </p>
                            </div>
                            <div className="nutrition-card">
                                <h3>지방</h3>
                                <p>{clientNutrition.client_fat} </p>
                            </div>
                            <div className="nutrition-card">
                                <h3>비타민</h3>
                                <p>{clientNutrition.client_vitamins}</p>
                            </div>
                        </div>
                    </div>
                )}

                {/* 급식 메뉴 표시 */}
                {isMenuLoading && <p>급식 메뉴를 불러오는 중...</p>}
                {noMenuMessage && <p>{noMenuMessage}</p>}
                {menu && !isRecommendationLoading && (
                    <div className="section">
                        <h2 className="section-title">오늘의 급식</h2>
                        <div className="menu-list">
                            {menu.map((meal, index) => (
                                <div key={index} className="menu-card">
                                    <h3 className="menu-date">{meal.date}</h3>
                                    <p className="menu-text">{cleanMenuText(meal.menu)}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* 추천 식단 표시 */}
                {isRecommendationLoading && <p>추천 식단을 불러오는 중...</p>}
                {recommendation && (
                    <div className="section">
                        <h2 className="section-title">추천 식단</h2>
                        <div className="menu-list">
                            {Object.keys(recommendation).map((mealKey) => (
                                <div key={mealKey} className="menu-card">
                                    <h3 className="menu-title">{recommendation[mealKey].name}</h3>
                                    <p className="menu-description">{recommendation[mealKey].description}</p>
                                    <div className="menu-details">
                                        <div className="menu-item">
                                            <span className="label">칼로리:</span> {recommendation[mealKey].nutrients.calories}
                                        </div>
                                        <div className="menu-item">
                                            <span className="label">재료:</span> {recommendation[mealKey].ingredients.join(', ')}
                                        </div>
                                        <div className="menu-item">
                                            <span className="label">난이도:</span> {recommendation[mealKey].difficulty}
                                        </div>
                                        <div className="menu-item">
                                            <span className="label">조리 시간:</span> {recommendation[mealKey].cooking_time}
                                        </div>
                                    </div>
                                    <a
                                        href={recommendation[mealKey].recipe_link}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="recipe-button"
                                    >
                                        레시피 보기
                                    </a>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

            </div>
        </div>
    );
}

export default App;
