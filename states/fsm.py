from aiogram.fsm.state import State, StatesGroup

class SearchStates(StatesGroup):
    waiting_for_query = State()

class AdminAddAnime(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_quality = State()
    waiting_for_photo = State()

class AdminEditAnime(StatesGroup):
    waiting_for_anime_id = State()
    waiting_for_new_title = State()
    waiting_for_new_description = State()

class AdminAddEpisode(StatesGroup):
    waiting_for_anime_id = State()
    waiting_for_episode_number = State()
    waiting_for_episode_description = State()
    waiting_for_video = State()

class AdminEditEpisode(StatesGroup):
    waiting_for_anime_id = State()
    waiting_for_episode_number = State()
    waiting_for_field = State()
    waiting_for_new_video = State()
    waiting_for_new_description = State()

class AdminDeleteAnime(StatesGroup):
    waiting_for_anime_id = State()
    waiting_for_confirmation = State()

class AdminDeleteEpisode(StatesGroup):
    waiting_for_episode_id = State()

class AdminListEpisodes(StatesGroup):
    waiting_for_anime_id = State()

class AdminAddFolder(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_photo = State()

class AdminLinkAnime(StatesGroup):
    waiting_for_folder_id = State()
    waiting_for_anime_id = State()

class AdminDeleteFolder(StatesGroup):
    waiting_for_folder_id = State()

class AdminEditFolder(StatesGroup):
    waiting_for_folder_id = State()
    waiting_for_new_title = State()
    waiting_for_new_description = State()
    waiting_for_new_photo = State()

class AdminUnlinkAnime(StatesGroup):
    waiting_for_folder_id = State()
    waiting_for_anime_to_unlink = State()

class AdminMassUpload(StatesGroup):
    waiting_for_anime_id = State()
    waiting_for_videos = State()
