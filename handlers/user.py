import html
from aiogram import Router, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from handlers.helpers import delete_previous_menu, save_menu_msg
from sqlalchemy.ext.asyncio import AsyncSession
from database.requests import get_user, create_user, get_favorites, get_history, get_all_anime, get_anime, get_all_folders, get_unlinked_anime, get_folder, get_anime_in_folder, get_4k_anime, get_user_by_username
from keyboards.reply import get_main_menu
from keyboards.inline import get_payment_keyboard, get_catalog_keyboard, get_anime_keyboard, get_history_keyboard
from datetime import datetime, timedelta
from config import ADMIN_IDS, SUPERADMIN_IDS

router = Router()

TOS_TEXT_1 = """
<b>Пользовательское соглашение (Terms of Service)</b>

<b>1. Общие положения и статус документа</b>
1.1. Настоящее Пользовательское соглашение (далее — «Соглашение») является публичной офертой и регулирует отношения между создателями Telegram-бота (далее — «Бот», «Сервис», «Администрация») и любым лицом, использующим данного Бота (далее — «Пользователь»).
1.2. Нажатие кнопки «/start», а также любое использование функций Бота означает безоговорочное согласие Пользователя с условиями настоящего Соглашения. Если Пользователь не согласен с условиями, он обязан немедленно прекратить использование Бота.
1.3. Использование Бота разрешено лицам, достигшим 18-летнего возраста, либо лицам от 14 лет с явного согласия их законных представителей.
1.4. <b>Делимость соглашения:</b> Если по какой-либо причине одно или несколько положений настоящего Соглашения будут признаны недействительными или не имеющими юридической силы, это не оказывает влияния на действительность или применимость остальных положений.
1.5. <b>Выживаемость положений (Survival Clause):</b> В случае расторжения настоящего Соглашения (в том числе при перманентной блокировке аккаунта Пользователя), пункты, касающиеся отказа от ответственности, политики возвратов (Strict No Refund) и защиты интеллектуальной собственности, сохраняют свою полную юридическую силу.

<b>2. Описание сервиса</b>
2.1. Бот предоставляет Пользователям доступ к своему внутреннему функционалу, базам данных, эксклюзивному медиаконтенту (включая контент в разрешении 4K) и сопутствующим развлекательно-информационным возможностям.
2.2. Бот предоставляется по принципу «как есть» (as is). Администрация не гарантирует бесперебойную работу Бота, полное отсутствие ошибок и не несет ответственности за временные технические сбои.

<b>3. Права и обязанности сторон</b>
<b>3.1. Пользователь обязуется:</b>
- Не использовать Бота для спама, флуда и применения автоматизированных скриптов.
- Не использовать Бота для любых действий, нарушающих применимое законодательство (мошенничество, распространение запрещенных материалов и т.д.).
- <b>Строго соблюдать авторские права Сервиса: категорически запрещается копировать, выкачивать (парсить), перепродавать, публиковать (сливать) на сторонних ресурсах или передавать третьим лицам предоставляемый Ботом контент, в особенности эксклюзивные материалы в качестве 4K.</b>
- Уважительно относиться к Администрации и службе поддержки.

<b>3.2. Права Администрации (Политика блокировок):</b>
- <b>Администрация оставляет за собой безусловное право отказать в обслуживании, ограничить функционал или полностью заблокировать аккаунт Пользователя (выдать перманентный бан) по своему личному усмотрению, в любой момент, без предварительного уведомления и без объяснения причин.</b>
- В частности, моментальная блокировка без права на апелляцию применяется при малейших подозрениях в воровстве или распространении 4K-контента Сервиса.
- Администрация вправе вносить изменения в функционал Бота по своему усмотрению.
"""

