import html
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import logging
import datetime
from config import ADMIN_IDS, SUPERADMIN_IDS
from states.fsm import AdminAddAnime, AdminAddEpisode, AdminDeleteAnime, AdminDeleteEpisode, AdminAddFolder, AdminLinkAnime, AdminDeleteFolder, AdminListEpisodes, AdminEditAnime, AdminMassUpload, AdminEditFolder, AdminUnlinkAnime, AdminEditEpisode, AdminEditVoiceover, AdminDeleteVoiceover, AdminQuickEditEpisode, AdminMassEditEpisodeDesc, AdminCopyDescriptions
from database.requests import add_anime, add_episode, get_all_anime, get_all_users, delete_anime, delete_episode, get_anime_by_title, add_folder, get_all_folders, link_anime_to_folder, get_folder_for_anime, delete_folder, get_episodes, get_anime, update_anime, update_folder, unlink_anime_from_folder, get_folder, get_anime_in_folder, get_episode, get_anime_by_display_id
from keyboards.reply import get_admin_menu, get_main_menu, get_cancel_menu, get_quality_keyboard, get_finish_upload_menu, get_admin_anime_menu, get_admin_episodes_menu, get_admin_folders_menu, get_edit_episode_menu
from keyboards.inline import get_folder_animes_keyboard, get_admin_voiceovers_inline_keyboard

router = Router()

async def get_anime_by_index(session, index_str: str):
    if not index_str.isdigit(): return None
    idx = int(index_str) - 1
    if idx < 0: return None
    from database.requests import get_all_anime
    animes = await get_all_anime(session)
    if idx >= len(animes): return None
    return animes[idx]




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

@router.message(Command("ad"))
async def cmd_ad(message: Message, command: CommandObject, session: AsyncSession):
    if not is_admin(message.from_user.id): return
    if not command.args:
        return await message.answer("❌ Напишите текст для рассылки после команды /ad.")
        
    users = await get_all_users(session)
    count = 0
    await message.answer("⏳ Начинаю рассылку...")
    for u in users:
        try:
            await message.bot.send_message(u.telegram_id, command.args, parse_mode="HTML")
            count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
            
    await message.answer(f"✅ Рассылка завершена. Доставлено {count} пользователям.")

@router.message(Command("superadmin"))
async def cmd_superadmin(message: Message, command: CommandObject, session: AsyncSession):
    if not is_superadmin(message.from_user.id):
        return
        
    if not command.args:
        help_text = (
            "Использование:\n"
            "/superadmin add [ID]\n"
            "/superadmin remove [ID]\n"
            "/superadmin upgrade [ID]\n"
            "/superadmin premium gift [дни] [@username]\n"
            "/superadmin premium del [@username]"
        )
        return await message.answer(help_text)
        
    args = command.args.split()
    
    if args[0] == "upgrade" and len(args) > 1:
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

    if args[0] == "remove" and len(args) > 1:
        remove_id_str = args[1].replace('"', '').replace("'", "")
        if remove_id_str.isdigit():
            remove_id = int(remove_id_str)
            if remove_id in ADMIN_IDS:
                ADMIN_IDS.remove(remove_id)
                try:
                    with open(".env", "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    
                    with open(".env", "w", encoding="utf-8") as f:
                        for line in lines:
                            if line.startswith("ADMIN_IDS="):
                                current_ids = [int(x) for x in line.strip().split("=")[1].split(",") if x]
                                if remove_id in current_ids:
                                    current_ids.remove(remove_id)
                                f.write(f"ADMIN_IDS={','.join(map(str, current_ids))}\n")
                            else:
                                f.write(line)
                    await message.answer(f"✅ Пользователь {remove_id} удален из администраторов.")
                except Exception as e:
                    await message.answer(f"Ошибка при сохранении: {e}")
            else:
                await message.answer("⚠️ Этот пользователь не является администратором.")
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

    if args[0] == "premium" and len(args) > 1:
        from database.requests import get_user_by_username
        from datetime import datetime, timedelta
        
        action = args[1]
        
        if action == "gift" and len(args) == 4:
            days = args[2]
            target_username = args[3].replace("@", "")
            if days.isdigit():
                target_user = await get_user_by_username(session, target_username)
                if target_user:
                    now = datetime.utcnow()
                    if target_user.is_premium and target_user.premium_until and target_user.premium_until > now:
                        new_until = target_user.premium_until + timedelta(days=int(days))
                    else:
                        new_until = now + timedelta(days=int(days))
                    
                    target_user.is_premium = True
                    target_user.premium_until = new_until
                    await session.commit()
                    
                    await message.answer(f"✅ Пользователю {target_username} выдана подписка на {days} дней!")
                    try:
                        await message.bot.send_message(
                            target_user.telegram_id, 
                            f"🎉 <b>Вам подарили премиум подписку!</b>\n\nДлительность: <b>{days} дней</b>.\nНаслаждайтесь просмотром!", 
                            parse_mode="HTML"
                        )
                    except:
                        pass
                else:
                    await message.answer("❌ Пользователь с таким юзернеймом не найден в базе.")
            else:
                await message.answer("❌ Количество дней должно быть числом.")
            return
            
        elif action == "del" and len(args) == 3:
            target_username = args[2].replace("@", "")
            target_user = await get_user_by_username(session, target_username)
            if target_user:
                target_user.is_premium = False
                target_user.premium_until = None
                await session.commit()
                await message.answer(f"✅ У пользователя {target_username} успешно аннулирована подписка.")
            else:
                await message.answer("❌ Пользователь с таким юзернеймом не найден в базе.")
            return
            
        await message.answer("❌ Неверный формат команды. Используйте /superadmin premium gift или /superadmin premium del")
        return
        
@router.message(Command("admin"))
async def cmd_admin(message: Message, command: CommandObject, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return

    if command.args and command.args.strip().lower() == "tos all":
        from sqlalchemy import update
        from database.models import User
        await session.execute(update(User).values(has_accepted_tos=False))
        await session.commit()
        await message.answer("✅ Статус TOS сброшен для всех пользователей. При следующем вызове /start они должны будут принять соглашение заново.")
        return

    if command.args and command.args.strip().lower() == "help":
        help_text = (
            "🛠 <b>Доступные команды администратора:</b>\n\n"
            "<code>/admin</code> — Открыть панель управления\n"
            "<code>/logs</code> — Получить файл с логами действий админов\n"
            "<code>/ad [текст]</code> — Сделать рассылку всем пользователям бота\n"
            "<code>/edit</code> — Быстро изменить описание серии (отправьте при просмотре)\n"
            "<code>/clear_logs</code> — Удалить старые логи ошибок из чата\n\n"
        )
        if is_superadmin(message.from_user.id):
            help_text += (
                "👑 <b>Команды суперадминистратора:</b>\n"
                "<code>/superadmin add [ID]</code> — Назначить нового администратора\n"
                "<code>/superadmin remove [ID]</code> — Удалить администратора\n"
                "<code>/superadmin upgrade [ID]</code> — Назначить суперадминистратора\n"
                "<code>/superadmin premium gift [дни] [@username]</code> — Выдать премиум пользователю\n"
                "<code>/superadmin premium del [@username]</code> — Забрать премиум у пользователя\n"
            )
        return await message.answer(help_text, parse_mode="HTML")

    await message.answer("Панель администратора", reply_markup=get_admin_menu())

@router.message(F.text == "🔙 В главное меню")
async def exit_admin_mode(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await state.clear()
    await message.answer("Вы вышли в главное меню", reply_markup=get_main_menu())

@router.message(F.text == "🎬 Управление Аниме")
async def admin_anime_menu(message: Message):
    if not is_admin(message.from_user.id): return
    await message.answer("Меню управления аниме:", reply_markup=get_admin_anime_menu())

@router.message(F.text == "📺 Управление Сериями")
async def admin_episodes_menu(message: Message):
    if not is_admin(message.from_user.id): return
    await message.answer("Меню управления сериями:", reply_markup=get_admin_episodes_menu())

@router.message(F.text == "📁 Управление Папками")
async def admin_folders_menu(message: Message):
    if not is_admin(message.from_user.id): return
    await message.answer("Меню управления папками:", reply_markup=get_admin_folders_menu())

@router.message(F.text == "↩️ Назад в админку")
async def back_to_admin_menu(message: Message):
    if not is_admin(message.from_user.id): return
    await message.answer("Админ-панель:", reply_markup=get_admin_menu())

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
        folder_text = f" (Папка <code>{folder.id}</code>)" if folder else " (Без папки)"
        star = "💎 " if getattr(a, 'is_4k', False) else ""
        movie = '🎥 ' if getattr(a, 'display_id', '') and str(getattr(a, 'display_id', '')).endswith('_3') else ''
        text += f"<code>{a.display_id}</code>. {star}{movie}{html.escape(a.title)}{folder_text}\n"
    
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "📥 Экспорт базы (CSV)")
async def admin_export_csv(message: Message, session: AsyncSession):
    if not is_admin(message.from_user.id): return
    animes = await get_all_anime(session)
    if not animes:
        return await message.answer("База данных аниме пуста.")
        
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["ID", "Название", "Качество", "ID Папки"])
    
    for a in animes:
        folder = await get_folder_for_anime(session, a.id)
        folder_id = folder.id if folder else "Без папки"
        quality = "4K" if getattr(a, 'is_4k', False) else "1080p"
        
        # Записываем display_id если он есть, иначе обычный id
        anime_id = getattr(a, 'display_id', a.id) or a.id
        writer.writerow([anime_id, a.title, quality, folder_id])
        
    csv_bytes = output.getvalue().encode('utf-8-sig') # utf-8-sig for excel compatibility
    file = BufferedInputFile(csv_bytes, filename="anime_database.csv")
    
    await message.answer_document(
        document=file,
        caption="📥 <b>Экспорт базы данных аниме</b>\n\nФайл в формате CSV. Отлично открывается в Excel или Google Sheets (разделитель - точка с запятой).",
        parse_mode="HTML"
    )

@router.message(F.text == "👥 Список пользователей")
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
    
    text = "Доступные аниме:\n" + "\n".join([f"<code>{a.display_id}</code>. {'💎 ' if getattr(a, 'is_4k', False) else ''}{html.escape(a.title)}" for a in animes])
    await message.answer(text + "\n\nВведите номер аниме из списка для просмотра его серий:", reply_markup=get_cancel_menu(), parse_mode="HTML")
    await state.set_state(AdminListEpisodes.waiting_for_anime_id)

@router.message(AdminListEpisodes.waiting_for_anime_id)
async def admin_list_episodes_process(message: Message, state: FSMContext, session: AsyncSession):
    display_id = message.text.strip()
    anime = await get_anime_by_display_id(session, display_id)
    if not anime:
        return await message.answer("Аниме с таким ID не найдено.", reply_markup=get_admin_menu())
    anime_id = anime.id
    
    episodes = await get_episodes(session, anime_id)
    if not episodes:
        await message.answer(f"В аниме '{anime.title}' пока нет залитых серий.", reply_markup=get_admin_menu())
    else:
        text = f"📺 <b>Список серий аниме '{anime.title}':</b>\n\n"
        for ep in episodes:
            text += f"<code>{ep.id}</code>. Серия {ep.episode_number}\n"
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
async def add_anime_title(message: Message, state: FSMContext):
    title = message.text.strip()
    await state.update_data(title=title)
    await message.answer("Введите кастомный ID для этого аниме (например 4_1, 4_2 или просто число):", reply_markup=get_cancel_menu())
    await state.set_state(AdminAddAnime.waiting_for_display_id)

@router.message(AdminAddAnime.waiting_for_display_id)
async def add_anime_display_id(message: Message, state: FSMContext, session: AsyncSession):
    display_id = message.text.strip()
    existing = await get_anime_by_display_id(session, display_id)
    if existing:
        return await message.answer("Аниме с таким кастомным ID уже существует. Введите другой ID:")
    await state.update_data(display_id=display_id)
    await message.answer("Введите описание аниме:")
    await state.set_state(AdminAddAnime.waiting_for_description)

@router.message(AdminAddAnime.waiting_for_description)
async def add_anime_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    
    data = await state.get_data()
    display_id = data.get('display_id', '')
    is_4k = "_2" in display_id
    await state.update_data(is_4k=is_4k)
    
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
        
    photo_file_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=photo_file_id)
    
    await message.answer("Введите скрытые теги (алиасы) для поиска через запятую (или отправьте '-', если их нет):", reply_markup=get_cancel_menu())
    await state.set_state(AdminAddAnime.waiting_for_aliases)

