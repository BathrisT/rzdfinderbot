from io import StringIO, BytesIO
from typing import Optional

import aiogram
from aiogram.types import BufferedInputFile


class TelegramBotHandler:
    """
    Handler для loguru. Использовать так:

    tg_handler = TelegramBotHandler(bot_token='awd', chat_id=123)
    loguru.add(tg_handler.notify, ...)
    """

    def __init__(
            self,
            bot_token: str,
            chat_id: str,
            project_name: Optional[str] = None
    ):
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._project_name = project_name

    async def notify(self, message) -> None:
        message = str(message)
        text = ''
        if self._project_name:
            text = f'{self._project_name}: \n'
        formatted_message = message
        file_flag = False
        if len(message) > 3700:
            file_flag = True
            formatted_message = message[:800] + '...\n\n[Подробнее в файле]'
        text += (
            f'<pre><code lang="python">'
            f'{formatted_message}'
            f'</code></pre>'
        )

        bot = aiogram.Bot(self._bot_token)
        try:
            await bot.send_message(chat_id=self._chat_id, text=text, parse_mode='HTML')
            if file_flag:
                file = BufferedInputFile(file=message.encode(), filename='error.txt')
                await bot.send_document(chat_id=self._chat_id, document=file, parse_mode='HTML')
        except Exception as e:

            print(f'ERROR | Исключение при отправке информации об ошибке в Telegram: \n{e}\n')
        await bot.session.close()

    def __call__(self, *args, **kwargs):
        raise NotImplementedError()