TOS_TEXT_2 = """
<b>4. Платные услуги и политика возвратов (Strict No Refund Policy)</b>
4.1. В Боте могут быть предусмотрены платные услуги (доступ к 4K-контенту, разовые покупки и т.д.). Оплата производится через интегрированные платежные системы.
4.2. Администрация не хранит и не обрабатывает платежные данные карт.
4.3. <b>Возврат денежных средств не осуществляется ни при каких обстоятельствах.</b> Оплачивая любые услуги, Пользователь признает, что приобретает невозвратный цифровой товар/доступ, и добровольно отказывается от права требовать возврата средств.
4.4. <b>Статус услуг «Навсегда» (Lifetime):</b> В случае приобретения услуг или тарифов, позиционируемых как предоставленные «Навсегда», срок их действия ограничивается временем технического существования и функционирования самого Бота. В случае закрытия проекта компенсация не выплачивается.
4.5. <b>Чарджбэки (Chargebacks):</b> При попытке принудительного возврата средств через банк, аккаунт Пользователя перманентно блокируется, а данные передаются в платежную систему для оспаривания.
4.6. В случае блокировки Пользователя (в том числе по усмотрению Администрации или за слив контента), доступ к платным функциям аннулируется, а <b>средства не возвращаются</b>.

<b>5. Отказ от ответственности и форс-мажор</b>
5.1. Администрация не несет ответственности за любой прямой или косвенный ущерб, возникший в результате использования Бота. Вся ответственность за любые действия с использованием Бота лежит на Пользователе.
5.2. <b>Сторонние ресурсы:</b> Если Бот предоставляет ссылки на сторонние ресурсы, Администрация не контролирует и не несет ответственности за их работоспособность или содержимое.
5.3. <b>Зависимость от платформы:</b> Сервис функционирует на базе мессенджера Telegram. В случае временной или перманентной блокировки Бота со стороны платформы Telegram, изменения API мессенджера или иных ограничений со стороны владельцев Telegram, обязательства Администрации перед Пользователями считаются прекращенными, и компенсации не выплачиваются.
5.4. <b>Форс-мажор:</b> Администрация не несет ответственности за перебои в работе Бота, вызванные причинами, не зависящими от Сервиса (сбои серверов Telegram, блокировки провайдеров, обстоятельства непреодолимой силы).

<b>6. Конфиденциальность (Privacy Policy)</b>
6.1. Бот собирает минимально необходимые данные (Telegram ID, имя пользователя, язык) для обеспечения работы платных услуг и защиты от воровства контента.
6.2. Администрация обязуется не передавать данные Пользователей третьим лицам, за исключением случаев прямого нарушения закона.
6.3. <b>Защита данных:</b> Администрация принимает все разумные меры для защиты собираемых данных, однако не несет ответственности за их утечку, возникшую в результате хакерских атак, взломов серверов или несанкционированного доступа третьих лиц.
6.4. <b>Право на удаление:</b> Пользователь имеет право запросить полное удаление своих данных, обратившись в службу поддержки. При этом оказание услуг и доступ к Боту прекращаются.

<b>7. Изменение условий</b>
7.1. Администрация оставляет за собой право в любой момент вносить изменения в настоящее Соглашение. 
7.2. Продолжение использования Бота после внесения любых изменений означает автоматическое согласие Пользователя с новой редакцией Соглашения.

<b>8. Контакты</b>
8.1. Связь с администрацией и поддержка осуществляются по ссылке: <a href="https://t.me/Kusaira_anime?direct">Служба поддержки</a>
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, state: FSMContext):
    user = await get_user(session, message.from_user.id)
    if not user:
        user = await create_user(session, message.from_user.id, message.from_user.username)
    
    if not user.has_accepted_tos:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Я согласен", callback_data="accept_tos")]
        ])
        await message.answer(TOS_TEXT_1, parse_mode="HTML")
        await message.answer(TOS_TEXT_2, reply_markup=keyboard, parse_mode="HTML")
        return
        
    text = (
        "🎥 <b>Добро пожаловать на Kusaira! Аниме в 4к!</b>\n\n"
        "Здесь вы можете смотреть любимые аниме в <b>оригинальном качестве</b> "
        "прямо в Telegram, без тормозов и назойливой рекламы."
    )
    await delete_previous_menu(message, state)
    await message.answer(text, reply_markup=get_main_menu(), parse_mode="HTML")

@router.callback_query(F.data == "accept_tos")
async def process_accept_tos(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    user = await get_user(session, callback.from_user.id)
    if user and not user.has_accepted_tos:
        user.has_accepted_tos = True
        await session.commit()
        
    try:
        await callback.message.delete()
    except:
        pass
        
    text = (
        "🎥 <b>Добро пожаловать на Kusaira! Аниме в 4к!</b>\n\n"
        "Здесь вы можете смотреть любимые аниме в <b>оригинальном качестве</b> "
        "прямо в Telegram, без тормозов и назойливой рекламы."
    )
    await callback.message.answer(text, reply_markup=get_main_menu(), parse_mode="HTML")
    await callback.answer()

@router.message(Command("premium"))
@router.message(F.text == "💎 Подписка")
async def cmd_premium(message: Message, session: AsyncSession, state: FSMContext, command: CommandObject = None):
    user = await get_user(session, message.from_user.id)

    # Логика для обычных юзеров
    if user and user.is_premium and user.premium_until:
        if user.premium_until > datetime.utcnow():
            days_left = (user.premium_until - datetime.utcnow()).days
            text = f"✨ <b>Ваша премиум подписка активна!</b>\n\nОсталось дней: <b>{days_left}</b>"
            await delete_previous_menu(message, state)
            return await message.answer(text, parse_mode="HTML", reply_markup=get_payment_keyboard(is_extend=True))
        else:
            user.is_premium = False
            await session.commit()
            
    text = (
        "😔 <b>У вас нет активной подписки.</b>\n\n"
        "Оформите Premium-подписку, чтобы получить эксклюзивный доступ "
        "ко всем 4K релизам и фильмам без ограничений!"
    )
    await delete_previous_menu(message, state)
    await message.answer(text, parse_mode="HTML", reply_markup=get_payment_keyboard())

@router.message(F.text == "🆘 Поддержка")
async def cmd_support(message: Message, state: FSMContext):
    text = (
        "🆘 <b>Служба поддержки</b>\n\n"
        "Возникли проблемы с оплатой, не грузит видео или нашли баг? "
        "А может просто хотите предложить крутое аниме для добавления?\n\n"
        "Мы всегда на связи и готовы помочь! Пишите сюда: "
        "👉 https://t.me/Kusaira_anime?direct"
    )
    await delete_previous_menu(message, state)
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "📚 Каталог")
async def show_catalog(message: Message, session: AsyncSession, state: FSMContext):
    folders = await get_all_folders(session, is_4k=False)
    unlinked = await get_unlinked_anime(session, is_4k=False)
    items = list(folders) + list(unlinked)
    
    if not items:
        return await message.answer("Каталог пока пуст.")
    
    await delete_previous_menu(message, state)
    msg = await message.answer(
        "📚 <b>Выберите из каталога:</b>",
        reply_markup=get_catalog_keyboard(items),
        parse_mode="HTML"
    )
    await save_menu_msg(msg.message_id, state)

from database.requests import get_4k_anime

@router.message(F.text == "📺 Каталог 4К")
async def show_4k_catalog(message: Message, session: AsyncSession, state: FSMContext):
    folders = await get_all_folders(session, is_4k=True)
    unlinked = await get_unlinked_anime(session, is_4k=True)
    items = list(folders) + list(unlinked)
    
    if not items:
        return await message.answer("Каталог 4К пока пуст.")
        
    await delete_previous_menu(message, state)
    msg = await message.answer(
        "📺 <b>Выберите аниме в 4К качестве:</b>\n<i>(Просмотр доступен только по подписке)</i>",
        reply_markup=get_catalog_keyboard(items),
        parse_mode="HTML"
    )
    await save_menu_msg(msg.message_id, state)

@router.callback_query(F.data.startswith("show_folder_"))
async def show_folder_card(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    folder_id = int(callback.data.split("_")[2])
    folder = await get_folder(session, folder_id)
    if not folder:
        return await callback.answer("Папка не найдена.", show_alert=True)
        
    anime_list = await get_anime_in_folder(session, folder_id)
    keyboard = get_catalog_keyboard(anime_list) if anime_list else None
        
    import html
    title_esc = html.escape(folder.title)
    desc_esc = html.escape(folder.description) if folder.description else ""
    text = f"📁 <b>{title_esc}</b>\n\n<pre>{desc_esc}</pre>\n\nВыберите аниме:"
    if len(text) > 1024:
        allowed_len = 1021 - len(f"📁 <b>{title_esc}</b>\n\n<pre></pre>\n\nВыберите аниме:")
        text = f"📁 <b>{title_esc}</b>\n\n<pre>{desc_esc[:allowed_len]}...</pre>\n\nВыберите аниме:"
    
    await delete_previous_menu(callback, state)
    
    if folder.photo_file_id:
        msg = await callback.message.answer_photo(
            photo=folder.photo_file_id,
            caption=text,
            reply_markup=keyboard,
            parse_mode="HTML",
            protect_content=True
        )
    else:
        msg = await callback.message.answer(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    await save_menu_msg(msg.message_id, state)
    await callback.answer()

@router.callback_query(F.data.startswith("show_anime_"))
async def show_anime_card(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    anime_id = int(callback.data.split("_")[2])
    anime = await get_anime(session, anime_id)
    if not anime:
        return await callback.answer("Аниме не найдено.", show_alert=True)
    
    is_fav = False # Для упрощения пока False, можно добавить проверку если нужно
    
    title = html.escape(anime.title)
    desc = html.escape(anime.description) if anime.description else "Нет описания."
    quality_tag = "💎 " if getattr(anime, 'is_4k', False) else ""
    movie_tag = "🎥 " if getattr(anime, 'display_id', '') and str(getattr(anime, 'display_id', '')).endswith('_3') else ""
    desc_esc = html.escape(desc) if desc else ""
    caption = f"🎬 {quality_tag}{movie_tag}<b>{title}</b>\n\n<pre>{desc_esc}</pre>"
    
    # Ограничение Telegram на длину caption для фото — 1024 символа
    if len(caption) > 1024:
        # 1024 - 3 (для "...") = 1021
        allowed_len = 1021 - len(f"🎬 {quality_tag}{movie_tag}<b>{title}</b>\n\n<pre></pre>")
        caption = f"🎬 {quality_tag}{movie_tag}<b>{title}</b>\n\n<pre>{desc_esc[:allowed_len]}...</pre>"
    
    await delete_previous_menu(callback, state)
    msg = await callback.message.answer_photo(
        photo=anime.photo_file_id,
        caption=caption,
        reply_markup=get_anime_keyboard(anime.id, is_fav),
        parse_mode="HTML"
    )
    await save_menu_msg(msg.message_id, state)
    await callback.answer()

@router.message(F.text == "⭐ Избранное")
async def show_favorites(message: Message, session: AsyncSession, state: FSMContext):
    user = await get_user(session, message.from_user.id)
    favs = await get_favorites(session, user.id)
    if not favs:
        return await message.answer("Ваш список избранного пуст.")
    
    await delete_previous_menu(message, state)
    msg = await message.answer(
        "⭐ <b>Ваше избранное:</b>",
        reply_markup=get_catalog_keyboard(favs),
        parse_mode="HTML"
    )
    await save_menu_msg(msg.message_id, state)

@router.message(F.text == "🕒 История")
async def show_history(message: Message, session: AsyncSession, state: FSMContext):
    user = await get_user(session, message.from_user.id)
    hist = await get_history(session, user.id)
    if not hist:
        return await message.answer("Вы еще ничего не смотрели.")
    
    await delete_previous_menu(message, state)
    msg = await message.answer(
        "🕒 <b>Последние просмотренные:</b>",
        reply_markup=get_history_keyboard(hist),
        parse_mode="HTML"
    )
    await save_menu_msg(msg.message_id, state)
