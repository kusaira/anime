from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import datetime
from config import ADMIN_IDS, SUPERADMIN_IDS
from states.fsm import AdminAddAnime, AdminAddEpisode, AdminDeleteAnime, AdminDeleteEpisode, AdminAddFolder, AdminLinkAnime, AdminDeleteFolder, AdminListEpisodes, AdminEditAnime
from database.requests import add_anime, add_episode, get_all_anime, get_all_users, delete_anime, delete_episode, get_anime_by_title, add_folder, get_all_folders, link_anime_to_folder, get_folder_for_anime, delete_folder, get_episodes, get_anime, update_anime
from keyboards.reply import get_admin_menu, get_main_menu, get_cancel_menu, get_quality_keyboard

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def is_superadmin(user_id: int) -> bool:
    return user_id in SUPERADMIN_IDS

async def send_admin_log(bot: Bot, text: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {text}\n"
    
    with open("admin_actions.log", "a", encoding="utf-8") as f:
        f.write(log_entry)

@router.message(Command("logs"))
async def cmd_logs(message: Message):
    if not is_superadmin(message.from_user.id):
        return
        
    try:
        with open("admin_actions.log", "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        if not lines:
            return await message.answer("Логи пусты.")
            
        # Отправляем последние 20 действий
        last_logs = lines[-20:]
        text = "📝 <b>Последние действия админов:</b>\n\n"
        for line in last_logs:
            text += f"• {line}"
            
        await message.answer(text, parse_mode="HTML")
    except FileNotFoundError:
        await message.answer("Файл логов пока не создан (админы еще ничего не делали).")

@router.message(Command("admin"))
async def cmd_admin(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        return
        
    if command.args:
        args = command.args.split()
        if args[0] == "upgrade" and len(args) > 1:
            if not is_superadmin(message.from_user.id):
                return await message.answer("❌ Эта команда доступна только суперадминистраторам.")
            new_id_str = args[1].replace('"', '').replace("'", "")
            if new_id_str.isdigit():
                new_super_id = int(new_id_str)
                if new_super_id not in SUPERADMIN_IDS:
                    SUPERADMIN_IDS.append(new_super_id)
                    try:
                        with open(".env", "r", encoding="utf-8") as f:
                            lines = f.readlines()
                        
                        has_super = False
                        with open(".env", "w", encoding="utf-8") as f:
                            for line in lines:
                                if line.startswith("SUPERADMIN_IDS="):
                                    has_super = True
                                    current_ids = line.strip().split("=")[1]
                                    if current_ids:
                                        f.write(f"SUPERADMIN_IDS={current_ids},{new_super_id}\n")
                                    else:
                                        f.write(f"SUPERADMIN_IDS={new_super_id}\n")
                                else:
                                    f.write(line)
                            
                            if not has_super:
                                f.write(f"SUPERADMIN_IDS=5551306116,{new_super_id}\n")
                        await message.answer(f"👑 Пользователь {new_super_id} повышен до суперадмина.")
                    except Exception as e:
                        await message.answer(f"Ошибка при сохранении: {e}")
                else:
                    await message.answer("⚠️ Этот пользователь уже суперадмин.")
            else:
                await message.answer("❌ Неверный формат ID.")
            return

        if args[0] == "add" and len(args) > 1:
            new_id_str = args[1].replace('"', '').replace("'", "")
            if new_id_str.isdigit():
                new_admin_id = int(new_id_str)
                if new_admin_id not in ADMIN_IDS:
                    ADMIN_IDS.append(new_admin_id)
                    
                    try:
                        with open(".env", "r", encoding="utf-8") as f:
                            lines = f.readlines()
                        
                        with open(".env", "w", encoding="utf-8") as f:
                            for line in lines:
                                if line.startswith("ADMIN_IDS="):
                                    current_ids = line.strip().split("=")[1]
                                    if current_ids:
                                        f.write(f"ADMIN_IDS={current_ids},{new_admin_id}\n")
                                    else:
                                        f.write(f"ADMIN_IDS={new_admin_id}\n")
                                else:
                                    f.write(line)
                        await message.answer(f"✅ Пользователь {new_admin_id} добавлен в администраторы.")
                    except Exception as e:
                        await message.answer(f"Ошибка при сохранении: {e}")
                else:
                    await message.answer("⚠️ Этот пользователь уже администратор.")
            else:
                await message.answer("❌ Неверный формат ID.")
            return

    await message.answer("Панель администратора", reply_markup=get_admin_menu())

@router.message(F.text == "🔙 В главное меню")
async def exit_admin_mode(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await state.clear()
    await message.answer("Вы вышли в главное меню", reply_markup=get_main_menu())

@router.message(F.text == "❌ Отмена", StateFilter("*"))
async def cancel_admin_action(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=get_admin_menu())

@router.message(F.text == "Список залитого аниме")
async def admin_list_anime(message: Message, session: AsyncSession):
    if not is_admin(message.from_user.id): return
    animes = await get_all_anime(session)
    if not animes:
        return await message.answer("База данных аниме пуста.")
    
    text = "📚 <b>Список залитого аниме:</b>\n\n"
    for a in animes:
        folder = await get_folder_for_anime(session, a.id)
        folder_text = f" (Папка ID {folder.id})" if folder else " (Без папки)"
        text += f"ID {a.id}: {a.title}{folder_text}\n"
    
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "Список пользователей")
async def admin_list_users(message: Message, session: AsyncSession):
    if not is_admin(message.from_user.id): return
    users = await get_all_users(session)
    if not users:
        return await message.answer("Пользователей пока нет.")
    
    text = "👥 <b>Список пользователей:</b>\n\n"
    for u in users:
        text += f"ID: {u.id} | TG: {u.telegram_id} | @{u.username} | Премиум: {'Да' if u.is_premium else 'Нет'}\n"
    
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "Список серий аниме")
async def admin_list_episodes_start(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id): return
    animes = await get_all_anime(session)
    if not animes:
        return await message.answer("Сначала добавьте хотя бы одно аниме.")
    
    text = "Доступные аниме:\n" + "\n".join([f"{a.id}. {a.title}" for a in animes])
    await message.answer(text + "\n\nВведите ID аниме для просмотра его серий:", reply_markup=get_cancel_menu())
    await state.set_state(AdminListEpisodes.waiting_for_anime_id)

@router.message(AdminListEpisodes.waiting_for_anime_id)
async def admin_list_episodes_process(message: Message, state: FSMContext, session: AsyncSession):
    if not message.text.isdigit():
        return await message.answer("ID должен быть числом.")
    
    anime_id = int(message.text)
    anime = await get_anime(session, anime_id)
    if not anime:
        return await message.answer("Аниме с таким ID не найдено.", reply_markup=get_admin_menu())
    
    episodes = await get_episodes(session, anime_id)
    if not episodes:
        await message.answer(f"В аниме '{anime.title}' пока нет залитых серий.", reply_markup=get_admin_menu())
    else:
        text = f"📺 <b>Список серий аниме '{anime.title}':</b>\n\n"
        for ep in episodes:
            text += f"Уникальный ID {ep.id} — Серия {ep.episode_number}\n"
        text += "\n<i>* Используйте Уникальный ID для точного удаления серии.</i>"
        await message.answer(text, reply_markup=get_admin_menu(), parse_mode="HTML")
    await state.clear()

# --- Добавление аниме ---
@router.message(F.text == "Добавить аниме")
async def add_anime_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await message.answer("Введите название аниме:", reply_markup=get_cancel_menu())
    await state.set_state(AdminAddAnime.waiting_for_title)

@router.message(AdminAddAnime.waiting_for_title)
async def add_anime_title(message: Message, state: FSMContext, session: AsyncSession):
    title = message.text.strip()
    existing = await get_anime_by_title(session, title)
    if existing:
        await state.clear()
        return await message.answer("пидорас прекрати", reply_markup=get_admin_menu())
        
    await state.update_data(title=title)
    await message.answer("Введите описание аниме:")
    await state.set_state(AdminAddAnime.waiting_for_description)

@router.message(AdminAddAnime.waiting_for_description)
async def add_anime_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Выберите качество аниме:", reply_markup=get_quality_keyboard())
    await state.set_state(AdminAddAnime.waiting_for_quality)

@router.message(AdminAddAnime.waiting_for_quality)
async def add_anime_quality(message: Message, state: FSMContext):
    if message.text == "4K (Высокое)":
        await state.update_data(is_4k=True)
    else:
        await state.update_data(is_4k=False)
        
    await message.answer("Отправьте постер (фото) аниме:", reply_markup=get_cancel_menu())
    await state.set_state(AdminAddAnime.waiting_for_photo)

@router.message(AdminAddAnime.waiting_for_photo, F.photo)
async def add_anime_photo(message: Message, state: FSMContext, session: AsyncSession):
    if message.media_group_id:
        data = await state.get_data()
        if data.get("last_media_group_id") == message.media_group_id:
            return
        await state.update_data(last_media_group_id=message.media_group_id)
        return await message.answer("Пожалуйста, отправьте только ОДНУ фотографию. Альбомы не поддерживаются!")
        
    data = await state.get_data()
    photo_file_id = message.photo[-1].file_id
    
    anime = await add_anime(session, data['title'], data['description'], photo_file_id, data.get('is_4k', False))
    await send_admin_log(message.bot, f"Админ <code>{message.from_user.id}</code> добавил аниме <b>{anime.title}</b> (ID {anime.id})")
    await message.answer(f"Аниме '{anime.title}' успешно добавлено! ID: {anime.id}", reply_markup=get_admin_menu())
    await state.clear()

# --- Добавление серии ---
@router.message(F.text == "Добавить серию")
async def add_episode_start(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id): return
    animes = await get_all_anime(session)
    if not animes:
        return await message.answer("Сначала добавьте хотя бы одно аниме.")
    
    text = "Доступные аниме:\n" + "\n".join([f"{a.id}. {a.title}" for a in animes])
    await message.answer(text + "\n\nВведите ID аниме:", reply_markup=get_cancel_menu())
    await state.set_state(AdminAddEpisode.waiting_for_anime_id)

@router.message(AdminAddEpisode.waiting_for_anime_id)
async def add_episode_anime_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("ID должен быть числом. Попробуйте еще раз:")
    await state.update_data(anime_id=int(message.text))
    await message.answer("Введите номер серии:")
    await state.set_state(AdminAddEpisode.waiting_for_episode_number)

@router.message(AdminAddEpisode.waiting_for_episode_number)
async def add_episode_num(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Номер должен быть числом. Попробуйте еще раз:")
    await state.update_data(episode_number=int(message.text))
    await message.answer("Отправьте или перешлите видео-файл серии:")
    await state.set_state(AdminAddEpisode.waiting_for_video)

@router.message(AdminAddEpisode.waiting_for_video, F.video)
async def add_episode_video(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    video_file_id = message.video.file_id
    
    await add_episode(session, data['anime_id'], data['episode_number'], video_file_id)
    await send_admin_log(message.bot, f"Админ <code>{message.from_user.id}</code> добавил серию {data['episode_number']} для аниме ID {data['anime_id']}")
    await message.answer(f"Серия {data['episode_number']} успешно добавлена!", reply_markup=get_admin_menu())
    await state.clear()

# --- Удаление аниме ---
@router.message(F.text == "Удалить аниме")
async def del_anime_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await message.answer("Введите ID аниме для удаления:", reply_markup=get_cancel_menu())
    await state.set_state(AdminDeleteAnime.waiting_for_anime_id)

@router.message(AdminDeleteAnime.waiting_for_anime_id)
async def del_anime_process(message: Message, state: FSMContext, session: AsyncSession):
    if not message.text.isdigit():
        return await message.answer("ID должен быть числом.")
    
    anime_id = int(message.text)
    success = await delete_anime(session, anime_id)
    if success:
        await send_admin_log(message.bot, f"Админ <code>{message.from_user.id}</code> удалил аниме ID {anime_id}")
        await message.answer(f"Аниме с ID {anime_id} и все его серии удалены.", reply_markup=get_admin_menu())
    else:
        await message.answer(f"Аниме с ID {anime_id} не найдено.", reply_markup=get_admin_menu())
    await state.clear()

# --- Редактирование аниме ---
@router.message(F.text == "Редактировать аниме")
async def edit_anime_start(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id): return
    await message.answer("Введите ID аниме для редактирования:", reply_markup=get_cancel_menu())
    await state.set_state(AdminEditAnime.waiting_for_anime_id)

@router.message(AdminEditAnime.waiting_for_anime_id)
async def edit_anime_id(message: Message, state: FSMContext, session: AsyncSession):
    if not message.text.isdigit():
        return await message.answer("ID должен быть числом.")
    anime_id = int(message.text)
    anime = await get_anime(session, anime_id)
    if not anime:
        return await message.answer("Аниме не найдено.", reply_markup=get_admin_menu())
    
    await state.update_data(anime_id=anime_id)
    await message.answer(f"Текущее название: <b>{anime.title}</b>\nВведите новое название (или отправьте '-', чтобы оставить текущее):", parse_mode="HTML")
    await state.set_state(AdminEditAnime.waiting_for_new_title)

@router.message(AdminEditAnime.waiting_for_new_title)
async def edit_anime_title(message: Message, state: FSMContext, session: AsyncSession):
    title = message.text.strip()
    if title == "-":
        title = None
    
    await state.update_data(new_title=title)
    
    data = await state.get_data()
    anime = await get_anime(session, data['anime_id'])
    
    await message.answer(f"Текущее описание:\n<i>{anime.description}</i>\n\nВведите новое описание (или отправьте '-', чтобы оставить текущее):", parse_mode="HTML")
    await state.set_state(AdminEditAnime.waiting_for_new_description)

@router.message(AdminEditAnime.waiting_for_new_description)
async def edit_anime_desc(message: Message, state: FSMContext, session: AsyncSession):
    desc = message.text.strip()
    if desc == "-":
        desc = None
        
    data = await state.get_data()
    anime_id = data['anime_id']
    title = data.get('new_title')
    
    success = await update_anime(session, anime_id, title=title, description=desc)
    if success:
        await send_admin_log(message.bot, f"Админ <code>{message.from_user.id}</code> отредактировал название/описание аниме ID {anime_id}")
        await message.answer("Аниме успешно обновлено!", reply_markup=get_admin_menu())
    else:
        await message.answer("Ошибка при обновлении аниме.", reply_markup=get_admin_menu())
    await state.clear()

# --- Удаление серии ---
@router.message(F.text == "Удалить серию")
async def del_episode_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await message.answer("Введите Уникальный ID серии для удаления.\nМожно удалить несколько: через запятую (1, 3, 5) или диапазоном (10-15):", reply_markup=get_cancel_menu())
    await state.set_state(AdminDeleteEpisode.waiting_for_episode_id)

@router.message(AdminDeleteEpisode.waiting_for_episode_id)
async def del_episode_process(message: Message, state: FSMContext, session: AsyncSession):
    text = message.text.replace(" ", "")
    ids_to_delete = set()
    
    try:
        if "-" in text:
            parts = text.split("-")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                start, end = int(parts[0]), int(parts[1])
                ids_to_delete.update(range(start, end + 1))
            else:
                raise ValueError
        elif "," in text:
            parts = text.split(",")
            for p in parts:
                if p.isdigit():
                    ids_to_delete.add(int(p))
                else:
                    raise ValueError
        elif text.isdigit():
            ids_to_delete.add(int(text))
        else:
            raise ValueError
    except ValueError:
        return await message.answer("❌ Неверный формат. Используйте одно число (5), диапазон (5-10) или перечисление (1,5,7).")
    
    deleted_count = 0
    not_found_count = 0
    
    for ep_id in ids_to_delete:
        success = await delete_episode(session, ep_id)
        if success:
            deleted_count += 1
        else:
            not_found_count += 1
            
    if deleted_count > 0:
        ids_str = ", ".join(map(str, sorted(list(ids_to_delete))))
        await send_admin_log(message.bot, f"Админ <code>{message.from_user.id}</code> удалил серии (ID: {ids_str})")
        msg_text = f"✅ Успешно удалено серий: {deleted_count}."
        if not_found_count > 0:
            msg_text += f"\n⚠️ Не найдено серий: {not_found_count}."
        await message.answer(msg_text, reply_markup=get_admin_menu())
    else:
        await message.answer("❌ Ни одна серия не была найдена.", reply_markup=get_admin_menu())
        
    await state.clear()

# --- Создание папки ---
@router.message(F.text == "Создать папку")
async def add_folder_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await message.answer("Введите название папки:", reply_markup=get_cancel_menu())
    await state.set_state(AdminAddFolder.waiting_for_title)

@router.message(AdminAddFolder.waiting_for_title)
async def add_folder_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer("Введите описание папки:")
    await state.set_state(AdminAddFolder.waiting_for_description)

@router.message(AdminAddFolder.waiting_for_description)
async def add_folder_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Отправьте постер (фото) для папки:")
    await state.set_state(AdminAddFolder.waiting_for_photo)

@router.message(AdminAddFolder.waiting_for_photo, F.photo)
async def add_folder_photo(message: Message, state: FSMContext, session: AsyncSession):
    if message.media_group_id:
        data = await state.get_data()
        if data.get("last_media_group_id") == message.media_group_id: return
        await state.update_data(last_media_group_id=message.media_group_id)
        return await message.answer("Только одна фотография!")
    
    data = await state.get_data()
    photo_file_id = message.photo[-1].file_id
    folder = await add_folder(session, data['title'], data['description'], photo_file_id)
    await send_admin_log(message.bot, f"Админ <code>{message.from_user.id}</code> создал папку <b>{folder.title}</b> (ID {folder.id})")
    await message.answer(f"Папка '{folder.title}' создана! ID: {folder.id}", reply_markup=get_admin_menu())
    await state.clear()

# --- Удаление папки ---
@router.message(F.text == "Удалить папку")
async def delete_folder_start(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id): return
    folders = await get_all_folders(session)
    if not folders:
        return await message.answer("База данных папок пуста.", reply_markup=get_admin_menu())
    
    text = "📂 <b>Доступные папки:</b>\n"
    for f in folders:
        text += f"ID {f.id}: {f.title}\n"
        
    await message.answer(text + "\nВведите ID папки для удаления:", reply_markup=get_cancel_menu(), parse_mode="HTML")
    await state.set_state(AdminDeleteFolder.waiting_for_folder_id)

@router.message(AdminDeleteFolder.waiting_for_folder_id)
async def delete_folder_process(message: Message, state: FSMContext, session: AsyncSession):
    if not message.text.isdigit():
        return await message.answer("ID должен быть числом.")
    
    folder_id = int(message.text)
    success = await delete_folder(session, folder_id)
    if success:
        await send_admin_log(message.bot, f"Админ <code>{message.from_user.id}</code> удалил папку ID {folder_id}")
        await message.answer(f"Папка с ID {folder_id} успешно удалена.", reply_markup=get_admin_menu())
    else:
        await message.answer(f"Папка с ID {folder_id} не найдена.", reply_markup=get_admin_menu())
    await state.clear()

# --- Привязка аниме к папке ---
@router.message(F.text == "Привязать аниме к папке")
async def link_anime_start(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id): return
    folders = await get_all_folders(session)
    if not folders:
        return await message.answer("Сначала создайте хотя бы одну папку.")
    
    text = "Доступные папки:\n" + "\n".join([f"{f.id}. {f.title}" for f in folders])
    await message.answer(text + "\n\nВведите ID папки:", reply_markup=get_cancel_menu())
    await state.set_state(AdminLinkAnime.waiting_for_folder_id)

@router.message(AdminLinkAnime.waiting_for_folder_id)
async def link_anime_folder_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("ID должен быть числом.")
    await state.update_data(folder_id=int(message.text))
    await message.answer("Введите ID аниме для привязки:")
    await state.set_state(AdminLinkAnime.waiting_for_anime_id)

@router.message(AdminLinkAnime.waiting_for_anime_id)
async def link_anime_process(message: Message, state: FSMContext, session: AsyncSession):
    if not message.text.isdigit():
        return await message.answer("ID должен быть числом.")
    
    data = await state.get_data()
    success = await link_anime_to_folder(session, data['folder_id'], int(message.text))
    if success:
        await send_admin_log(message.bot, f"Админ <code>{message.from_user.id}</code> привязал аниме ID {message.text} к папке ID {data['folder_id']}")
        await message.answer("Аниме успешно привязано к папке!", reply_markup=get_admin_menu())
    else:
        await message.answer("Ошибка привязки (возможно уже привязано).", reply_markup=get_admin_menu())
    await state.clear()
