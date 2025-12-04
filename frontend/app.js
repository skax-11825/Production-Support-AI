// 설정 관리
class ConfigManager {
    constructor() {
        this.loadSettings();
    }

    loadSettings() {
        const saved = localStorage.getItem('difyConfig');
        if (saved) {
            const config = JSON.parse(saved);
            document.getElementById('difyApiBase').value = config.difyApiBase || 'https://api.dify.ai/v1';
            document.getElementById('difyApiKey').value = config.difyApiKey || '';
            document.getElementById('apiServerUrl').value = config.apiServerUrl || 'http://localhost:8000';
        }
    }

    saveSettings() {
        const config = {
            difyApiBase: document.getElementById('difyApiBase').value,
            difyApiKey: document.getElementById('difyApiKey').value,
            apiServerUrl: document.getElementById('apiServerUrl').value
        };
        localStorage.setItem('difyConfig', JSON.stringify(config));
        return config;
    }

    getSettings() {
        return {
            difyApiBase: document.getElementById('difyApiBase').value,
            difyApiKey: document.getElementById('difyApiKey').value,
            apiServerUrl: document.getElementById('apiServerUrl').value
        };
    }
}

// Dify API 클라이언트
class DifyClient {
    constructor(config) {
        this.apiBase = config.difyApiBase;
        this.apiKey = config.difyApiKey;
        this.userId = 'web-ui-user';
    }

    async sendMessage(message, conversationId = null) {
        if (!this.apiKey) {
            throw new Error('Dify API Key가 설정되지 않았습니다.');
        }

        // Dify Chat API 엔드포인트
        // 주의: 이 URL은 Dify Chat 애플리케이션의 API 엔드포인트입니다
        // 형식: https://api.dify.ai/v1/chat-messages
        // 또는 자체 호스팅: https://your-dify-domain.com/v1/chat-messages
        const url = `${this.apiBase}/chat-messages`;
        const payload = {
            inputs: {},
            query: message,
            response_mode: 'blocking',  // 'blocking' 또는 'streaming'
            conversation_id: conversationId,
            user: this.userId
        };

        try {
            console.log('Dify API 요청:', { url, apiKey: this.apiKey.substring(0, 15) + '...' });
            
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const errorMessage = errorData.message || errorData.error || `HTTP ${response.status}: ${response.statusText}`;
                console.error('Dify API 오류 상세:', {
                    status: response.status,
                    statusText: response.statusText,
                    errorData: errorData,
                    url: url,
                    apiKey: this.apiKey.substring(0, 10) + '...' // API Key 일부만 로그
                });
                throw new Error(errorMessage);
            }

            const data = await response.json();
            return {
                answer: data.answer || '응답을 받을 수 없습니다.',
                conversationId: data.conversation_id,
                metadata: data.metadata || {}
            };
        } catch (error) {
            // "Failed to fetch" 오류는 CORS 또는 네트워크 문제
            if (error.message === 'Failed to fetch' || error.name === 'TypeError') {
                console.error('네트워크/CORS 오류:', {
                    url: url,
                    error: error.message,
                    name: error.name
                });
                throw new Error(`연결 실패: API 서버에 연결할 수 없습니다. URL(${url})과 CORS 설정을 확인하세요.`);
            }
            throw new Error(`Dify API 오류: ${error.message}`);
        }
    }

    async checkConnection() {
        if (!this.apiKey) {
            return { connected: false, message: 'API Key가 설정되지 않았습니다.' };
        }

        try {
            // 간단한 테스트 메시지 전송
            const result = await this.sendMessage('테스트');
            return { connected: true, message: '연결 성공' };
        } catch (error) {
            return { connected: false, message: error.message };
        }
    }
}

// API 서버 클라이언트
class APIServerClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }

    async checkHealth() {
        try {
            const response = await fetch(`${this.baseUrl}/health`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();
            return {
                connected: data.status === 'healthy',
                databaseConnected: data.database_connected,
                message: data.status === 'healthy' ? '정상' : '비정상'
            };
        } catch (error) {
            return {
                connected: false,
                databaseConnected: false,
                message: `연결 실패: ${error.message}`
            };
        }
    }
}

