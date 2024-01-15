import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types.message import Message
from aiogram.types.callback_query import CallbackQuery
from aiogram.types.labeled_price import LabeledPrice
from aiogram.types.pre_checkout_query import PreCheckoutQuery
from cruds.users import UserManager
from database import async_session_maker

from keyboards.invoices import create_invoice_keyboard
from keyboards.start import return_to_start_keyboard
from models.users import UserModel
from schemas.users import UserUpdateSchema
from utils.delete_state_messages import delete_state_messages

router = Router()


@router.callback_query(F.data == 'create_invoice')
async def create_invoice(callback: CallbackQuery, state: FSMContext):
    invoice_link = await callback.bot.create_invoice_link(
        title='🚅 Оплата подписки на отслеживание билетов РЖД',
        description='30 дней',
        payload=f'{callback.from_user.id}_1month_{callback.message.message_id}',
        provider_token='381764678:TEST:75410',  # TODO: брать из конфига
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

    #  Заносим созданный счет в бд
    # async with async_session_maker() as session:
    #     invoice_crud = InvoiceManager(session=session)
    #     await invoice_crud.create(InvoiceCreateSchema())
    #     await session.commit()

    await delete_state_messages(
        query=callback,
        state=state
    )


@router.pre_checkout_query()
async def pre_checkout_query(query: PreCheckoutQuery):
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def handle_successful_payment(message: Message, current_user: UserModel, state: FSMContext):
    tg_user_id, date_string, invoice_message_id = message.successful_payment.invoice_payload.split('_')

    # рассчитываем сколько прибавить
    subscription_add_date = datetime.timedelta(days=0)
    if date_string == '1month':
        subscription_add_date = datetime.timedelta(days=30)

    # рассчитываем какую дату занести в бд
    new_subscription_date = current_user.subscription_expires_at
    if new_subscription_date is None or new_subscription_date < datetime.datetime.utcnow():
        new_subscription_date = datetime.datetime.utcnow()
    new_subscription_date += subscription_add_date

    # Обновляем дату окончания подписки у юзера
    async with async_session_maker() as session:
        user_crud = UserManager(session=session)
        await user_crud.update(
            obj_id=current_user.id,
            obj_in=UserUpdateSchema(subscription_expires_at=new_subscription_date)
        )
        await session.commit()

    # Удаляем сообщение со счетом для оплаты
    try:
        await message.bot.delete_message(
            chat_id=message.from_user.id,
            message_id=invoice_message_id
        )
    except Exception:
        pass

    text = (
f'''
<b>⚡️ Подписка успешно оплачена</b>

Теперь вы имеете полный доступ к возможности отслеживания. Для начала использования, <b>нажмите на кнопку ниже</b>

<i>Срок действия: до {new_subscription_date.strftime('%d.%m.%Y %H:%M')}</i>
'''
    )
    await message.answer(
        text=text,
        parse_mode='HTML',
        reply_markup=return_to_start_keyboard(text='💫 Начать использование')
    )