@router.message(AdminAddAnime.waiting_for_aliases)
async def add_anime_aliases(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    aliases = None
    if message.text.strip() != "-":
        aliases = message.text.strip()
        
    anime = await add_anime(
        session, 
        data['title'], 
        data['description'], 
        data['photo_file_id'], 
        data.get('is_4k', False), 
        data.get('display_id'),
        aliases=aliases
    )
    await send_admin_log(message.bot, f"Админ <code>{message.from_user.id}</code> добавил аниме <b>{anime.title}</b> (ID <code>{anime.display_id}</code>)")
    await message.answer(f"Аниме '{anime.title}' успешно добавлено! ID: <code>{anime.display_id}</code>", reply_markup=get_admin_menu(), parse_mode="HTML")
    await state.clear()

# --- Добавление серии ---
@router.message(F.text == "Добавить серию")
async def add_episode_start(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id): return
    animes = await get_all_anime(session)
    if not animes:
        return await message.answer("Сначала добавьте хотя бы одно аниме.")
    
    text = "Доступные аниме:\n" + "\n".join([f"<code>{a.display_id}</code>. {'💎 ' if getattr(a, 'is_4k', False) else ''}{html.escape(a.title)}" for a in animes])
    await message.answer(text + "\n\nВведите номер аниме из списка:", reply_markup=get_cancel_menu(), parse_mode="HTML")
    await state.set_state(AdminAddEpisode.waiting_for_anime_id)

@router.message(AdminAddEpisode.waiting_for_anime_id)
async def add_episode_anime_id(message: Message, state: FSMContext, session: AsyncSession):
    display_id = message.text.strip()
    anime = await get_anime_by_display_id(session, display_id)
    if not anime:
        return await message.answer("Аниме с таким ID не найдено. Попробуйте еще раз:")
    await state.update_data(anime_id=anime.id)
    await message.answer("Введите номер серии:")
    await state.set_state(AdminAddEpisode.waiting_for_episode_number)

@router.message(AdminAddEpisode.waiting_for_episode_number)
async def add_episode_num(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("ID должен быть числом. Попробуйте еще раз:")
    await state.update_data(episode_number=int(message.text))
    await message.answer("Отправьте описание серии (или отправьте тире '-', если описания нет):")
    await state.set_state(AdminAddEpisode.waiting_for_episode_description)

@router.message(AdminAddEpisode.waiting_for_episode_description)
async def add_episode_desc(message: Message, state: FSMContext):
    await state.update_data(episode_description=message.text)
    await message.answer("Выберите озвучку из списка ниже:", reply_markup=get_admin_voiceovers_inline_keyboard())
    await message.answer("Или введите название вручную (для пропуска отправьте '-'):", reply_markup=get_cancel_menu())
    await state.set_state(AdminAddEpisode.waiting_for_voiceover_name)

@router.message(AdminAddEpisode.waiting_for_voiceover_name)
async def add_episode_voiceover(message: Message, state: FSMContext):
    await state.update_data(voiceover_name=message.text.strip())
    await message.answer("Отправьте или перешлите видео-файл серии:", reply_markup=get_cancel_menu())
    await state.set_state(AdminAddEpisode.waiting_for_video)

@router.callback_query(F.data.startswith("adminvo_"))
async def process_admin_voiceover_inline(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    vo_name = callback.data.replace("adminvo_", "")
    current_state = await state.get_state()
    
    if current_state == AdminAddEpisode.waiting_for_voiceover_name.state:
        await state.update_data(voiceover_name=vo_name)
        await callback.message.edit_text(f"✅ Выбрана озвучка: <b>{vo_name}</b>", parse_mode="HTML")
        await callback.message.answer("Отправьте или перешлите видео-файл серии:", reply_markup=get_cancel_menu())
        await state.set_state(AdminAddEpisode.waiting_for_video)
        await callback.answer()
        
    elif current_state == AdminMassUpload.waiting_for_voiceover_name.state:
        from database.requests import get_or_create_voiceover
        import html
        from database.requests import get_anime
        data = await state.get_data()
        
        vo_id = None
        if vo_name != "-":
            vo = await get_or_create_voiceover(session, data['anime_id'], vo_name)
            vo_id = vo.id
            display_vo = html.escape(vo.name)
        else:
            display_vo = "Без озвучки"
            
        await state.update_data(voiceover_id=vo_id, voiceover_name=vo_name)
        anime = await get_anime(session, data['anime_id'])
        
        await callback.message.edit_text(f"✅ Выбрана озвучка: <b>{display_vo}</b>", parse_mode="HTML")
        
        msg_text = (
            f"✅ Выбрано аниме: <b>{anime.title}</b>\n"
            f"🎙 Озвучка: <b>{display_vo}</b>\n\n"
            "Теперь отправляйте видеофайлы или альбомы видео. "
            "Бот автоматически извлечет номер серии из названия файла "
            "(например: <code>1.mp4</code> или <code>серия 2.mp4</code>).\n\n"
            "Обязательно отправляйте видео <b>с компьютера</b> или <b>как файл (без сжатия)</b>, "
            "чтобы Telegram не переименовал их."
        )
        from keyboards.reply import get_finish_upload_menu
        await callback.message.answer(msg_text, reply_markup=get_finish_upload_menu(), parse_mode="HTML")
        await state.set_state(AdminMassUpload.waiting_for_videos)
        await callback.answer()
    else:
        await callback.answer("Это действие сейчас недоступно.")

@router.message(AdminAddEpisode.waiting_for_video, F.video)
async def add_episode_video(message: Message, state: FSMContext, session: AsyncSession):
    from database.requests import get_or_create_voiceover
    data = await state.get_data()
    video_file_id = message.video.file_id
    
    vo_name = data['voiceover_name']
    vo_id = None
    
    if vo_name != "-":
        vo = await get_or_create_voiceover(session, data['anime_id'], vo_name)
        vo_id = vo.id
        display_vo = html.escape(vo.name)
    else:
        display_vo = "Без озвучки"
        
    await add_episode(session, data['anime_id'], data['episode_number'], video_file_id, data['episode_description'], vo_id)
    await send_admin_log(message.bot, f"Админ <code>{message.from_user.id}</code> добавил серию {data['episode_number']} ({display_vo}) для аниме ID {data['anime_id']}")
    await message.answer(f"Серия {data['episode_number']} ({display_vo}) успешно добавлена!", reply_markup=get_admin_menu())
    await state.clear()

# --- Редактирование серии ---
@router.message(F.text == "Редактировать серию")
async def edit_episode_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await message.answer("Введите номер аниме из списка:", reply_markup=get_cancel_menu())
    await state.set_state(AdminEditEpisode.waiting_for_anime_id)

@router.message(AdminEditEpisode.waiting_for_anime_id)
async def edit_episode_anime_id(message: Message, state: FSMContext, session: AsyncSession):
    display_id = message.text.strip()
    anime = await get_anime_by_display_id(session, display_id)
    if not anime:
        await message.answer("Аниме с таким ID не найдено.", reply_markup=get_admin_menu())
        return await state.clear()
        
    from database.requests import get_voiceovers
    voiceovers = await get_voiceovers(session, anime.id)
    if not voiceovers:
        await message.answer("У этого аниме пока нет озвучек.", reply_markup=get_admin_menu())
        return await state.clear()
        
    await state.update_data(anime_id=anime.id)
    
    text = "Выберите ID озвучки:\n"
    for vo in voiceovers:
        text += f"<code>{vo.id}</code>. {html.escape(vo.name)}\n"
        
    await message.answer(text, parse_mode="HTML")
    await state.set_state(AdminEditEpisode.waiting_for_voiceover_id)

@router.message(AdminEditEpisode.waiting_for_voiceover_id)
async def edit_episode_vo_id(message: Message, state: FSMContext, session: AsyncSession):
    if not message.text.isdigit():
        return await message.answer("ID должен быть числом.")
    vo_id = int(message.text)
    
    data = await state.get_data()
    from database.requests import get_voiceovers
    voiceovers = await get_voiceovers(session, data['anime_id'])
    if vo_id not in [v.id for v in voiceovers]:
        return await message.answer("Неверный ID озвучки. Попробуйте еще раз:")
        
    await state.update_data(voiceover_id=vo_id)
    await message.answer("Введите номер серии для редактирования:")
    await state.set_state(AdminEditEpisode.waiting_for_episode_number)

@router.message(AdminEditEpisode.waiting_for_episode_number)
async def edit_episode_number(message: Message, state: FSMContext, session: AsyncSession):
    try:
        if not message.text.isdigit():
            return await message.answer("ID должен быть числом.")
        ep_num = int(message.text)
        data = await state.get_data()
        
        vo_id = data.get('voiceover_id')
        if not vo_id:
            await message.answer("Сессия устарела. Начните заново из меню.", reply_markup=get_admin_menu())
            return await state.clear()
            
        episode = await get_episode(session, data['anime_id'], ep_num, vo_id)
        if not episode:
            await message.answer(f"Серия {ep_num} у этого аниме не найдена.", reply_markup=get_admin_menu())
            return await state.clear()
            
        await state.update_data(episode_number=ep_num)
        await message.answer("Что вы хотите изменить?", reply_markup=get_edit_episode_menu())
        await state.set_state(AdminEditEpisode.waiting_for_field)
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        await message.answer(f"Произошла ошибка:\n<pre>{err}</pre>", parse_mode="HTML")

@router.message(AdminEditEpisode.waiting_for_field)
async def edit_episode_field(message: Message, state: FSMContext):
    if message.text == "Видео":
        await message.answer("Отправьте новое видео:", reply_markup=get_cancel_menu())
        await state.set_state(AdminEditEpisode.waiting_for_new_video)
    elif message.text == "Описание":
        await message.answer("Отправьте новое описание (или '-' чтобы удалить текущее):", reply_markup=get_cancel_menu())
        await state.set_state(AdminEditEpisode.waiting_for_new_description)
    else:
        await message.answer("Пожалуйста, выберите опцию на клавиатуре.")

@router.message(AdminEditEpisode.waiting_for_new_video, F.video)
async def edit_episode_video(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    vo_id = data.get('voiceover_id')
    if not vo_id: return await state.clear()
    video_file_id = message.video.file_id
    
    episode = await get_episode(session, data['anime_id'], data['episode_number'], vo_id)
    episode.tg_file_id = video_file_id
    await session.commit()
    
    await send_admin_log(message.bot, f"Админ <code>{message.from_user.id}</code> обновил видео серии {data['episode_number']} для аниме ID {data['anime_id']}")
    await message.answer("Видео серии успешно обновлено!", reply_markup=get_admin_menu())
    await state.clear()

@router.message(AdminEditEpisode.waiting_for_new_description)
async def edit_episode_desc(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    vo_id = data.get('voiceover_id')
    if not vo_id: return await state.clear()
    new_desc = message.text if message.text != "-" else None
    
    episode = await get_episode(session, data['anime_id'], data['episode_number'], vo_id)
    episode.description = new_desc
    await session.commit()
    
    await send_admin_log(message.bot, f"Админ <code>{message.from_user.id}</code> обновил описание серии {data['episode_number']} для аниме ID {data['anime_id']}")
    await message.answer("Описание серии успешно обновлено!", reply_markup=get_admin_menu())
    await state.clear()

# --- Удаление аниме ---
@router.message(F.text == "Удалить аниме")
async def del_anime_start(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id): return
    from database.requests import get_all_anime
    animes = await get_all_anime(session)
    import html
    text = "Доступные аниме:\n" + "\n".join([f"<code>{a.display_id}</code>. {'💎 ' if getattr(a, 'is_4k', False) else ''}{html.escape(a.title)}" for a in animes])
    await message.answer(text + "\n\nВведите номер аниме из списка для удаления:", reply_markup=get_cancel_menu(), parse_mode="HTML")
    await state.set_state(AdminDeleteAnime.waiting_for_anime_id)

@router.message(AdminDeleteAnime.waiting_for_anime_id)
async def del_anime_process_id(message: Message, state: FSMContext, session: AsyncSession):
    display_id = message.text.strip()
    anime = await get_anime_by_display_id(session, display_id)
    if not anime:
        await message.answer(f"Аниме с ID {display_id} не найдено.", reply_markup=get_admin_menu())
        await state.clear()
        return
        
    anime_id = anime.id
    await state.update_data(anime_id=anime_id)
    await message.answer(
        f"Вы собираетесь безвозвратно удалить аниме <b>{anime.title}</b> (ID {display_id}) и все его серии!\n\n"
        "Вы точно уверены? Напишите:\n<code>Да, я беру ответственность на себя</code>\n\n"
        "(Или нажмите кнопку Отмена)", 
        parse_mode="HTML"
    )
    await state.set_state(AdminDeleteAnime.waiting_for_confirmation)

@router.message(AdminDeleteAnime.waiting_for_confirmation)
async def del_anime_process_confirm(message: Message, state: FSMContext, session: AsyncSession):
    if message.text.strip().lower() != "да, я беру ответственность на себя" and message.text.strip().lower() != "да, я беру ответсвтвенность на себя":
        await message.answer("Удаление отменено. Текст подтверждения не совпадает.", reply_markup=get_admin_menu())
        await state.clear()
        return
        
    data = await state.get_data()
    anime_id = data.get("anime_id")
    
    success = await delete_anime(session, anime_id)
    if success:
        await send_admin_log(message.bot, f"Админ <code>{message.from_user.id}</code> удалил аниме ID {anime_id}")
        await message.answer(f"Аниме с ID {anime_id} и все его серии успешно удалены.", reply_markup=get_admin_menu())
    else:
        await message.answer("Произошла ошибка при удалении.", reply_markup=get_admin_menu())
    await state.clear()

# --- Редактирование аниме ---
@router.message(F.text == "Редактировать аниме")
async def edit_anime_start(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id): return
    from database.requests import get_all_anime
    animes = await get_all_anime(session)
    import html
    text = "Доступные аниме:\n" + "\n".join([f"<code>{a.display_id}</code>. {'💎 ' if getattr(a, 'is_4k', False) else ''}{html.escape(a.title)}" for a in animes])
    await message.answer(text + "\n\nВведите номер аниме из списка для редактирования:", reply_markup=get_cancel_menu(), parse_mode="HTML")
    await state.set_state(AdminEditAnime.waiting_for_anime_id)

@router.message(AdminEditAnime.waiting_for_anime_id)
async def edit_anime_id(message: Message, state: FSMContext, session: AsyncSession):
    display_id = message.text.strip()
    anime = await get_anime_by_display_id(session, display_id)
    if not anime:
        return await message.answer("Аниме не найдено.", reply_markup=get_admin_menu())
    anime_id = anime.id
    
    await state.update_data(anime_id=anime_id)
    await message.answer(f"Текущий кастомный ID: <b>{anime.display_id}</b>\nВведите новый кастомный ID (или отправьте '-', чтобы оставить текущий):", parse_mode="HTML")
    await state.set_state(AdminEditAnime.waiting_for_new_display_id)


@router.message(AdminEditAnime.waiting_for_new_display_id)
async def edit_anime_display_id(message: Message, state: FSMContext, session: AsyncSession):
    new_id = message.text.strip()
    if new_id != "-":
        existing = await get_anime_by_display_id(session, new_id)
        if existing:
            return await message.answer("Аниме с таким кастомным ID уже существует. Введите другой ID (или '-' чтобы пропустить):")
        await state.update_data(new_display_id=new_id)
    
    data = await state.get_data()
    anime = await get_anime(session, data['anime_id'])
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
        
    await state.update_data(new_description=desc)
    
    await message.answer("Отправьте новый постер (картинку) для аниме (или отправьте '-', чтобы оставить текущий):", parse_mode="HTML")
    await state.set_state(AdminEditAnime.waiting_for_new_photo)

@router.message(AdminEditAnime.waiting_for_new_photo, F.photo | F.text)
async def edit_anime_photo(message: Message, state: FSMContext, session: AsyncSession):
    if message.photo:
        photo_id = message.photo[-1].file_id
    elif message.text and message.text.strip() == "-":
        photo_id = None
    else:
        return await message.answer("Пожалуйста, отправьте картинку или '-', чтобы оставить текущую.")
        
    await state.update_data(new_photo_id=photo_id)
    
    data = await state.get_data()
    anime = await get_anime(session, data['anime_id'])
    
    current_aliases = anime.aliases if anime.aliases else "Нет"
    await message.answer(f"Текущие теги (алиасы): <b>{current_aliases}</b>\nВведите новые скрытые теги через запятую (или '-', чтобы оставить текущие, или 'удалить' чтобы очистить):", parse_mode="HTML")
    await state.set_state(AdminEditAnime.waiting_for_new_aliases)

@router.message(AdminEditAnime.waiting_for_new_aliases)
async def edit_anime_aliases(message: Message, state: FSMContext, session: AsyncSession):
    aliases_text = message.text.strip()
    
    data = await state.get_data()
    anime_id = data['anime_id']
    title = data.get('new_title')
    desc = data.get('new_description')
    display_id = data.get('new_display_id')
    photo_id = data.get('new_photo_id')
    
    aliases = None
    if aliases_text.lower() == "удалить":
        aliases = "-" # в update_anime "-" означает очистку
    elif aliases_text != "-":
        aliases = aliases_text
        
    success = await update_anime(session, anime_id, title=title, description=desc, display_id=display_id, photo_file_id=photo_id, aliases=aliases)
    if success:
        await send_admin_log(message.bot, f"Админ <code>{message.from_user.id}</code> отредактировал информацию аниме ID {anime_id}")
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

# --- Массовое редактирование описаний серий ---
@router.message(F.text == "Масс. смена описаний")
async def mass_edit_episode_desc_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    msg = (
        "Введите Уникальные ID серий и новое описание через разделитель <code>|</code>\n\n"
        "Формат:\n"
        "<code>ID, ID, ID-ID | Новое описание</code>\n\n"
        "Примеры:\n"
        "<code>1, 2, 5-10 | Крутое описание для этих серий</code>\n"
        "<code>15 | Описание только для 15 серии</code>\n\n"
        "Если отправить <code>-</code> вместо описания, оно будет очищено."
    )
    await message.answer(msg, reply_markup=get_cancel_menu(), parse_mode="HTML")
    await state.set_state(AdminMassEditEpisodeDesc.waiting_for_data)

@router.message(AdminMassEditEpisodeDesc.waiting_for_data)
async def mass_edit_episode_desc_process(message: Message, state: FSMContext, session: AsyncSession):
    text = message.text
    if "|" not in text:
        return await message.answer("❌ Ошибка формата. Пожалуйста, используйте разделитель | (например: 1, 2-5 | описание)")
        
    lines = text.strip().split('\n')
    from database.models import Episode
    
    updated_count = 0
    errors = []
    
    for line_idx, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        if "|" not in line:
            errors.append(f"Строка {line_idx}: нет разделителя |")
            continue
            
        parts = line.split("|", 1)
        ids_str = parts[0].replace(" ", "")
        new_desc = parts[1].strip()
        
        if new_desc == "-":
            new_desc = None
            
        ids_to_edit = set()
        try:
            for part in ids_str.split(","):
                if not part: continue
                if "-" in part:
                    sparts = part.split("-")
                    if len(sparts) == 2 and sparts[0].isdigit() and sparts[1].isdigit():
                        start, end = int(sparts[0]), int(sparts[1])
                        ids_to_edit.update(range(start, end + 1))
                    else:
                        raise ValueError
                elif part.isdigit():
                    ids_to_edit.add(int(part))
                else:
                    raise ValueError
        except ValueError:
            errors.append(f"Строка {line_idx}: Неверный формат ID ({ids_str})")
            continue
            
        for ep_id in ids_to_edit:
            ep = await session.get(Episode, ep_id)
            if ep:
                ep.description = new_desc
                updated_count += 1
            else:
                errors.append(f"ID {ep_id}: серия не найдена")
                
    await session.commit()
    
    msg = f"✅ Успешно обновлено описаний: {updated_count}."
    if errors:
        msg += "\n\n⚠️ Замечания:\n" + "\n".join(errors[:10])
        if len(errors) > 10:
            msg += f"\n...и еще {len(errors) - 10} ошибок."
            
    await send_admin_log(message.bot, f"Админ <code>{message.from_user.id}</code> массово изменил описание для {updated_count} серий.")
    await message.answer(msg, reply_markup=get_admin_menu())
    await state.clear()

# --- Редактирование озвучки ---
@router.message(F.text == "Редактировать озвучку")
async def edit_voiceover_start(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id): return
    from database.requests import get_all_anime
    animes = await get_all_anime(session)
    text = "Доступные аниме:\n" + "\n".join([f"<code>{a.display_id}</code>. {'💎 ' if getattr(a, 'is_4k', False) else ''}{html.escape(a.title)}" for a in animes])
    await message.answer(text + "\n\nВведите номер аниме из списка:", reply_markup=get_cancel_menu(), parse_mode="HTML")
    await state.set_state(AdminEditVoiceover.waiting_for_anime_id)

@router.message(AdminEditVoiceover.waiting_for_anime_id)
async def edit_voiceover_anime_id(message: Message, state: FSMContext, session: AsyncSession):
    display_id = message.text.strip()
    anime = await get_anime_by_display_id(session, display_id)
    if not anime:
        return await message.answer("Аниме не найдено.")
    anime_id = anime.id
    from database.requests import get_voiceovers
    voiceovers = await get_voiceovers(session, anime_id)
    if not voiceovers:
        return await message.answer("У этого аниме нет озвучек.", reply_markup=get_admin_menu())
        
    await state.update_data(anime_id=anime_id)
    text = "Выберите ID озвучки для переименования:\n\n"
    for vo in voiceovers:
        text += f"<code>{vo.id}</code>. {html.escape(vo.name)}\n"
    await message.answer(text, parse_mode="HTML")
    await state.set_state(AdminEditVoiceover.waiting_for_voiceover_id)

@router.message(AdminEditVoiceover.waiting_for_voiceover_id)
async def edit_voiceover_id(message: Message, state: FSMContext, session: AsyncSession):
    if not message.text.isdigit():
        return await message.answer("ID должен быть числом.")
    from database.requests import get_voiceover
    vo = await get_voiceover(session, int(message.text))
    if not vo:
        return await message.answer("Озвучка не найдена.")
        
    await state.update_data(voiceover_id=vo.id)
    await message.answer(f"Текущее название: {html.escape(vo.name)}\nОтправьте новое название:")
    await state.set_state(AdminEditVoiceover.waiting_for_new_name)

@router.message(AdminEditVoiceover.waiting_for_new_name)
async def edit_voiceover_new_name(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    from database.requests import get_voiceover
    vo = await get_voiceover(session, data['voiceover_id'])
    old_name = vo.name
    vo.name = message.text
    await session.commit()
    
    await send_admin_log(message.bot, f"Админ <code>{message.from_user.id}</code> переименовал озвучку {data['voiceover_id']} ({old_name} -> {html.escape(vo.name)})")
    await message.answer(f"✅ Название озвучки изменено на {html.escape(vo.name)}", reply_markup=get_admin_menu())
    await state.clear()

# --- Удаление озвучки ---
@router.message(F.text == "Удалить озвучку")
async def delete_voiceover_start(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id): return
    from database.requests import get_all_anime
    animes = await get_all_anime(session)
    text = "Доступные аниме:\n" + "\n".join([f"<code>{a.display_id}</code>. {'💎 ' if getattr(a, 'is_4k', False) else ''}{html.escape(a.title)}" for a in animes])
    await message.answer(text + "\n\nВведите номер аниме из списка:", reply_markup=get_cancel_menu(), parse_mode="HTML")
    await state.set_state(AdminDeleteVoiceover.waiting_for_anime_id)

@router.message(AdminDeleteVoiceover.waiting_for_anime_id)
async def delete_voiceover_anime_id(message: Message, state: FSMContext, session: AsyncSession):
    display_id = message.text.strip()
    anime = await get_anime_by_display_id(session, display_id)
    if not anime:
        return await message.answer("Аниме не найдено.")
    anime_id = anime.id
    from database.requests import get_voiceovers
    voiceovers = await get_voiceovers(session, anime_id)
    if not voiceovers:
        return await message.answer("У этого аниме нет озвучек.", reply_markup=get_admin_menu())
        
    text = "Выберите ID озвучки для УДАЛЕНИЯ (вместе со всеми её сериями!):\n\n"
    for vo in voiceovers:
        text += f"<code>{vo.id}</code>. {html.escape(vo.name)}\n"
    await message.answer(text, parse_mode="HTML")
    await state.set_state(AdminDeleteVoiceover.waiting_for_voiceover_id)

@router.message(AdminDeleteVoiceover.waiting_for_voiceover_id)
async def delete_voiceover_id(message: Message, state: FSMContext, session: AsyncSession):
    if not message.text.isdigit():
        return await message.answer("ID должен быть числом.")
    from database.requests import delete_voiceover
    success = await delete_voiceover(session, int(message.text))
    if success:
        await send_admin_log(message.bot, f"Админ <code>{message.from_user.id}</code> удалил озвучку {message.text}")
        await message.answer("✅ Озвучка и все её серии успешно удалены.", reply_markup=get_admin_menu())
    else:
        await message.answer("❌ Озвучка не найдена.", reply_markup=get_admin_menu())
    await state.clear()

# --- Массовая загрузка серий ---
import re

@router.message(F.text == "Масс. загрузка серий")
async def mass_upload_start(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id): return
    
    animes = await get_all_anime(session)
    if not animes:
        return await message.answer("Сначала добавьте хотя бы одно аниме.", reply_markup=get_admin_menu())
        
    text = "Выберите ID аниме для массовой загрузки серий:\n\n"
    for a in animes:
        safe_title = html.escape(str(a.title))
        star = '💎 ' if getattr(a, 'is_4k', False) else ''
        movie = '🎥 ' if getattr(a, 'display_id', '') and str(getattr(a, 'display_id', '')).endswith('_3') else ''
        line = f"<code>{a.display_id}</code>. {star}{movie}{safe_title}\n"
        if len(text) + len(line) > 3800:
            await message.answer(text, parse_mode="HTML")
            text = ""
        text += line
        
    if text:
        await message.answer(text, reply_markup=get_cancel_menu(), parse_mode="HTML")
        
    await state.set_state(AdminMassUpload.waiting_for_anime_id)

@router.message(AdminMassUpload.waiting_for_anime_id)
async def mass_upload_anime_id(message: Message, state: FSMContext, session: AsyncSession):
    if not message.text:
        return await message.answer("Пожалуйста, введите текстовый ID аниме.")
    display_id = message.text.strip()
    anime = await get_anime_by_display_id(session, display_id)
    if not anime:
        return await message.answer("Аниме с таким ID не найдено. Попробуйте еще раз.")
    
    await state.update_data(anime_id=anime.id)
    
    await message.answer("Выберите озвучку из списка ниже:", reply_markup=get_admin_voiceovers_inline_keyboard())
    await message.answer("Или введите название вручную (для пропуска отправьте '-'):", reply_markup=get_cancel_menu())
    await state.set_state(AdminMassUpload.waiting_for_voiceover_name)

@router.message(AdminMassUpload.waiting_for_voiceover_name)
async def mass_upload_voiceover(message: Message, state: FSMContext, session: AsyncSession):
    from database.requests import get_or_create_voiceover
    data = await state.get_data()
    
    if not message.text:
        return await message.answer("Пожалуйста, введите текстовое название озвучки (или '-').")
        
    vo_name = message.text.strip()
    vo_id = None
    
    if vo_name != "-":
        vo = await get_or_create_voiceover(session, data['anime_id'], vo_name)
        vo_id = vo.id
        display_vo = html.escape(vo.name)
    else:
        display_vo = "Без озвучки"
        
    await state.update_data(voiceover_id=vo_id, voiceover_name=vo_name)
    
    anime = await get_anime(session, data['anime_id'])
    
    msg_text = (
        f"✅ Выбрано аниме: <b>{anime.title}</b>\n"
        f"🎙 Озвучка: <b>{display_vo}</b>\n\n"
        "Теперь отправляйте видеофайлы или альбомы видео. "
        "Бот автоматически извлечет номер серии из названия файла "
        "(например: <code>1.mp4</code> или <code>серия 2.mp4</code>).\n\n"
        "Обязательно отправляйте видео <b>с компьютера</b> или <b>как файл (без сжатия)</b>, "
        "чтобы Telegram не переименовал их."
    )
    await message.answer(msg_text, reply_markup=get_finish_upload_menu(), parse_mode="HTML")
    await state.set_state(AdminMassUpload.waiting_for_videos)

@router.message(F.text == "❌ Завершить загрузку", StateFilter(AdminMassUpload.waiting_for_videos))
async def mass_upload_finish(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("✅ Массовая загрузка завершена.", reply_markup=get_admin_menu())

@router.message(StateFilter(AdminMassUpload.waiting_for_videos), F.video | F.document)
async def mass_upload_process_video(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    data = await state.get_data()
    anime_id = data.get('anime_id')
    
    # Получаем имя файла и ID файла
    if message.video:
        file_name = message.video.file_name
        file_id = message.video.file_id
    elif message.document:
        file_name = message.document.file_name
        file_id = message.document.file_id
    else:
        return
        
    if not file_name:
        return await message.answer("❌ У этого файла нет названия, не могу определить серию.")
        
    # Ищем число в названии файла
    numbers = re.findall(r'\d+', file_name)
    if not numbers:
        return await message.answer(f"❌ Не нашел цифру в названии файла: <code>{file_name}</code>", parse_mode="HTML")
        
    # Берем первое число из названия как номер серии
    ep_num = int(numbers[0])
    
    await add_episode(session, anime_id, ep_num, file_id, None, data['voiceover_id'])
    
    try:
        await message.answer(f"✅ Серия <b>{ep_num}</b> ({data['voiceover_name']}) успешно добавлена (файл: {file_name})", parse_mode="HTML", disable_notification=True)
        await send_admin_log(bot, f"Админ {message.from_user.id} массово загрузил серию {ep_num} ({data['voiceover_name']}) для аниме {anime_id} ({file_name})")
    except Exception as e:
        print(f"Не удалось отправить уведомление о загрузке (возможно флуд): {e}")
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
    await message.answer("Выберите качество для этой папки:", reply_markup=get_quality_keyboard())
    await state.set_state(AdminAddFolder.waiting_for_quality)

@router.message(AdminAddFolder.waiting_for_quality)
async def add_folder_quality(message: Message, state: FSMContext):
    if message.text not in ["1080p (Обычное)", "4K (Высокое)"]:
        return await message.answer("Пожалуйста, используйте кнопки.")
    is_4k = message.text == "4K (Высокое)"
    await state.update_data(is_4k=is_4k)
    await message.answer("Отправьте постер (фото) для папки:", reply_markup=get_cancel_menu())
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
    folder = await add_folder(session, data['title'], data['description'], photo_file_id, data.get('is_4k', False))
    await send_admin_log(message.bot, f"Админ <code>{message.from_user.id}</code> создал папку <b>{folder.title}</b> (ID {folder.id}, 4K: {folder.is_4k})")
    await message.answer(f"Папка '{folder.title}' создана! ID: {folder.id}", reply_markup=get_admin_menu())
    await state.clear()

# --- Список папок ---
@router.message(F.text == "Список залитых папок")
async def list_folders(message: Message, session: AsyncSession):
    if not is_admin(message.from_user.id): return
    folders = await get_all_folders(session)
    if not folders:
        return await message.answer("База данных папок пуста.", reply_markup=get_admin_menu())
    
    text = "📂 <b>Список всех залитых папок:</b>\n\n"
    for f in folders:
        diamond = "💎 " if getattr(f, 'is_4k', False) else ""
        text += f"ID <code>{f.id}</code>: {diamond}{html.escape(f.title)}\n"
        
    await message.answer(text, reply_markup=get_admin_menu(), parse_mode="HTML")

# --- Удаление папки ---
@router.message(F.text == "Удалить папку")
async def delete_folder_start(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id): return
    folders = await get_all_folders(session)
    if not folders:
        return await message.answer("База данных папок пуста.", reply_markup=get_admin_menu())
    
    text = "📂 <b>Доступные папки:</b>\n"
    for f in folders:
        diamond = "💎 " if getattr(f, 'is_4k', False) else ""
        text += f"ID <code>{f.id}</code>: {diamond}{html.escape(f.title)}\n"
        
    await message.answer(text + "\nВведите ID папки для удаления:", reply_markup=get_cancel_menu(), parse_mode="HTML")
    await state.set_state(AdminDeleteFolder.waiting_for_folder_id)

@router.message(AdminDeleteFolder.waiting_for_folder_id)
async def delete_folder_process(message: Message, state: FSMContext, session: AsyncSession):
    if not message.text.isdigit():
        return await message.answer("ID должен быть числом.")
    
    folder_id = int(message.text)
    success = await delete_folder(session, folder_id)
    await message.answer("✅ Папка успешно удалена!", reply_markup=get_admin_menu())
    await send_admin_log(message.bot, f"Админ {message.from_user.id} удалил папку {folder_id}")
    await state.clear()

# --- Редактирование папки ---
@router.message(F.text == "Редактировать папку")
async def edit_folder_start(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id): return
    
    folders = await get_all_folders(session)
    text = "Список папок:\n\n"
    for f in folders:
        diamond = "💎 " if getattr(f, 'is_4k', False) else ""
        text += f"ID <code>{f.id}</code>: {diamond}{html.escape(f.title)}\n"
    text += "\nВведите ID папки для редактирования:"
    await message.answer(text, reply_markup=get_cancel_menu(), parse_mode="HTML")
    await state.set_state(AdminEditFolder.waiting_for_folder_id)

@router.message(AdminEditFolder.waiting_for_folder_id)
async def edit_folder_id(message: Message, state: FSMContext, session: AsyncSession):
    if not message.text.isdigit():
        return await message.answer("Отправьте числовой ID.")
    folder_id = int(message.text)
    folder = await get_folder(session, folder_id)
    if not folder:
        return await message.answer("Папка не найдена.")
        
    await state.update_data(folder_id=folder_id)
    await message.answer(f"Текущее название: {folder.title}\nВведите новое название (или '-' чтобы оставить прежним):")
    await state.set_state(AdminEditFolder.waiting_for_new_title)

@router.message(AdminEditFolder.waiting_for_new_title)
async def edit_folder_title(message: Message, state: FSMContext):
    title = None if message.text == "-" else message.text
    await state.update_data(title=title)
    await message.answer("Введите новое описание (или '-' чтобы оставить прежним):")
    await state.set_state(AdminEditFolder.waiting_for_new_description)

@router.message(AdminEditFolder.waiting_for_new_description)
async def edit_folder_description(message: Message, state: FSMContext):
    description = None if message.text == "-" else message.text
    await state.update_data(description=description)
    await message.answer("Отправьте новое фото для обложки (или '-' чтобы оставить прежним):")
    await state.set_state(AdminEditFolder.waiting_for_new_photo)

@router.message(AdminEditFolder.waiting_for_new_photo, F.photo | F.text == "-")
async def edit_folder_photo(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    photo_file_id = None
    if message.photo:
        photo_file_id = message.photo[-1].file_id
        
    data = await state.get_data()
    folder_id = data['folder_id']
    title = data['title']
    description = data['description']
    
    await update_folder(session, folder_id, title, description, photo_file_id)
    await message.answer("✅ Папка успешно обновлена!", reply_markup=get_admin_menu())
    await send_admin_log(bot, f"Админ {message.from_user.id} отредактировал папку {folder_id}")
    await state.clear()

# --- Удаление аниме из папки ---
@router.message(F.text == "Удалить аниме из папки")
async def unlink_anime_start(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id): return
    
    folders = await get_all_folders(session)
    text = "Список папок:\n\n"
    for f in folders:
        diamond = "💎 " if getattr(f, 'is_4k', False) else ""
        text += f"ID <code>{f.id}</code>: {diamond}{html.escape(f.title)}\n"
    text += "\nВведите ID папки, из которой нужно удалить аниме:"
    await message.answer(text, reply_markup=get_cancel_menu(), parse_mode="HTML")
    await state.set_state(AdminUnlinkAnime.waiting_for_folder_id)

@router.message(AdminUnlinkAnime.waiting_for_folder_id)
async def unlink_anime_folder_id(message: Message, state: FSMContext, session: AsyncSession):
    if not message.text.isdigit():
        return await message.answer("Отправьте числовой ID.")
    folder_id = int(message.text)
    folder = await get_folder(session, folder_id)
    if not folder:
        return await message.answer("Папка не найдена.")
        
    animes = await get_anime_in_folder(session, folder_id)
    if not animes:
        await message.answer("Эта папка пуста.", reply_markup=get_admin_menu())
        return await state.clear()
        
    await message.answer(
        f"Аниме в папке <b>{folder.title}</b>:\nНажмите на аниме, чтобы удалить его из папки.",
        reply_markup=get_folder_animes_keyboard(folder_id, animes),
        parse_mode="HTML"
    )
    await state.clear()

@router.callback_query(F.data.startswith("unlink_"))
async def process_unlink_anime(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    if not is_admin(callback.from_user.id): return
    
    # data: unlink_{folder_id}_{anime_id}
    parts = callback.data.split("_")
    folder_id = int(parts[1])
    anime_id = int(parts[2])
    
    success = await unlink_anime_from_folder(session, folder_id, anime_id)
    if success:
        await callback.answer("✅ Аниме удалено из папки!", show_alert=True)
        await send_admin_log(bot, f"Админ {callback.from_user.id} удалил аниме {anime_id} из папки {folder_id}")
        
        # Обновляем клавиатуру
        animes = await get_anime_in_folder(session, folder_id)
        if not animes:
            await callback.message.edit_text("Папка теперь пуста.")
        else:
            await callback.message.edit_reply_markup(reply_markup=get_folder_animes_keyboard(folder_id, animes))
    else:
        await callback.answer("❌ Ошибка или аниме уже удалено.", show_alert=True)

# --- Привязка аниме к папке ---
@router.message(F.text == "Привязать аниме к папке")
async def link_anime_start(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id): return
    folders = await get_all_folders(session)
    if not folders:
        return await message.answer("Сначала создайте хотя бы одну папку.")
    
    text = "Доступные папки:\n" + "\n".join([f"<code>{f.id}</code>. {'💎 ' if getattr(f, 'is_4k', False) else ''}{html.escape(f.title)}" for f in folders])
    await message.answer(text + "\n\nВведите ID папки:", reply_markup=get_cancel_menu(), parse_mode="HTML")
    await state.set_state(AdminLinkAnime.waiting_for_folder_id)

@router.message(AdminLinkAnime.waiting_for_folder_id)
async def link_anime_folder_id(message: Message, state: FSMContext, session: AsyncSession):
    if not message.text.isdigit():
        return await message.answer("ID должен быть числом.")
    await state.update_data(folder_id=int(message.text))
    
    animes = await get_all_anime(session)
    if not animes:
        return await message.answer("Нет доступных аниме для привязки.", reply_markup=get_admin_menu())
        
    text = "Доступные аниме:\n" + "\n".join([f"<code>{a.display_id}</code>. {'💎 ' if getattr(a, 'is_4k', False) else ''}{html.escape(a.title)}" for a in animes])
    
    if len(text) > 4000:
        for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
            await message.answer(chunk, parse_mode="HTML")
        await message.answer("Введите кастомный ID аниме для привязки (можно несколько через пробел):")
    else:
        await message.answer(text + "\n\nВведите кастомный ID аниме для привязки (можно несколько через пробел):", parse_mode="HTML")
        
    await state.set_state(AdminLinkAnime.waiting_for_anime_id)

@router.message(AdminLinkAnime.waiting_for_anime_id)
async def link_anime_process(message: Message, state: FSMContext, session: AsyncSession):
    display_ids = message.text.strip().split()
    data = await state.get_data()
    folder_id = data['folder_id']
    
    success_count = 0
    errors = []
    
    for display_id in display_ids:
        anime = await get_anime_by_display_id(session, display_id)
        if not anime:
            errors.append(f"{display_id}: не найдено")
            continue
        
        success = await link_anime_to_folder(session, folder_id, anime.id)
        if success:
            success_count += 1
        else:
            errors.append(f"{display_id}: уже привязано")
            
    msg = f"✅ Успешно привязано аниме: {success_count}."
    if errors:
        msg += "\n\n⚠️ Ошибки:\n" + "\n".join(errors)
        
    await send_admin_log(message.bot, f"Админ <code>{message.from_user.id}</code> привязал {success_count} аниме к папке ID {folder_id}")
    await message.answer(msg, reply_markup=get_admin_menu())
    await state.clear()

# --- Быстрое редактирование описания серии (/edit) ---
@router.message(Command("edit"))
async def quick_edit_episode(message: Message, state: FSMContext, command: CommandObject, session: AsyncSession):
    from config import ADMIN_IDS, SUPERADMIN_IDS
    if not is_admin(message.from_user.id): return
    data = await state.get_data()
    ep_id = data.get('viewing_episode_id')
    if not ep_id:
        return await message.answer("Сначала откройте какую-нибудь серию в каталоге или поиске, чтобы отредактировать её описание.")
        
    from database.requests import get_episode_by_id
    ep = await get_episode_by_id(session, ep_id)
    if not ep:
        return await message.answer("Ошибка: серия не найдена в базе.")
        
    if command.args:
        new_desc = command.args.strip()
        if new_desc == "-":
            new_desc = None
        elif (new_desc.startswith('"') and new_desc.endswith('"')) or (new_desc.startswith("'") and new_desc.endswith("'")):
            new_desc = new_desc[1:-1]
            
        ep.description = new_desc
        await session.commit()
        await message.answer("Описание серии успешно обновлено! Новое описание будет видно при следующем открытии этой серии.", reply_markup=get_admin_menu())
        return

    desc = ep.description if ep.description else "Нет описания"
    await message.answer(f"Вы редактируете описание серии {ep.episode_number}.\nТекущее описание:\n<i>{desc}</i>\n\nВведите новое описание (или отправьте '-', чтобы очистить):", parse_mode="HTML", reply_markup=get_cancel_menu())
    await state.set_state(AdminQuickEditEpisode.waiting_for_new_description)

@router.message(AdminQuickEditEpisode.waiting_for_new_description)
async def process_quick_edit_episode(message: Message, state: FSMContext, session: AsyncSession):
    new_desc = message.text.strip()
    if new_desc == "-":
        new_desc = None
        
    data = await state.get_data()
    ep_id = data.get('viewing_episode_id')
    
    from database.requests import get_episode_by_id
    ep = await get_episode_by_id(session, ep_id)
    if ep:
        ep.description = new_desc
        await session.commit()
        await message.answer("Описание серии успешно обновлено! Новое описание будет видно при следующем открытии этой серии.", reply_markup=get_admin_menu())
    else:
        await message.answer("Ошибка сохранения.", reply_markup=get_admin_menu())
        
    await state.clear()

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- Вайтлист (Техническое обслуживание) ---
@router.message(Command("whitelist"))
async def whitelist_cmd(message: Message, command: CommandObject):
    if not is_superadmin(message.from_user.id): return
    
    if command.args == "on":
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Подтверждаю (Включить)", callback_data="whitelist_confirm_on")]])
        await message.answer("⚠️ Вы уверены, что хотите включить режим технических работ? Обычные пользователи не смогут пользоваться ботом!", reply_markup=kb)
    elif command.args == "off":
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Подтверждаю (Выключить)", callback_data="whitelist_confirm_off")]])
        await message.answer("Вы уверены, что хотите выключить режим технических работ? Бот станет доступен всем.", reply_markup=kb)
    else:
        await message.answer("Используйте: /whitelist on или /whitelist off")

@router.callback_query(F.data == "whitelist_confirm_on")
async def whitelist_confirm_on(callback: CallbackQuery):
    if not is_superadmin(callback.from_user.id): return
    import json
    with open('whitelist_config.json', 'w', encoding='utf-8') as f:
        json.dump({"enabled": True}, f)
    await callback.message.edit_text("✅ Режим технических работ ВКЛЮЧЕН. Бот доступен только админами.")
    await callback.answer()

@router.callback_query(F.data == "whitelist_confirm_off")
async def whitelist_confirm_off(callback: CallbackQuery):
    if not is_superadmin(callback.from_user.id): return
    import json
    with open('whitelist_config.json', 'w', encoding='utf-8') as f:
        json.dump({"enabled": False}, f)
    await callback.message.edit_text("❌ Режим технических работ ВЫКЛЮЧЕН. Бот доступен всем пользователям.")
    await callback.answer()

# --- Очистка логов ошибок ---
@router.message(Command("clear_logs"))
async def clear_logs_cmd(message: Message, bot: Bot):
    from config import SUPERADMIN_IDS
    if message.from_user.id not in SUPERADMIN_IDS: return
    
    status_msg = await message.answer("⏳ Сканирую последние 150 сообщений чата в поисках логов ошибок...\n(Могут кратковременно мелькать пересланные сообщения, это нормально)")
    
    deleted_count = 0
    start_id = message.message_id
    
    import asyncio
    for msg_id in range(start_id - 1, max(0, start_id - 150), -1):
        try:
            # Пытаемся скопировать сообщение себе же, чтобы прочитать текст (обход ограничений Telegram API)
            fwd = await bot.forward_message(
                chat_id=message.chat.id, 
                from_chat_id=message.chat.id, 
                message_id=msg_id, 
                disable_notification=True
            )
            
            # Проверяем текст
            is_error_log = False
            if fwd.text and "ПРОИЗОШЛА ОШИБКА" in fwd.text:
                is_error_log = True
            elif fwd.caption and "ПРОИЗОШЛА ОШИБКА" in fwd.caption:
                is_error_log = True
                
            # Удаляем форвард-пустышку
            await bot.delete_message(chat_id=message.chat.id, message_id=fwd.message_id)
            
            # Если это лог ошибки - удаляем оригинал
            if is_error_log:
                await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
                deleted_count += 1
                
            # Небольшая пауза, чтобы не словить FloodWait
            await asyncio.sleep(0.06)
            
        except Exception:
            # Сообщение не существует, удалено или мы не можем его переслать
            pass
            
    await status_msg.edit_text(f"✅ Сканирование завершено.\nУспешно удалено логов об ошибках: {deleted_count}")

# --- Копирование описаний серий ---
@router.message(F.text == "Скопировать описания серий")
async def copy_desc_start(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id): return
    from database.requests import get_all_anime
    animes = await get_all_anime(session)
    text = "Доступные аниме:\n" + "\n".join([f"<code>{a.display_id}</code>. {'💎 ' if getattr(a, 'is_4k', False) else ''}{html.escape(a.title)}" for a in animes])
    await message.answer(text + "\n\nВведите кастомный ID аниме <b>ИСТОЧНИКА</b> (откуда копировать):", reply_markup=get_cancel_menu(), parse_mode="HTML")
    await state.set_state(AdminCopyDescriptions.waiting_for_source_anime)

@router.message(AdminCopyDescriptions.waiting_for_source_anime)
async def copy_desc_source_anime(message: Message, state: FSMContext, session: AsyncSession):
    from database.requests import get_anime_by_display_id, get_voiceovers
    display_id = message.text.strip()
    anime = await get_anime_by_display_id(session, display_id)
    if not anime:
        return await message.answer("Аниме не найдено. Проверьте ID.")
        
    await state.update_data(source_anime_id=anime.id)
    
    vos = await get_voiceovers(session, anime.id)
    if not vos:
        text = "У этого аниме нет озвучек."
    else:
        text = "Доступные озвучки ИСТОЧНИКА:\n" + "\n".join([f"<code>{v.id}</code>. {html.escape(v.name)}" for v in vos])
        
    await message.answer(text + "\n\nОтправьте ID озвучки ИСТОЧНИКА (или отправьте тире '-', если описания у серий без озвучки):", parse_mode="HTML")
    await state.set_state(AdminCopyDescriptions.waiting_for_source_voiceover)

@router.message(AdminCopyDescriptions.waiting_for_source_voiceover)
async def copy_desc_source_vo(message: Message, state: FSMContext, session: AsyncSession):
    vo_input = message.text.strip()
    if vo_input == "-":
        await state.update_data(source_voiceover_id=None)
    else:
        if not vo_input.isdigit():
            return await message.answer("Пожалуйста, введите числовой ID озвучки или '-'.")
        from database.requests import get_voiceover
        vo = await get_voiceover(session, int(vo_input))
        if not vo:
            return await message.answer("Озвучка не найдена. Попробуйте еще раз.")
        await state.update_data(source_voiceover_id=vo.id)
        
    from database.requests import get_all_anime
    animes = await get_all_anime(session)
    text = "Доступные аниме:\n" + "\n".join([f"<code>{a.display_id}</code>. {'💎 ' if getattr(a, 'is_4k', False) else ''}{html.escape(a.title)}" for a in animes])
    await message.answer(text + "\n\nВведите кастомный ID аниме <b>НАЗНАЧЕНИЯ</b> (куда копировать):", parse_mode="HTML")
    await state.set_state(AdminCopyDescriptions.waiting_for_dest_anime)

@router.message(AdminCopyDescriptions.waiting_for_dest_anime)
async def copy_desc_dest_anime(message: Message, state: FSMContext, session: AsyncSession):
    from database.requests import get_anime_by_display_id, get_voiceovers
    display_id = message.text.strip()
    anime = await get_anime_by_display_id(session, display_id)
    if not anime:
        return await message.answer("Аниме не найдено. Проверьте ID.")
        
    await state.update_data(dest_anime_id=anime.id)
    
    vos = await get_voiceovers(session, anime.id)
    if not vos:
        text = "У этого аниме нет озвучек."
    else:
        text = "Доступные озвучки НАЗНАЧЕНИЯ:\n" + "\n".join([f"<code>{v.id}</code>. {html.escape(v.name)}" for v in vos])
        
    await message.answer(text + "\n\nОтправьте ID озвучки НАЗНАЧЕНИЯ (или отправьте тире '-', если копировать в серии без озвучки):", parse_mode="HTML")
    await state.set_state(AdminCopyDescriptions.waiting_for_dest_voiceover)

@router.message(AdminCopyDescriptions.waiting_for_dest_voiceover)
async def copy_desc_execute(message: Message, state: FSMContext, session: AsyncSession):
    vo_input = message.text.strip()
    if vo_input == "-":
        dest_voiceover_id = None
    else:
        if not vo_input.isdigit():
            return await message.answer("Пожалуйста, введите числовой ID озвучки или '-'.")
        from database.requests import get_voiceover
        vo = await get_voiceover(session, int(vo_input))
        if not vo:
            return await message.answer("Озвучка не найдена. Попробуйте еще раз.")
        dest_voiceover_id = vo.id
        
    data = await state.get_data()
    source_anime_id = data['source_anime_id']
    source_voiceover_id = data.get('source_voiceover_id')
    dest_anime_id = data['dest_anime_id']
    
    from database.models import Episode
    from sqlalchemy import select
    
    # 1. Получаем все серии источника
    if source_voiceover_id is None:
        source_query = select(Episode).where(Episode.anime_id == source_anime_id, Episode.voiceover_id.is_(None))
    else:
        source_query = select(Episode).where(Episode.anime_id == source_anime_id, Episode.voiceover_id == source_voiceover_id)
        
    source_result = await session.execute(source_query)
    source_episodes = source_result.scalars().all()
    
    desc_map = {}
    for ep in source_episodes:
        if ep.description:
            desc_map[ep.episode_number] = ep.description
            
    if not desc_map:
        await state.clear()
        return await message.answer("❌ У источника нет серий с описаниями для копирования.", reply_markup=get_admin_menu())
        
    # 2. Получаем все серии назначения
    if dest_voiceover_id is None:
        dest_query = select(Episode).where(Episode.anime_id == dest_anime_id, Episode.voiceover_id.is_(None))
    else:
        dest_query = select(Episode).where(Episode.anime_id == dest_anime_id, Episode.voiceover_id == dest_voiceover_id)
        
    dest_result = await session.execute(dest_query)
    dest_episodes = dest_result.scalars().all()
    
    updated_count = 0
    for ep in dest_episodes:
        if ep.episode_number in desc_map:
            ep.description = desc_map[ep.episode_number]
            updated_count += 1
            
    await session.commit()
    
    await send_admin_log(message.bot, f"Админ <code>{message.from_user.id}</code> скопировал {updated_count} описаний.")
    await message.answer(f"✅ Успешно скопировано описаний: {updated_count}.", reply_markup=get_admin_menu())
    await state.clear()

# --- УПРАВЛЕНИЕ ОПЛАТОЙ И ПРОМОКОДАМИ ---
from keyboards.reply import get_admin_payments_menu
from states.fsm import AdminSettings, AdminCreatePromo, AdminDeletePromo

@router.message(F.text == "💳 Управление Оплатой")
async def admin_payments_menu(message: Message):
    if not is_admin(message.from_user.id): return
    await message.answer("Управление подпиской и промокодами:", reply_markup=get_admin_payments_menu())

@router.message(F.text == "Настройки подписки")
async def admin_settings_start(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id): return
    from database.requests import get_settings
    settings = await get_settings(session)
    await message.answer(
        f"Текущая цена подписки: <b>{settings.premium_price} ₽</b>\n"
        f"Длительность подписки: <b>{settings.premium_duration_days} дней</b>\n\n"
        "Введите новую ЦЕНУ подписки в рублях (или отправьте '-', чтобы не менять):",
        parse_mode="HTML"
    )
    await state.set_state(AdminSettings.waiting_for_price)

@router.message(AdminSettings.waiting_for_price)
async def admin_settings_price(message: Message, state: FSMContext):
    if message.text != '-':
        if not message.text.isdigit():
            return await message.answer("Пожалуйста, введите число (или '-').")
        await state.update_data(price=int(message.text))
    await message.answer("Теперь введите новую ДЛИТЕЛЬНОСТЬ подписки в днях (или отправьте '-', чтобы не менять):")
    await state.set_state(AdminSettings.waiting_for_duration)

@router.message(AdminSettings.waiting_for_duration)
async def admin_settings_duration(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    price = data.get('price')
    duration = None
    if message.text != '-':
        if not message.text.isdigit():
            return await message.answer("Пожалуйста, введите число (или '-').")
        duration = int(message.text)
        
    from database.requests import update_settings
    await update_settings(session, price=price, duration=duration)
    await message.answer("✅ Настройки подписки успешно обновлены!", reply_markup=get_admin_payments_menu())
    await state.clear()

@router.message(F.text == "Создать промокод")
async def admin_create_promo_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await message.answer("Введите текст нового промокода (только английские буквы и цифры):")
    await state.set_state(AdminCreatePromo.waiting_for_code)

@router.message(AdminCreatePromo.waiting_for_code)
async def admin_create_promo_code(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    import re
    if not re.match(r'^[A-Z0-9]+$', code):
        return await message.answer("Недопустимый формат. Используйте только английские буквы и цифры.")
    await state.update_data(code=code)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Скидка (в рублях)"), KeyboardButton(text="Бесплатные дни")]
        ], resize_keyboard=True
    )
    await message.answer("Выберите тип промокода:", reply_markup=keyboard)
    await state.set_state(AdminCreatePromo.waiting_for_type)

@router.message(AdminCreatePromo.waiting_for_type)
async def admin_create_promo_type(message: Message, state: FSMContext):
    if message.text == "Скидка (в рублях)":
        p_type = 'discount'
        await message.answer("Введите размер скидки в рублях:", reply_markup=get_admin_payments_menu())
    elif message.text == "Бесплатные дни":
        p_type = 'free_days'
        await message.answer("Введите количество бесплатных дней:", reply_markup=get_admin_payments_menu())
    else:
        return await message.answer("Выберите тип с помощью кнопок.")
    
    await state.update_data(type=p_type)
    await state.set_state(AdminCreatePromo.waiting_for_value)

@router.message(AdminCreatePromo.waiting_for_value)
async def admin_create_promo_value(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Введите целое число.")
    await state.update_data(value=int(message.text))
    await message.answer("Введите максимальное количество использований промокода:")
    await state.set_state(AdminCreatePromo.waiting_for_uses)

@router.message(AdminCreatePromo.waiting_for_uses)
async def admin_create_promo_uses(message: Message, state: FSMContext, session: AsyncSession):
    if not message.text.isdigit():
        return await message.answer("Введите целое число.")
    uses = int(message.text)
    data = await state.get_data()
    
    from database.requests import create_promo_code
    try:
        await create_promo_code(
            session, 
            code=data['code'], 
            discount_type=data['type'], 
            discount_value=data['value'], 
            max_uses=uses
        )
        t_str = "скидка" if data['type'] == 'discount' else "дней"
        await message.answer(f"✅ Промокод <code>{data['code']}</code> на {data['value']} {t_str} создан! Лимит: {uses}.", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Ошибка (возможно промокод уже существует): {e}")
    await state.clear()

@router.message(F.text == "Список промокодов")
async def admin_list_promos(message: Message, session: AsyncSession):
    if not is_admin(message.from_user.id): return
    from database.requests import get_all_promo_codes
    promos = await get_all_promo_codes(session)
    if not promos:
        return await message.answer("Нет созданных промокодов.")
    
    lines = []
    for p in promos:
        t_str = f"Скидка {p.discount_value} ₽" if p.discount_type == 'discount' else f"{p.discount_value} дн. бесплатно"
        lines.append(f"🎟 <code>{p.code}</code>: {t_str} ({p.uses_count}/{p.max_uses})")
    
    await message.answer("Список промокодов:\n" + "\n".join(lines), parse_mode="HTML")

@router.message(F.text == "Удалить промокод")
async def admin_delete_promo_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await message.answer("Введите текст промокода для удаления:")
    await state.set_state(AdminDeletePromo.waiting_for_code)

@router.message(AdminDeletePromo.waiting_for_code)
async def admin_delete_promo_code(message: Message, state: FSMContext, session: AsyncSession):
    from database.requests import delete_promo_code
    code = message.text.strip()
    success = await delete_promo_code(session, code)
    if success:
        await message.answer(f"✅ Промокод {code} удален.")
    else:
        await message.answer(f"❌ Промокод не найден.")
    await state.clear()
