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
    const [recommendation, setRecommendation] = useState(null);
    const [menu, setMenu] = useState(null);
    const [age, setAge] = useState('');
    const [dislikes, setDislikes] = useState('');
    const [allergies, setAllergies] = useState('');
    const [noMenuMessage, setNoMenuMessage] = useState(''); // 급식 정보가 없을 경우 메시지

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
        if (selectedEducationCode) {
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
    }, [selectedEducationCode]);

    const handleSchoolSelection = (school) => {
        setSelectedSchool(school.SCHUL_NM);
        setSchoolCode(school.SD_SCHUL_CODE);
        setEducationCode(school.ATPT_OFCDC_SC_CODE);
    };

    const handleSubmitRecommendation = async (e) => {
        e.preventDefault();

        try {
            const response = await axios.post('http://127.0.0.1:5000/api/recommendation', {
                age,
                dislikes: dislikes.split(',').map(item => item.trim()),
                allergies: allergies.split(',').map(item => item.trim()),
            });

            setRecommendation(response.data.recommendation);
        } catch (error) {
            console.error('Error fetching recommendation:', error);
        }
    };

    const handleSubmitSchoolMenu = async (e) => {
        e.preventDefault();

        // schoolCode와 educationCode 값이 제대로 설정되었는지 확인하는 로그
        console.log('학교 코드:', schoolCode);  // schoolCode가 비어 있거나 잘못 설정되었을 경우 확인
        console.log('교육청 코드:', educationCode);  // educationCode가 비어 있거나 잘못 설정되었을 경우 확인

        if (!schoolCode || !educationCode) {
            console.error('학교 코드와 교육청 코드가 필요합니다.');
            return;
        }

        console.log('급식 정보 요청 전:', { school_code: schoolCode, education_code: educationCode });  // 로그 추가

        try {
            const response = await axios.post('http://127.0.0.1:5000/api/school-menu', {
                school_code: schoolCode,
                education_code: educationCode,
            });

            console.log('급식 정보 응답:', response.data);  // 응답 내용 확인

            if (response.data.menu.length === 0) {
                setNoMenuMessage('오늘의 급식 정보가 없습니다.');  // 급식이 없으면 메시지 표시
            } else {
                setMenu(response.data.menu);  // 급식 메뉴 데이터를 state에 저장
            }
        } catch (error) {
            console.error('Error fetching school menu:', error);
            setNoMenuMessage('급식 정보를 가져오는 데 문제가 발생했습니다.');
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

                <form onSubmit={handleSubmitSchoolMenu} className="space-y-4 mt-6">
                    <label className="block">
                        <span className="text-gray-700">교육청 선택</span>
                        <select
                            value={selectedEducationCode}
                            onChange={(e) => {
                                console.log('선택된 교육청 값:', e.target.value);  // 선택된 교육청 값 로그
                                setSelectedEducationCode(e.target.value);
                            }}
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
                                console.log('선택된 학교 값:', e.target.value);  // 선택된 학교 값 로그
                                setSelectedSchool(e.target.value);
                                const selectedSchool = schools.find(school => school.SCHUL_NM === e.target.value); // 선택된 학교 정보 찾기
                                if (selectedSchool) {
                                    handleSchoolSelection(selectedSchool);  // 선택된 학교 정보를 handleSchoolSelection에 전달
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


                    <button
                        type="submit"
                        className="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600"
                    >
                        급식 정보 가져오기
                    </button>
                </form>

                {noMenuMessage && <p>{noMenuMessage}</p>} {/* 급식 정보가 없을 때 메시지 표시 */}

                {menu && (
                    <div className="mt-6 space-y-4">
                        {menu.map((meal, index) => (
                            <div key={index} className="p-4 border border-gray-300 rounded">
                                <h3 className="font-bold text-lg">{meal.date}</h3>
                                <p>{meal.menu}</p>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default App;