// 채팅 UI 관리
class ChatUI {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.userInput = document.getElementById('userInput');
        this.sendButton = document.getElementById('sendButton');
        this.statusBar = document.getElementById('statusBar');
        this.statusText = document.getElementById('statusText');
        this.conversationId = null;
    }

    addMessage(content, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (typeof content === 'string') {
            contentDiv.innerHTML = this.formatMessage(content);
        } else {
            contentDiv.appendChild(content);
        }
        
        messageDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    formatMessage(text) {
        // 마크다운 스타일 포맷팅
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
    }

    addDataTable(data) {
        if (!data || data.length === 0) {
            return document.createTextNode('조회된 데이터가 없습니다.');
        }

        const container = document.createElement('div');
        container.className = 'data-table';

        const table = document.createElement('table');
        const thead = document.createElement('thead');
        const tbody = document.createElement('tbody');

        // 헤더 생성
        const headerRow = document.createElement('tr');
        const keys = Object.keys(data[0]);
        keys.forEach(key => {
            const th = document.createElement('th');
            th.textContent = key;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);

        // 데이터 행 생성
        data.forEach(item => {
            const row = document.createElement('tr');
            keys.forEach(key => {
                const td = document.createElement('td');
                td.textContent = item[key] !== null && item[key] !== undefined ? item[key] : '-';
                row.appendChild(td);
            });
            tbody.appendChild(row);
        });

        table.appendChild(thead);
        table.appendChild(tbody);
        container.appendChild(table);
        return container;
    }

    setStatus(text, type = 'normal') {
        this.statusText.textContent = text;
        this.statusBar.className = `status-bar ${type}`;
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    clearInput() {
        this.userInput.value = '';
    }

    setLoading(loading) {
        this.sendButton.disabled = loading;
        this.userInput.disabled = loading;
        if (loading) {
            this.setStatus('처리 중...', 'loading');
        }
    }
}

// 메인 애플리케이션
class App {
    constructor() {
        this.configManager = new ConfigManager();
        this.chatUI = new ChatUI();
        this.difyClient = null;
        this.apiClient = null;
        this.initializeEventListeners();
        this.checkSystemStatus();
    }

    initializeEventListeners() {
        // 전송 버튼
        document.getElementById('sendButton').addEventListener('click', () => this.handleSendMessage());
        
        // Enter 키
        document.getElementById('userInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSendMessage();
            }
        });

        // 설정 저장
        document.getElementById('saveSettings').addEventListener('click', () => this.saveSettings());
        
        // 상태 확인
        document.getElementById('checkStatus').addEventListener('click', () => this.checkSystemStatus());
    }

    saveSettings() {
        const config = this.configManager.saveSettings();
        this.difyClient = new DifyClient(config);
        this.apiClient = new APIServerClient(config.apiServerUrl);
        
        this.chatUI.addMessage('설정이 저장되었습니다.', false);
        this.checkSystemStatus();
    }

    async checkSystemStatus() {
        const config = this.configManager.getSettings();
        
        // API 서버 상태 확인
        this.apiClient = new APIServerClient(config.apiServerUrl);
        const apiStatus = await this.apiClient.checkHealth();
        const apiStatusElement = document.getElementById('apiServerStatus');
        apiStatusElement.textContent = apiStatus.message;
        apiStatusElement.className = `status-value ${apiStatus.connected ? 'connected' : 'disconnected'}`;

        // Dify 상태 확인
        if (config.difyApiKey) {
            this.difyClient = new DifyClient(config);
            const difyStatus = await this.difyClient.checkConnection();
            const difyStatusElement = document.getElementById('difyStatus');
            difyStatusElement.textContent = difyStatus.message;
            difyStatusElement.className = `status-value ${difyStatus.connected ? 'connected' : 'disconnected'}`;
        } else {
            const difyStatusElement = document.getElementById('difyStatus');
            difyStatusElement.textContent = 'API Key 미설정';
            difyStatusElement.className = 'status-value disconnected';
        }
    }

    async handleSendMessage() {
        const message = this.chatUI.userInput.value.trim();
        if (!message) return;

        // 사용자 메시지 표시
        this.chatUI.addMessage(message, true);
        this.chatUI.clearInput();
        this.chatUI.setLoading(true);

        try {
            const config = this.configManager.getSettings();
            if (!config.difyApiKey) {
                throw new Error('Dify API Key를 먼저 설정해주세요.');
            }

            if (!this.difyClient) {
                this.difyClient = new DifyClient(config);
            }

            // Dify에 메시지 전송
            const result = await this.difyClient.sendMessage(message, this.chatUI.conversationId);
            this.chatUI.conversationId = result.conversationId;

            // 응답 표시
            this.chatUI.addMessage(result.answer, false);

            // 메타데이터에 데이터가 있으면 표시
            if (result.metadata && result.metadata.data) {
                const dataElement = this.chatUI.addDataTable(result.metadata.data);
                const dataMessage = document.createElement('div');
                dataMessage.className = 'message bot-message';
                const contentDiv = document.createElement('div');
                contentDiv.className = 'message-content';
                contentDiv.appendChild(dataElement);
                dataMessage.appendChild(contentDiv);
                this.chatUI.chatMessages.appendChild(dataMessage);
                this.chatUI.scrollToBottom();
            }

            this.chatUI.setStatus('완료', 'normal');
        } catch (error) {
            this.chatUI.addMessage(`오류: ${error.message}`, false);
            this.chatUI.setStatus('오류 발생', 'error');
        } finally {
            this.chatUI.setLoading(false);
        }
    }
}

// 앱 초기화
document.addEventListener('DOMContentLoaded', () => {
    new App();
});

