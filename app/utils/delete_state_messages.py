from typing import Any

from aiogram.fsm.context import FSMContext


async def delete_state_messages(query: Any, state: FSMContext):
    data = await state.get_data()
    if "messages_to_delete" in data:
        for message_obj in data['messages_to_delete']:
            try:
                await query.bot.delete_message(
                    chat_id=message_obj['chat_id'],
                    message_id=message_obj['message_id']
                )
            except:
                pass
    data['messages_to_delete'] = []
    await state.set_data(data)
