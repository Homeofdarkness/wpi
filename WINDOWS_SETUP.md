# Установка и запуск WPI на Windows

Эта инструкция рассчитана на Windows 10/11, PowerShell, Git Bash и Visual
Studio Code. Для проекта нужен Python 3.11 или новее; рекомендуемая версия —
Python 3.12.

Если рядом с командой не указано иное, она выполняется в PowerShell. Команды
обновления выполняются в Git Bash, который устанавливается вместе с Git for
Windows. После установки программ закройте и заново откройте оба терминала,
чтобы они получили обновлённую переменную `PATH`.

## 1. Установка Git

Самый простой вариант — через WinGet:

```powershell
winget install --id Git.Git -e --source winget
```

Если WinGet недоступен, скачайте установщик с официальной страницы
[Git for Windows](https://git-scm.com/install/windows). При установке можно
оставить предложенные параметры.

Проверка:

```powershell
git --version
```

Один раз укажите данные, которые Git будет записывать в ваши коммиты:

```powershell
git config --global user.name "Ваше имя"
git config --global user.email "you@example.com"
```

## 2. Установка Visual Studio Code

Через WinGet:

```powershell
winget install --id Microsoft.VisualStudioCode -e
```

Альтернативный вариант — `User Installer` с официальной страницы
[VS Code for Windows](https://code.visualstudio.com/docs/setup/windows).
Пользовательский установщик подходит в большинстве случаев и не требует
прав администратора.

Проверка после перезапуска PowerShell:

```powershell
code --version
```

## 3. Установка uv

`uv` создаёт виртуальное окружение, устанавливает нужную версию Python и
синхронизирует зависимости проекта из `uv.lock`.

Установка через WinGet:

```powershell
winget install --id astral-sh.uv -e
```

Если WinGet недоступен, используйте официальный установщик uv:

```powershell
powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Проверка:

```powershell
uv --version
```

Подробности: [официальная инструкция по установке uv](https://docs.astral.sh/uv/getting-started/installation/).

## 4. Установка Python

### Рекомендуемый вариант для этого проекта

Пусть `uv` установит отдельный Python 3.12:

```powershell
uv python install 3.12
uv python list
```

Системный Python при таком варианте не обязателен: все команды проекта
запускаются через `uv run`.

### Если нужен системный Python

Установите Python Install Manager с
[официальной страницы Python](https://www.python.org/downloads/), затем:

```powershell
py install 3.12
py -V:3.12 --version
```

Не устанавливайте библиотеки проекта глобально через `pip`: ими управляет
`uv` внутри `.venv`.

## 5. Что такое PATH и как его проверить

`PATH` — список каталогов, в которых Windows ищет программы при вводе команд
`git`, `uv`, `code` или `python`. Установленная программа может существовать на
диске, но терминал напишет «команда не найдена», если каталог с её `.exe` не
попал в `PATH`.

WinGet и обычные установщики добавляют нужные каталоги автоматически. Уже
открытый терминал не увидит это изменение, поэтому после установки сначала
полностью закройте PowerShell, Git Bash и VS Code, а затем откройте их заново.

Проверка в PowerShell:

```powershell
where.exe git
where.exe uv
where.exe code
git --version
uv --version
code --version
```

Проверка в Git Bash:

```bash
command -v git
command -v uv
command -v code
git --version
uv --version
code --version
```

Git Bash при запуске импортирует Windows `PATH`, поэтому обычно дополнительная
настройка для него не нужна.

Типичные каталоги программ:

| Программа | Типичный каталог в Windows `PATH` |
| --- | --- |
| Git | `C:\Program Files\Git\cmd` |
| VS Code User Installer | `%LOCALAPPDATA%\Programs\Microsoft VS Code\bin` |
| uv из официального скрипта | `%USERPROFILE%\.local\bin` |
| Python Install Manager | `%LOCALAPPDATA%\Python\bin` |

Если `uv` работает в PowerShell, но не находится в Git Bash, сначала
перезапустите Git Bash. Для установки uv официальным скриптом можно проверить
каталог так:

```bash
ls "$HOME/.local/bin/uv.exe"
export PATH="$HOME/.local/bin:$PATH"
uv --version
```

Последняя команда `export` изменяет `PATH` только в текущем окне. Если она
решила проблему, добавьте строку `export PATH="$HOME/.local/bin:$PATH"` в
`~/.bashrc`, затем перезапустите Git Bash.

Добавить каталог в Windows `PATH` вручную можно через меню «Изменение
переменных среды для учётной записи» → `Path` → «Изменить» → «Создать».
Добавляйте каталог, а не путь до конкретного `.exe`, и не удаляйте существующие
записи.

Не добавляйте `.venv\Scripts` этого проекта в глобальный Windows `PATH`:
окружение относится только к WPI. Используйте `uv run`, а в VS Code выбирайте
интерпретатор `.venv\Scripts\python.exe`.

## 6. Получение проекта

Если проекта ещё нет на компьютере:

```powershell
git clone https://github.com/Homeofdarkness/wpi.git "$HOME\Documents\wpi"
cd "$HOME\Documents\wpi"
```

Ссылка уже указана полностью — ничего подставлять или заменять вручную не
нужно. Страница проекта:
[Homeofdarkness/wpi](https://github.com/Homeofdarkness/wpi).

Если проект уже находится в `C:\Users\venom\PycharmProjects\wpi`, клонировать
его повторно не нужно:

```powershell
cd "C:\Users\venom\PycharmProjects\wpi"
```

Все последующие команды нужно выполнять из каталога, где находятся
`pyproject.toml`, `uv.lock` и `main.py`.

## 7. Создание окружения и установка зависимостей

```powershell
uv sync --frozen --python 3.12 --group dev
```

Команда создаст `.venv` и установит версии зависимостей из `uv.lock`, включая
инструменты разработки `pytest` и `ruff`. Активировать `.venv` вручную для
команд `uv run` не нужно.

Проверка интерпретатора:

```powershell
uv run python --version
```

## 8. Настройка VS Code

Откройте проект:

```powershell
code .
```

Установите расширения:

```powershell
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension charliermarsh.ruff
```

Затем в VS Code:

1. Нажмите `Ctrl+Shift+P`.
2. Выберите `Python: Select Interpreter`.
3. Выберите `.venv\Scripts\python.exe` из текущего проекта.

## 9. Запуск приложения

Основной интерактивный запуск:

```powershell
uv run python main.py
```

Программа предложит выбрать игровой режим и способ ввода:

- `country_creator` — создание страны;
- `moves_skipper` — пропуск хода по вставленным блокам статистики.

Остановить программу можно сочетанием `Ctrl+C`.

## 10. Создание базовой страны из файла

Запуск с файлами по умолчанию:

```powershell
uv run python create_basic_country.py
```

При этом читается `test_files\edem_country_input.txt`, основная стата
сохраняется в `test_files\edem_country_output.txt`, а редактируемые настройки
промышленности — в
`test_files\edem_country_output_industry_settings.toml`.
Создание само по себе не пропускает ход: настроенные эффекты появятся в
основном выходе со статусом `ожидает расчёта хода`.

Создание страны с расчётом одного хода и применением всех эффектов:

```powershell
uv run python create_basic_country.py --turns 1 --seed 1
```

Для нескольких ходов измените `--turns`; `--seed` можно опустить. При файловом
запуске кредит автоматически не оформляется, поэтому программа не ждёт ручной
ввод.

Свои пути можно передать явно:

```powershell
uv run python create_basic_country.py `
  "test_files\my_country_input.txt" `
  --output "test_files\my_country_output.txt" `
  --industry-settings-output "test_files\my_industry_settings.toml"
```

Символ обратного апострофа в конце строки — перенос команды PowerShell.
Однострочный эквивалент:

```powershell
uv run python create_basic_country.py "test_files\my_country_input.txt" --output "test_files\my_country_output.txt" --industry-settings-output "test_files\my_industry_settings.toml"
```

## 11. Проверки перед работой или коммитом

Запустить все тесты:

```powershell
uv run pytest -q
```

Проверить код с Ruff:

```powershell
uv run ruff check .
uv run ruff format --check .
```

Автоматически исправить безопасно исправляемые замечания и отформатировать
код:

```powershell
uv run ruff check . --fix
uv run ruff format .
```

После автоисправлений снова запустите тесты.

## 12. Обновление проекта через Git Bash

Рядом с этой инструкцией находится `update_project.sh`. Он:

1. проверяет наличие Git, uv, `pyproject.toml` и `uv.lock`;
2. отказывается продолжать при локальных незакоммиченных изменениях;
3. получает изменения Git и выполняет только fast-forward обновление;
4. синхронизирует окружение строго по `uv.lock`;
5. запускает Ruff и тесты.

Git сам по себе не исполняет `.sh`, но Git for Windows устанавливает Git Bash.
Откройте каталог проекта в Проводнике, нажмите правой кнопкой мыши по пустому
месту и выберите `Open Git Bash here`, затем выполните:

```bash
bash ./update_project.sh
```

Если нужно только скачать код и зависимости, временно пропустив проверки:

```bash
bash ./update_project.sh --skip-checks
```

`--skip-checks` стоит использовать только для диагностики: обычное обновление
должно завершаться тестами.

### Короткая команда `git update`

Git позволяет зарегистрировать локальный алиас для этого репозитория. Один раз
выполните в Git Bash из каталога WPI:

```bash
git config --local alias.update '!bash ./update_project.sh'
```

После этого полное обновление запускается командой:

```bash
git update
```

А обновление без проверок:

```bash
git update --skip-checks
```

Алиас хранится в `.git/config` конкретной копии проекта и не влияет на другие
репозитории. После нового `git clone` его потребуется зарегистрировать снова.

Из PowerShell скрипт тоже можно запустить через Bash, установленный вместе с
Git for Windows:

```powershell
& "C:\Program Files\Git\bin\bash.exe" ./update_project.sh
```

Скрипт намеренно не выполняет `git reset`, не удаляет файлы и не прячет
изменения автоматически. Если он сообщает о локальных изменениях, сначала
посмотрите их:

```bash
git status
git diff
```

Если изменения нужно сохранить в репозитории:

```bash
git add .
git commit -m "Сохранить локальные изменения"
```

После этого повторите `git update` или `bash ./update_project.sh`.

## 13. Ручное обновление без скрипта

Полный ручной вариант, включая отдельную проверку форматирования:

```bash
git status
git fetch --all --prune
git merge --ff-only '@{u}'
uv sync --frozen --group dev
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
```

Скрипт обновляет проект до версий, уже зафиксированных в `uv.lock`. Он не
выполняет `uv lock --upgrade`, потому что обновление всех библиотек меняет
результаты расчётов и должно делаться отдельной задачей с тестированием.

## 14. Частые проблемы

### Команда не найдена

Если `git`, `uv` или `code` не распознаётся, выполните проверки из раздела про
`PATH`. Сначала перезапустите терминалы; вручную меняйте `PATH`, только если
программа действительно установлена, но её каталог отсутствует в списке.

### Git Bash не запускает `update_project.sh`

Вызывать файл через `bash` можно независимо от executable-флага:

```bash
bash ./update_project.sh
```

Если скрипт отсутствует, проверьте ветку и состояние проекта:

```bash
git status
git branch --show-current
ls -la update_project.sh
```

### VS Code выбрал не тот Python

Повторите `Python: Select Interpreter` и выберите:

```text
<папка проекта>\.venv\Scripts\python.exe
```

### Повреждено или устарело окружение

Обычно достаточно повторной синхронизации:

```powershell
uv sync --frozen --python 3.12 --group dev
```

### Fast-forward обновление завершилось ошибкой

Сначала выполните:

```bash
git status
git branch -vv
```

Fast-forward невозможен, если локальная и удалённая ветки разошлись. В этом
случае не применяйте `reset --hard`: сначала сохраните свою работу и решите,
нужен merge или rebase.

### Где посмотреть правила ввода и формулы

- `README.md` — краткий обзор и основные команды;
- `WIKI.md` — статы, порядок хода и формулы;
- `INDUSTRY.md` — настройка промышленности;
- `test_files\moves_skipper_example` — примеры входных блоков.
