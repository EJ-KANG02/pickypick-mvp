import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';  // App 컴포넌트 임포트
import './index.css';  // 기본 스타일 임포트

// React 18 이상에서는 createRoot()를 사용합니다.
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);

