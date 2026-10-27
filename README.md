# Yandex Quasar Voice — Home Assistant App

Самодостаточное дополнение Home Assistant OS для голосового поиска музыки на
рутованной Yandex Station. Устанавливается как обычное приложение из магазина —
отдельный Linux-сервер, Python и ручной systemd не нужны.

```text
Yandex Station ──ADB──▶ это приложение в HAOS
                              │ локальные HA Actions
                              ▼
                Music Assistant → YouTube Music → Glagol
```

Пользователь указывает четыре значения в форме приложения: адрес станции,
сущность плеера Music Assistant, ID интеграции MA и ID источника YouTube Music.
Токен Home Assistant вводить не нужно: приложение использует защищённый внутренний
канал Supervisor.

## Безопасность

- микрофон, аудиопотоки, память процессов и прошивка не перехватываются;
- контейнер читает только новые строки `maind.log` и после переподключения начинает с EOF;
- доступ к Home Assistant идёт только через локальный Supervisor API;
- команды умного дома отбрасываются;
- поиск ограничивается настроенным музыкальным провайдером.

## Статус 0.1

Реализован первый контейнерный срез: ADB с автоматическим восстановлением, безопасный
парсер голосовых команд, поиск только в выбранном YouTube Music provider и запуск на
выбранном MA-плеере через Home Assistant.

## Разработка

```sh
python3 -m unittest discover -s tests -v
docker build --build-arg BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest yandex_quasar_voice
```

Поддерживаемая фраза первой версии: «Алиса, включи *исполнитель или песня*».

## Совместимость

Требуется Home Assistant OS/Supervised, интеграция Music Assistant, настроенные
YouTube Music и Yandex Station providers, а также root ADB на станции.

## Лицензия

MIT. Проект не связан с Яндексом и не одобрен им.
