# Securities Monitor

#### EQ
* основная сессия: 10:00 - 18:40
* вечерня сессия: 19:05 - 23:50

#### FX
* основная сессия: 10:00 - 19:00

#### FO
* утреняя сессия: 9:00 - 14:00
* дневная сессия: 14:05 - 18:50
* вечерняя сессия: 19:05 - 23:50

#### HI2
* 18:45 - дневная сессия

## Настройка
```.env
# TELEGRAM CONFIG
TELEGRAM_BOT_TOKEN=<telegram bot token>
TELEGRAM_GROUP_CHATID=<telegram group chatid>

# PASSPORT MOEX
MOEX_PASSPORT_LOGIN=<passport.moex email>
MOEX_PASSPORT_PASSWORD=<passport.moex password>

# MONITOR CONFIG
DELAY=<delay in seconds. 600 = 10min>
INTERVAL_REQUEST=<waiting in min. 5 = 5min>
```

## Запуск
1. Ручной запуск
```.sh
python -m venv venv
```
```.sh
source venv/bin/activate
```
```.sh
pip install -r requirements.txt
```
```.sh
export PYTHONPATH=$(pwd)
```
```.sh
-terminal 1
python /src/bot/bot.py

-terminal 2
python /src/scheduler.py
```

2. Docker
```.sh
docker build -t algopack_monitor .
```

```.sh
docker run -it algopack_monitor
```

## Структура проекта
```
.
├── Dockerfile
├── Makefile
├── README.md
├── entrypoint.sh
├── requirements.txt
├── setup.cfg
├── src
│   ├── bot - Пакет с исходниками телеграм бота
│   │   ├── bot.py - точка входа бота
│   │   ├── config.py конфиги тг бота
│   │   └── handlers - обработчики стейтов
│   │       ├── __init__.py
│   │       ├── alerts.py
│   │       ├── context.py
│   │       ├── days_status.py
│   │       └── filters.py
│   ├── monitor.py - Модуль с функциями мониторинга эндпоинтов
│   ├── passport.py - Модуль авторизации запросов через moex.passport.com
│   ├── scheduler.py - Модуль расписания задач
│   ├── static - папка для временного хранения изображения с графиками
│   ├── trading_calendar.json - сгенерированное торговое расписание со статусами для каждого дня
│   └── trading_calendar.py - Модуль работы с торговым расписанием
└── supervisord.conf - Конфиг супервизора для автосборки Docker
```

``` .sh
> print current jobs list - jobs:   jobs
Job ID: EQ1
Next Run Time: 2024-07-15 13:15:10+03:00
Trigger: interval[0:01:00]
Function: <bound method TradingScheduler.eq_monitoring_delays of <__main__.TradingScheduler object at 0x10048cf70>>
--------------------
Job ID: FO1
Next Run Time: 2024-07-15 13:15:10+03:00
Trigger: interval[0:01:00]
Function: <bound method TradingScheduler.fo_monitoring_delays of <__main__.TradingScheduler object at 0x10048cf70>>
--------------------
Job ID: FX1
Next Run Time: 2024-07-15 13:15:10+03:00
Trigger: interval[0:01:00]
Function: <bound method TradingScheduler.fx_monitoring_delays of <__main__.TradingScheduler object at 0x10048cf70>>
--------------------
Job ID: FO2
Next Run Time: 2024-07-15 14:10:10+03:00
Trigger: interval[0:01:00]
Function: <bound method TradingScheduler.fo_monitoring_delays of <__main__.TradingScheduler object at 0x10048cf70>>
--------------------
Job ID: Send_plots
Next Run Time: 2024-07-15 19:02:05+03:00
Trigger: cron[hour='19', minute='2', second='5']
Function: <bound method TradingScheduler.send_plots_to_chat of <__main__.TradingScheduler object at 0x10048cf70>>
--------------------
Job ID: hi2_check
Next Run Time: 2024-07-15 19:03:30+03:00
Trigger: cron[hour='19', minute='3', second='30']
Function: <bound method TradingScheduler.hi2_checker of <__main__.TradingScheduler object at 0x10048cf70>>
--------------------
Job ID: FO3
Next Run Time: 2024-07-15 19:10:10+03:00
Trigger: interval[0:01:00]
Function: <bound method TradingScheduler.fo_monitoring_delays of <__main__.TradingScheduler object at 0x10048cf70>>
--------------------
Job ID: Daily_run_jobs
Next Run Time: 2024-07-16 00:00:00+03:00
Trigger: cron[hour='0', minute='0', second='0']
Function: <bound method TradingScheduler.run_jobs of <__main__.TradingScheduler object at 0x10048cf70>>
--------------------
```
