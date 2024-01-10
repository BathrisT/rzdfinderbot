from typing import Any, List

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from utils.delete_state_messages import delete_state_messages


async def add_messages_in_state_to_delete(query: Any, state: FSMContext, messages: List[Message], delete_prev_messages=True):
    if delete_prev_messages:
        await delete_state_messages(query, state)

    data = await state.get_data()
    if "messages_to_delete" not in data:
        data['messages_to_delete'] = list()
    for message in messages:
        data['messages_to_delete'].append({
            "chat_id": message.chat.id,
            "message_id": message.message_id
        })
    await state.set_data(data)
