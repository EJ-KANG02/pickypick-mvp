import React, { useState } from 'react';
import axios from 'axios';

const Chat = () => {
    const [messages, setMessages] = useState([]);
    const [userInput, setUserInput] = useState('');

    const sendMessage = async () => {
        const newMessage = { text: userInput, sender: 'user' };
        setMessages([...messages, newMessage]);
        setUserInput('');

        // API 호출
        const response = await axios.post('http://localhost:5000/api/message', {
            message: userInput
        });

        setMessages([...messages, newMessage, { text: response.data.reply, sender: 'ai' }]);
    };

    return (
        <div className="flex flex-col">
            <div className="chat-window bg-gray-100 p-4 rounded-lg h-96 overflow-y-scroll">
                {messages.map((msg, index) => (
                    <div key={index} className={msg.sender === 'user' ? "text-right" : "text-left"}>
                        <span className={msg.sender === 'user' ? "bg-blue-500 text-white p-2 rounded-lg" : "bg-gray-300 p-2 rounded-lg"}>
                            {msg.text}
                        </span>
                    </div>
                ))}
            </div>
            <input
                type="text"
                className="mt-4 p-2 border border-gray-300 rounded"
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            />
        </div>
    );
};

export default Chat;
