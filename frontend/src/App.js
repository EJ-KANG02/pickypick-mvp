import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
    const [age, setAge] = useState('');
    const [dislikes, setDislikes] = useState('');
    const [allergies, setAllergies] = useState('');
    const [recommendation, setRecommendation] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();

        try {
            const response = await axios.post('http://127.0.0.1:5000/api/recommendation', {
                age,
                dislikes: dislikes.split(',').map(item => item.trim()),
                allergies: allergies.split(',').map(item => item.trim()),
            });

            const recommendationData = JSON.parse(response.data.recommendation);  // JSON 형식의 응답 파싱
            setRecommendation(recommendationData);
        } catch (error) {
            console.error('Error fetching recommendation:', error);
        }
    };

    return (
        <div className="min-h-screen flex flex-col justify-center items-center bg-gray-100">
            <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-lg">
                <h1 className="text-2xl font-bold mb-4 text-gray-700">아이 맞춤 식단 추천</h1>
                <form onSubmit={handleSubmit} className="space-y-4">
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
                    <button type="submit" className="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600">
                        추천 식단 받기
                    </button>
                </form>
                {recommendation && (
                    <div className="mt-6 space-y-4">
                        {Object.keys(recommendation).map((mealKey, index) => {
                            const meal = recommendation[mealKey];
                            //재료 및 영양소 0~1개일 시 예외 처리
                            const nutrients = meal.nutrients || {};
                            const ingredients = Array.isArray(meal.ingredients)
                                ? meal.ingredients.join(', ')
                                : meal.ingredients || '재료 정보 없음';
                            return (
                                <div key={index} className="p-4 border border-gray-300 rounded">
                                    <h3 className="font-bold text-lg">{meal.name}</h3>
                                    <p className="meal-description">{meal.description  || '식단 설명 없음'}</p>
                                    <p>난이도: {meal.difficulty} | 요리 시간: {meal.cooking_time}</p>
                                    <p>재료: {ingredients}</p>
                                    <p>칼로리: {meal.calories} kcal</p>
                                    <p>탄수화물: {nutrients.carbs || '정보 없음'} </p>
                                    <p>단백질: {nutrients.protein || '정보 없음'} </p>
                                    <p>지방: {nutrients.fat || '정보 없음'} </p>
                                    <p>비타민: {nutrients.vitamins || '정보 없음'}</p>
                                    <a href={meal.recipe_link} target="_blank" rel="noopener noreferrer"
                                       className="recipe-button">
                                        레시피 보기
                                    </a>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}

export default App;
