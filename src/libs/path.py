from __future__ import annotations

import os.path
import pathlib
import time

import dotenv


def ensure_dir(path: pathlib) -> pathlib:
    if not os.path.exists(path):
        os.mkdir(path)
    return path


LIBS_DIR = pathlib.Path(__file__).parent
SRC_DIR = LIBS_DIR.parent
PROJECT_DIR = SRC_DIR.parent
DATA_DIR = ensure_dir(PROJECT_DIR / 'data')  # ensure_dir(PROJECT_DIR / 'data')
MAIL_DATA_DIR = ensure_dir(DATA_DIR / 'mail')
GENERATED_DIR = ensure_dir(DATA_DIR / '__generated__')  # ensure_dir(PROJECT_DIR / "__generated__")
OPENAI_DATA_DIR = ensure_dir(DATA_DIR / 'openai')  # ensure_dir(DATA_DIR / 'openai')
CHATGPT_DATA_DIR = ensure_dir(OPENAI_DATA_DIR / 'chatgpt')
FILES_DATA_DIR = ensure_dir(DATA_DIR / "files")
CHATGPT_DIR = ensure_dir(OPENAI_DATA_DIR / 'chatgpt')
LOGS_DIR = ensure_dir(PROJECT_DIR / 'logs')

# ----------------------------
# env
# ----------------------------
ENV_LOCAL_PATH = PROJECT_DIR / '.env.local'
ENV_SERVER_PATH = PROJECT_DIR / ".env.server"
ENV_DEV_PATH = PROJECT_DIR / '.env.development'
ENV_PROD_PATH = PROJECT_DIR / '.env.production'
MODELS_DATA_PATH = GENERATED_DIR / f'openapi_models_{time.time_ns()}.json'
SETTINGS_PATH = pathlib.Path(__file__)

ENV_JSON_PATH = PROJECT_DIR / ".env.json"
envs_to_load = [
    PROJECT_DIR / ".env",
    PROJECT_DIR / '.env.local',
]
for env in envs_to_load:
    if env.exists():
        print(f'loading env at file://{env}')
        dotenv.load_dotenv(env)

EMAIL_ACTIVATION_HTML_PATH = MAIL_DATA_DIR / 'activation.html'