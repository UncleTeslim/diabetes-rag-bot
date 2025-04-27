document.addEventListener('DOMContentLoaded', function() {
    const chatContainer = document.getElementById('chat');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const userQuestion = userInput.value.trim();
        if (!userQuestion) return;
        
        addUserMessage(userQuestion);
        userInput.value = '';
        
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'loading';
        loadingDiv.className = 'flex items-center p-3 rounded-lg bg-[#2c3e50] max-w-[80%] self-start fade-in';
        loadingDiv.innerHTML = '<div class="spinner mr-3"></div><div>Thinking...</div>';
        chatContainer.appendChild(loadingDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: userQuestion })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            const loadingElement = document.getElementById('loading');
            if (loadingElement) {
                loadingElement.remove();
            }

            console.log("Response from server:", data); // Log for debugging

            // Check if the response has the 'response' field
            if (data && data.response) {
                addBotMessage(data.response);
            } else {
                addBotMessage('⚠️ Sorry, there was an error processing your request. Please try again.');
            }
        })
        .catch(error => {
            const loadingElement = document.getElementById('loading');
            if (loadingElement) {
                loadingElement.remove();
            }
            addBotMessage('⚠️ Sorry, there was an error processing your request. Please try again.');
            console.error('Error:', error);
        });
    });
    
function addUserMessage(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'flex justify-end mb-3';
    messageDiv.innerHTML = `
        <div class="bg-[#94d2bd] text-black p-3 rounded-lg max-w-[80%] fade-in">
            <p>${escapeHTML(message)}</p>
        </div>
    `;
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function addBotMessage(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = "flex justify-start mb-4";

    const botBubble = document.createElement('div');
    botBubble.className = "bg-[#2c3e50] p-4 rounded-lg max-w-[80%] text-white text-sm leading-relaxed fade-in";
    botBubble.innerText = message; // 🔥 SAFE: No parsing, just clean text

    messageDiv.appendChild(botBubble);

    document.getElementById('chat').appendChild(messageDiv);
}
    
function escapeHTML(str) {
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
});


