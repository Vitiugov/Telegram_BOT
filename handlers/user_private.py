from aiogram import Router,F, types
from aiogram.filters import CommandStart,Command, StateFilter, or_f
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from database.orm_query import orm_add_product, orm_delete_product, orm_update_product, orm_get_products, orm_get_product

from kbds import reply,inline


user_private_router = Router()

# КЛАСС ДЛЯ ФСМ МАШИНЫ И РЕДАКТИРОВАНИЯ
class AddProduct(StatesGroup):
    name = State()
    Description = State()
    link = State()
    image = State()

    product_for_change= None

    texts = {
        'AddProduct:name': 'Введите название заново:',
        'AddProduct:Description': 'Введите описание заново:',
        'AddProduct:link': 'Введите сылку заново:',
        'AddProduct:image': 'Этот стейт последний, поэтому...',
    }


@user_private_router.message(CommandStart())
@user_private_router.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer('Привет я бот для хранения данных!',
                            reply_markup=reply.start_kb.as_markup(
                            resize_keyboard=True,
                            input_field_placeholder='Что Вас интересует?'))

@user_private_router.message((F.text.lower()('меню')))
@user_private_router.message(Command("menu"))
async def menu_cmd(message: types.Message):
    await message.answer("Меню вызвано:",
                            reply_markup=reply.start_kb.as_markup(
                            resize_keyboard=True,
                            input_field_placeholder='Что Вас интересует?'))

@user_private_router.message((F.text.lower().contains('просмотр')))
@user_private_router.message(Command("view"))
async def menu_cmd(message: types.Message, session: AsyncSession):
    await message.answer("Вот список записей")
    for product in await orm_get_products(session):
        await message.answer_photo(
            product.image,
            caption=f"<strong>Название: {product.name}\
                            \nОписание:</strong> {product.description}\n<strong>Ссылка: </strong> {product.link}",
            reply_markup=inline.get_callback_btns(
                btns={
                    "Удалить": f"delete_{product.id}",
                    "Изменить": f"change_{product.id}",
                }
            ),
        )

# НА БУДУЩЕЕ СДЕЛАТЬ КНОПКУ С ВЫБОРОМ ОК ИЛИ ОТМЕНА ДЛЯ РЕДАКТИРОВАНИЯ
@user_private_router.callback_query(StateFilter(None), F.data.startswith('change_'))
async def change_product_callback(callback: types.CallbackQuery,state: FSMContext, session: AsyncSession):
    product_id = callback.data.split("_")[-1]

    product_for_change = await orm_get_product(session, int(product_id))

    AddProduct.product_for_change = product_for_change

    await callback.answer()
    await callback.message.answer(
        "Введите название", reply_markup=reply.del_kb
    )
    await state.set_state(AddProduct.name)

@user_private_router.callback_query(F.data.startswith('delete_'))
async def delete_product(callback: types.CallbackQuery, session: AsyncSession):
    product_id = callback.data.split("_")[-1]
    await orm_delete_product(session, int(product_id))

    # НА БУДУЩЕЕ СДЕЛАТЬ КНОПКУ С ВЫБОРОМ ОК ИЛИ ОТМЕНА ДЛЯ УДАЛЕНИЯ
    await callback.answer("Запись удалена")
    await callback.message.answer("Запись удалена!")


# ДОБАВЛЕНИЕ ЗАПИСИ ЧЕРЕЗ FSM


# хендлер для ввода имени
@user_private_router.message(StateFilter(None), (F.text.lower().contains('добавить')))
@user_private_router.message(Command("add"))
async def menu_cmd(message: types.Message, state: FSMContext):
    await message.answer("Введите название", reply_markup=reply.del_kb)
    await state.set_state(AddProduct.name)

