import requests
from config.config import GPT_TOKEN

class GPTHelper:
    def __init__(self):
        self.api_key = GPT_TOKEN
        self.api_url = "https://deepseekapi.org/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _escape_markdown(self, text: str) -> str:
        """Экранирует специальные символы для MarkdownV2"""
        chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in chars:
            text = text.replace(char, f'\\{char}')
        return text

    def _send_request(self, prompt: str) -> str:
        """Отправляет запрос к DeepSeek API"""
        data = {
            "model": "deepseek-coder-1.3b-base",  # Используем базовую модель
            "messages": [
                {
                    "role": "system",
                    "content": "Форматируй ответы простым текстом с минимальным форматированием. "
                              "Используй * для выделения важных моментов."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(
                self.api_url, 
                headers=self.headers, 
                json=data, 
                timeout=120
            )
            
            if response.status_code == 401:
                return "Ошибка авторизации. Проверьте API ключ."
            elif response.status_code != 200:
                return f"Ошибка сервера: {response.status_code} - {response.text}"
            
            response.raise_for_status()
            content = response.json()['choices'][0]['message']['content']
            return self._escape_markdown(content)
        except requests.exceptions.Timeout:
            return "Превышено время ожидания ответа от сервера (2 минуты)."
        except requests.exceptions.ConnectionError:
            return "Ошибка подключения к серверу. Попробуйте позже."
        except Exception as e:
            return f"Неизвестная ошибка: {str(e)}"

    def analyze_habit(self, habit_name: str) -> str:
        """Анализирует привычку и предлагает рекомендации"""
        prompt = f"""
        Проанализируй привычку "{habit_name}" и предоставь:

        1. Краткое описание привычки
        2. Оценка сложности (1-10)
        3. Рекомендуемая частота
        4. Советы по формированию
        5. Возможные препятствия

        Используй простое форматирование с * для выделения важных моментов.
        """
        return self._send_request(prompt)

    def get_motivation(self, habit_name: str, streak: int) -> str:
        """Генерирует мотивационное сообщение"""
        prompt = f"""
        Создай короткое мотивационное сообщение для привычки "{habit_name}" 
        с текущей серией {streak} дней.
        
        Сделай сообщение позитивным и кратким (2-3 предложения).
        Добавь эмодзи в начале и конце.
        """
        return self._send_request(prompt)

    def suggest_improvements(self, habit_data: dict) -> str:
        """Предлагает улучшения на основе статистики"""
        prompt = f"""
        На основе статистики:
        - Привычка: {habit_data['name']}
        - Успешных дней: {habit_data['completions']}
        - Пропущено дней: {habit_data['missed']}
        - Лучшая серия: {habit_data['best_streak']}

        Предложи 3 простых совета для улучшения результатов.
        """
        return self._send_request(prompt) 