# Настройка Git для автоматического деплоя

## Шаг 1: Создание GitHub репозитория

1. Перейдите на https://github.com
2. Нажмите "New repository"
3. Название: `wbproducts`
4. Тип: Private (рекомендуется)
5. НЕ добавляйте README, .gitignore уже есть
6. Создайте репозиторий

## Шаг 2: Инициализация Git локально (на Windows)

Откройте терминал в папке проекта и выполните:

```bash
cd C:\Users\user\wbproducts

# Инициализация Git (если еще не сделано)
git init

# Добавление всех файлов
git add .

# Первый коммит
git commit -m "Initial commit"

# Добавление удаленного репозитория (замените YOUR_USERNAME на ваш username)
git remote add origin https://github.com/YOUR_USERNAME/wbproducts.git

# Отправка на GitHub
git branch -M main
git push -u origin main
```

## Шаг 3: Настройка Git на сервере

Подключитесь к серверу:

```bash
ssh root@195.133.73.232
```

На сервере выполните:

```bash
# Переход в директорию проекта
cd /opt/wbproducts

# Инициализация Git
git init

# Добавление удаленного репозитория (замените YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/wbproducts.git

# Получение первой версии
git fetch origin
git checkout -b main origin/main

# Или если ветка называется master:
# git checkout -b master origin/master

# Сделать скрипт исполняемым
chmod +x git-deploy.sh
```

## Шаг 4: Настройка SSH ключа для GitHub (опционально, но рекомендуется)

На сервере:

```bash
# Генерация SSH ключа
ssh-keygen -t ed25519 -C "your_email@example.com"

# Просмотр публичного ключа
cat ~/.ssh/id_ed25519.pub
```

Скопируйте вывод и добавьте его в GitHub:
1. GitHub → Settings → SSH and GPG keys → New SSH key
2. Вставьте ключ и сохраните

Измените URL репозитория на SSH:
```bash
cd /opt/wbproducts
git remote set-url origin git@github.com:YOUR_USERNAME/wbproducts.git
```

## Процесс обновления (после настройки)

### На локальном компьютере (Windows):

1. Внесите изменения в код
2. Закоммитьте и отправьте на GitHub:

```bash
cd C:\Users\user\wbproducts

git add .
git commit -m "Описание изменений"
git push origin main
```

### На сервере:

```bash
ssh root@195.133.73.232
cd /opt/wbproducts
./git-deploy.sh
```

Готово! Бот автоматически обновится и перезапустится.

## Альтернатива: Webhook для автоматического деплоя

Можно настроить автоматический деплой при каждом push в GitHub:

1. На сервере установите webhook listener:
```bash
pip install flask
```

2. Создайте скрипт `webhook.py` для автоматического деплоя
3. Настройте GitHub webhook на URL вашего сервера

## Быстрая команда обновления

Создайте alias на локальном компьютере для быстрого деплоя:

В PowerShell добавьте в профиль:
```powershell
function Deploy-WBBot {
    cd C:\Users\user\wbproducts
    git add .
    git commit -m $args[0]
    git push origin main
    ssh root@195.133.73.232 "cd /opt/wbproducts && ./git-deploy.sh"
}
```

Использование:
```powershell
Deploy-WBBot "Исправлен баг с ценами"
```

## Решение проблем

### Конфликты при git pull
```bash
cd /opt/wbproducts
git stash
git pull origin main
git stash pop
```

### Сброс всех изменений на сервере
```bash
cd /opt/wbproducts
git reset --hard origin/main
./git-deploy.sh
```

### Проверка статуса
```bash
cd /opt/wbproducts
git status
git log --oneline -5
```
