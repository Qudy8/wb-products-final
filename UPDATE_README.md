# Инструкция по обновлению бота на сервере

## Способ 1: Обновление через SCP (рекомендуется)

### Шаг 1: На локальном компьютере
Скопируйте измененные файлы на сервер:

```bash
# Скопировать конкретный файл
scp C:\Users\user\wbproducts\main.py root@195.133.73.232:/opt/wbproducts/

# Или скопировать несколько файлов
scp C:\Users\user\wbproducts\{main.py,database.py,wb_api.py} root@195.133.73.232:/opt/wbproducts/

# Или весь проект (осторожно, перезапишет всё)
scp -r C:\Users\user\wbproducts/* root@195.133.73.232:/opt/wbproducts/
```

### Шаг 2: На сервере
Подключитесь к серверу и перезапустите бота:

```bash
ssh root@195.133.73.232
cd /opt/wbproducts
chmod +x update.sh
./update.sh
```

## Способ 2: Через Git (если используете репозиторий)

### Настройка один раз:
1. Создайте Git репозиторий для проекта
2. На сервере клонируйте репозиторий

### Для обновления:
На локальном компьютере:
```bash
git add .
git commit -m "Описание изменений"
git push
```

На сервере:
```bash
ssh root@195.133.73.232
cd /opt/wbproducts
git pull
./update.sh
```

## Способ 3: Быстрое обновление одного файла

Если изменили только один файл (например, main.py):

```bash
# С локального компьютера
scp C:\Users\user\wbproducts\main.py root@195.133.73.232:/opt/wbproducts/

# Затем на сервере
ssh root@195.133.73.232
systemctl restart wbbot
journalctl -u wbbot -f
```

## Полезные команды на сервере

```bash
# Проверить статус бота
systemctl status wbbot

# Перезапустить бота
systemctl restart wbbot

# Остановить бота
systemctl stop wbbot

# Запустить бота
systemctl start wbbot

# Смотреть логи в реальном времени
journalctl -u wbbot -f

# Смотреть последние 100 строк логов
journalctl -u wbbot -n 100

# Проверить, какие файлы изменились
ls -lth /opt/wbproducts/
```

## Проверка работы после обновления

1. Проверьте статус: `systemctl status wbbot`
2. Проверьте логи: `journalctl -u wbbot -f`
3. Протестируйте бота в Telegram

## Если что-то пошло не так

```bash
# Откатить изменения (если используете git)
cd /opt/wbproducts
git checkout main.py  # или другой файл

# Посмотреть подробные логи ошибок
journalctl -u wbbot -n 50 --no-pager

# Перезапустить бота
systemctl restart wbbot
```
