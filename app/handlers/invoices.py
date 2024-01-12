import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types.message import Message
from aiogram.types.callback_query import CallbackQuery
from aiogram.types.labeled_price import LabeledPrice
from aiogram.types.pre_checkout_query import PreCheckoutQuery

from keyboards.invoices import create_invoice_keyboard
from keyboards.start import return_to_start_keyboard
from utils.delete_state_messages import delete_state_messages

router = Router()


@router.callback_query(F.data == 'create_invoice')
async def create_invoice(callback: CallbackQuery, state: FSMContext):
    invoice_link = await callback.bot.create_invoice_link(
        title='🚅 Оплата подписки на отслеживание билетов РЖД',
        description='30 дней',
        payload=f'{callback.from_user.id}_1month_{callback.message.message_id}',
        provider_token='381764678:TEST:75410',
        currency='RUB',
        prices=[LabeledPrice(label='Подписка на 30 дней', amount='10000')]
    )
    text = 'Для оплаты/продления подписки на 30 дней, нажмите на кнопку ниже'

    await callback.bot.send_message(
        text=text,
        chat_id=callback.from_user.id,
        parse_mode='HTML',
        reply_markup=create_invoice_keyboard(invoice_link=invoice_link)
    )

    #  TODO: Занести созданный счет в бд

    await delete_state_messages(
        query=callback,
        state=state
    )


@router.pre_checkout_query()
async def pre_checkout_query(query: PreCheckoutQuery):
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def handle_successful_payment(message: Message, state: FSMContext):
    tg_user_id, date_string, invoice_message_id = message.successful_payment.invoice_payload.split('_')

    subscription_add_date = datetime.timedelta(days=0)
    if date_string == '1month':
        subscription_add_date = datetime.timedelta(days=30)
    # TODO: Добавляем к подписке 30 дней в бд, или если подписки нет, то текущая дата + 30 дней

    #  Удаляем сообщение со счетом для оплаты
    try:
        await message.bot.delete_message(
            chat_id=message.from_user.id,
            message_id=invoice_message_id
        )
    except Exception:
        pass

    text = (
        '''
        <b>⚡️ Подписка успешно оплачена</b>
        
        Теперь вы имеете полный доступ к возможности отслеживания. Для начала использования, <b>нажмите на кнопку ниже</b>
        
        <i>Срок действия: до 12.02.2022 11:42</i>
        '''
    )  # TODO: изменить срок действия на верный
    await message.answer(
        text=text,
        parse_mode='HTML',
        reply_markup=return_to_start_keyboard(text='💫 Начать использование')
    )
