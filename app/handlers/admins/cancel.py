from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext


async def cancel(call: types.CallbackQuery, state: FSMContext):
    await call.answer("Успешная отмена")
    await state.reset_state(with_data=True)
    await call.message.delete()


def setup_cancel_adm(dp: Dispatcher):
    dp.register_callback_query_handler(cancel, text="cancel", is_admin=True, state="*")
