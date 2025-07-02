class Chatbox {
    constructor() {
        this.args = {
            openButton: document.querySelector('.chatbox__button'),
            chatBox: document.querySelector('.chatbox__support'),
            sendButton: document.querySelector('.send__button'),
            spinner: document.querySelector('.spinner'),
            chatMessages: document.querySelector('.chatbox__messages'),
            errorMessage: document.querySelector('.error__message'),
            refreshButton: document.querySelector('.refresh__button'),
        }

        this.state = false;
        this.messages = [];
        this.language = this.detectLanguage();
        this.welcomeMessageShown = false;
    }

    display() {
        const { openButton, chatBox, sendButton, spinner, refreshButton } = this.args;

        openButton.addEventListener('click', () => this.toggleState(chatBox));
        sendButton.addEventListener('click', () => this.onSendButton(chatBox, spinner));
        refreshButton.addEventListener('click', () => this.onRefreshButton(chatBox, spinner));

        const node = chatBox.querySelector('input');
        node.addEventListener("keyup", ({ key }) => {
            if (key === "Enter") {
                this.onSendButton(chatBox, spinner);
            }
        });
    }

    toggleState(chatbox) {
        this.state = !this.state;

        if (this.state) {
            chatbox.classList.add('chatbox--active');
            if (!this.welcomeMessageShown) {
                this.showWelcomeMessage(chatbox);
                this.welcomeMessageShown = true;
            }
            this.args.openButton.querySelector('img').src = "./resources/images/icons8-close-32.png";
        } else {
            chatbox.classList.remove('chatbox--active');
            this.args.openButton.querySelector('img').src = "./resources/images/icons8-message-32.png";
        }
    }

    onSendButton(chatbox, spinner) {
        let textField = chatbox.querySelector('input');
        let text1 = textField.value;
        if (text1 === "") {
            return;
        }
        textField.value = '';

        spinner.style.display = 'block';
        textField.disabled = true;
        this.args.chatMessages.classList.add('hidden--messages');
        this.hideErrorMessage();

        let msg1 = { name: "User", message: text1 };
        this.messages.push(msg1);
        this.updateChatText(chatbox);

        fetch('http://127.0.0.1:5000/chat', {
            method: 'POST',
            body: JSON.stringify({ message: text1 }),
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json'
            },
        })
        .then(r => r.json())
        .then(r => {
            let msg2 = { name: "Bot", message: r.answer, feedbackGiven: false, run_id: r.run_id };
            this.messages.push(msg2);
            this.updateChatText(chatbox);
            this.playNotificationSound();
        })
        .catch(error => {
            console.error('Error:', error);
            this.displayErrorMessage();
        })
        .finally(() => {
            spinner.style.display = 'none';
            textField.disabled = false;
            this.args.chatMessages.classList.remove('hidden--messages');
        });
    }

    updateChatText(chatbox) {
        let html = '';
        let lastBotIndex = -1;

        for (let i = this.messages.length - 1; i >= 0; i--) {
            if (this.messages[i].name === "Bot") {
                lastBotIndex = i;
                break;
            }
        }

        this.messages.slice().reverse().forEach((item, index) => {
            const originalIndex = this.messages.length - 1 - index;
            if (item.name === "Bot") {
                if (originalIndex !== 0 && !item.feedbackGiven) {
                    html += '<div class="feedback-buttons">';
                    html += `<button class="thumbs-up" data-index="${originalIndex}">&#x1F44D;</button>`;
                    html += `<button class="thumbs-down" data-index="${originalIndex}">&#x1F44E;</button>`;
                    html += '</div>';
                }
                html += '<div class="messages__item messages__item--visitor">' + item.message + '</div>';
            } else {
                html += '<div class="messages__item messages__item--operator">' + item.message + '</div>';
            }
        });

        const chatmessage = chatbox.querySelector('.chatbox__messages');
        chatmessage.innerHTML = html;

        this.addFeedbackListeners(chatbox);
    }

    addFeedbackListeners(chatbox) {
        const thumbsUpButtons = chatbox.querySelectorAll('.thumbs-up');
        const thumbsDownButtons = chatbox.querySelectorAll('.thumbs-down');

        thumbsUpButtons.forEach(button => {
            button.addEventListener('click', (event) => {
                this.onFeedbackClick(event.target, chatbox);
            });
        });

        thumbsDownButtons.forEach(button => {
            button.addEventListener('click', (event) => {
                this.onFeedbackClick(event.target, chatbox);
            });
        });
    }

    onFeedbackClick(button, chatbox) {
        const messageIndex = button.getAttribute('data-index');
        this.messages[messageIndex].feedbackGiven = true;
        const score = button.classList.contains('thumbs-up') ? 1.0 : 0;
        const run_id = this.messages[messageIndex].run_id

        fetch('http://127.0.0.1:5000/feedback', {
            method: 'POST',
            body: JSON.stringify({ 
                run_id : run_id,
                score : score
            }),
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json'
            },
        })
        .then(response => response.json())
        .catch(error => {
            console.error('Error:', error);
        })

        this.updateChatText(chatbox);
    }

    displayErrorMessage() {
        const errorMessageElement = this.args.errorMessage;
        errorMessageElement.style.display = 'block';
    }

    hideErrorMessage() {
        const errorMessageElement = this.args.errorMessage;
        errorMessageElement.style.display = 'none';
    }

    playNotificationSound() {
        const sound = document.getElementById('notificationSound');
        sound.play();
    }

    showWelcomeMessage(chatbox) {
        let message;
        if (this.language === 'tr') {
            message = "Merhaba! Size nasıl yardımcı olabilirim?";
        } else {
            message = "Hi! How can I assist you today?";
        }

        let msg = { name: "Bot", message: message };
        this.messages.push(msg);
        this.updateChatText(chatbox);
        this.playNotificationSound();
    }

    detectLanguage() {
        const lang = document.documentElement.lang || navigator.language || 'en';
        return lang.startsWith('tr') ? 'tr' : 'en';
    }

    onRefreshButton(chatbox, spinner) {
        spinner.style.display = 'block';
        this.args.chatMessages.classList.add('hidden--messages');
        this.hideErrorMessage();
    
        fetch('http://127.0.0.1:5000/refresh', {
            method: 'POST',
            mode: 'cors',
        })
        .then(() =>{
            this.messages = [];
            this.updateChatText(chatbox);
            this.showWelcomeMessage(chatbox);
        })
        .catch(error => {
            console.error('Error:', error);
            this.displayErrorMessage();
        })
        .finally(() => {
            spinner.style.display = 'none';
            this.args.chatMessages.classList.remove('hidden--messages');
        });
    }

}


const chatbox = new Chatbox();
chatbox.display();