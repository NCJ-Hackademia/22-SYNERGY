document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    const chatWindow = document.getElementById('chat-window');
    const messageInput = document.getElementById('message-input');
    const startBtn = document.getElementById('start-btn');
    const sendBtn = document.getElementById('send-btn');
    const endBtn = document.getElementById('end-btn');
    let roomId = null;

    function appendMessage(text, from) {
        const div = document.createElement('div');
        div.classList.add('mb-2');
        if (from === 'you') {
            div.classList.add('text-right', 'text-blue-300');
            div.textContent = `You: ${text}`;
        } else if (from === 'stranger') {
            div.classList.add('text-left', 'text-green-300');
            div.textContent = `Stranger: ${text}`;
        } else {
            div.classList.add('text-center', 'text-yellow-300');
            div.textContent = text;
        }
        chatWindow.appendChild(div);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    function resetChat() {
        roomId = null;
        messageInput.disabled = true;
        sendBtn.disabled = true;
        endBtn.disabled = true;
        startBtn.disabled = false;
    }

    startBtn.addEventListener('click', () => {
        socket.emit('start_chat');
        startBtn.disabled = true;
    });

    sendBtn.addEventListener('click', () => {
        const message = messageInput.value.trim();
        if (message && roomId) {
            socket.emit('send_message', { room_id: roomId, message });
            messageInput.value = '';
        }
    });

    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendBtn.click();
        }
    });

    endBtn.addEventListener('click', () => {
        if (roomId) {
            socket.emit('end_chat', { room_id: roomId });
            appendMessage('You ended the chat.', 'system');
            resetChat();
        }
    });

    socket.on('chat_started', (data) => {
        roomId = data.room_id;
        appendMessage('Connected to a stranger!', 'system');
        messageInput.disabled = false;
        sendBtn.disabled = false;
        endBtn.disabled = false;
    });

    socket.on('message', (data) => {
        appendMessage(data.text, data.from);
    });

    socket.on('stranger_disconnected', () => {
        appendMessage('Stranger disconnected.', 'system');
        resetChat();
    });
});