@user_private_router.message(StateFilter('*'),Command("отмена"))
@user_private_router.message(StateFilter('*'),F.text.casefold() == "отмена")
async def menu_cmd(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    if AddProduct.product_for_change:
        AddProduct.product_for_change = None
    await state.clear()
    await message.answer("Действия отменены", reply_markup=reply.start_kb.as_markup(
                            resize_keyboard=True,
                            input_field_placeholder='Что Вас интересует?'))

@user_private_router.message(StateFilter('*'),Command("назад"))
@user_private_router.message(StateFilter('*'),F.text.casefold() == "назад")
async def menu_cmd(message: types.Message,state: FSMContext) -> None:

    current_state = await state.get_state()
    if current_state == AddProduct.name:
        await message.answer(('Предидущего шага нету, или введите команду "отмена"'))
        return
    previous = None
    for step in AddProduct.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(f"ок, возвращаемся к прошлому шагу \n {AddProduct.texts[previous.state]}")
        previous = step


@user_private_router.message(AddProduct.name, or_f(F.text, F.text =='.'))
async def add_name(message: types.Message, state: FSMContext):
    if message.text == '.':
        await state.update_data(name=AddProduct.product_for_change.name)
    else:
        # МОЖНО ДОБАВИТЬ ПРОВЕРКУ
        await state.update_data(name=message.text)

    await message.answer("Введите описание")
    await state.set_state(AddProduct.Description)


# Хендлер для отлова некорректных вводов для состояния name
@user_private_router.message(AddProduct.name)
async def add_name2(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели не допустимые данные, введите ТЕКСТ названия")

# Переходим из описания к ссылке
@user_private_router.message(AddProduct.Description, or_f(F.text, F.text =='.'))
async def add_description(message: types.Message, state: FSMContext):
    if message.text == '.':
        await state.update_data(Description=AddProduct.product_for_change.description)
    else:
        await state.update_data(Description=message.text)
    await message.answer("Введите ссылку")
    await state.set_state(AddProduct.link)

# Хендлер для отлова некорректных вводов для состояния Description
@user_private_router.message(AddProduct.Description)
async def add_name2(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели не допустимые данные, введите ТЕКСТ описания")

@user_private_router.message(AddProduct.link, or_f(F.text, F.text =='.'))
async def add_link(message: types.Message, state: FSMContext):
    if message.text == '.':
        await state.update_data(link=AddProduct.product_for_change.link)
    else:
        await state.update_data(link=message.text)
    await message.answer("Загрузите изображение")
    await state.set_state(AddProduct.image)

# Хендлер для отлова некорректных вводов для состояния link
@user_private_router.message(AddProduct.link)
async def add_name2(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели не допустимые данные, введите ССЫЛКУ")

@user_private_router.message(AddProduct.image, or_f(F.photo, F.text =='.'))
async def add_image(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text and message.text == ".":
        await state.update_data(image=AddProduct.product_for_change.image)

    else:
        await state.update_data(image=message.photo[-1].file_id)

    data = await state.get_data()
    try:
        if AddProduct.product_for_change:
            await orm_update_product(session, AddProduct.product_for_change.id, data)
        else:
            await orm_add_product(session, data)

        await message.answer("Данные записаны", reply_markup=reply.start_kb.as_markup(
                                                resize_keyboard=True,
                                                input_field_placeholder='Что Вас интересует?'))

        await state.clear()
    except Exception as e:
        await message.answer(
            f"ОШИБКА \n{str(e)}\n Обратитесь к программисту", reply_markup=reply.start_kb.as_markup(
                            resize_keyboard=True,
                            input_field_placeholder='Что Вас интересует?')
        )
        await state.clear()
    AddProduct.product_for_change = None



# Хендлер для отлова некорректных вводов для состояния link
@user_private_router.message(AddProduct.image)
async def add_name2(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели не допустимые данные, введите ИЗОБРАЖЕНИЕ")

@user_private_router.message((F.text.lower().contains('убрать меню')))
async def menu_cmd(message: types.Message):
    await message.answer("Меню убрано", reply_markup=reply.del_kb)