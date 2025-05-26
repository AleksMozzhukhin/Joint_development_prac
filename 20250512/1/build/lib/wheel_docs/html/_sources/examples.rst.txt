Примеры использования
=====================

Запуск сервера
--------------

Базовый запуск
~~~~~~~~~~~~~~

.. code-block:: bash

   python -m mood.server

Запуск с настройками
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python -m mood.server --host 0.0.0.0 --port 8080

Подключение клиентов
--------------------

Интерактивный режим
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python -m mood.client --username player1

Выполнение команд из файла
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python -m mood.client --username bot1 --command-file example_commands.mood

Примеры команд
--------------

Движение по карте
~~~~~~~~~~~~~~~~~

.. code-block:: text

   > up          # Движение вверх
   > down        # Движение вниз
   > left        # Движение влево
   > right       # Движение вправо

Добавление монстров
~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   > addmon dragon coords 5 5 hp 100 hello "I am a mighty dragon!"
   > addmon goblin coords 3 3 hp 30 hello "Grr! I'm a goblin!"

Сражение с монстрами
~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   > attack dragon with sword
   > attack goblin with axe

Общение с игроками
~~~~~~~~~~~~~~~~~~

.. code-block:: text

   > sayall Hello, everyone!
   > sayall Let's go hunt some monsters!

Настройка системы
~~~~~~~~~~~~~~~~~

.. code-block:: text

   > movemonsters on     # Включить бродячих монстров
   > movemonsters off    # Выключить бродячих монстров
   > locale ru_RU.UTF8   # Переключиться на русский язык
   > locale en           # Переключиться на английский язык

Файл команд
-----------

Пример файла `example_commands.mood`:

.. code-block:: text

   # Это комментарий
   sayall Привет всем! Я бот.

   # Добавляем монстра
   addmon wolf coords 7 7 hp 50 hello "Awoooo!"

   # Перемещаемся к монстру
   right
   right
   right
   right
   right
   right
   right
   down
   down
   down
   down
   down
   down
   down

   # Атакуем монстра
   attack wolf with sword
   attack wolf with spear
   attack wolf with axe

   # Сообщаем о победе
   sayall Волк побежден!

   # Включаем бродячих монстров
   movemonsters on

   # Выходим
   quit

Режимы игры
-----------

Одиночная игра
~~~~~~~~~~~~~~

1. Запустите сервер:

   .. code-block:: bash

      python -m mood.server

2. В другом терминале подключите клиента:

   .. code-block:: bash

      python -m mood.client --username player1

Многопользовательская игра
~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Запустите сервер:

   .. code-block:: bash

      python -m mood.server

2. Подключите несколько клиентов из разных терминалов:

   .. code-block:: bash

      # Терминал 1
      python -m mood.client --username alice

      # Терминал 2
      python -m mood.client --username bob

      # Терминал 3
      python -m mood.client --username charlie

Автоматизированная игра
~~~~~~~~~~~~~~~~~~~~~~~

Создайте файл команд и запустите бота:

.. code-block:: bash

   python -m mood.client --username bot --command-file my_strategy.mood

Отладка и разработка
--------------------

Для отладки можно включить подробный вывод:

.. code-block:: bash

   # Запуск сервера с отладкой
   python -m mood.server --verbose

   # Запуск клиента с отладкой
   python -m mood.client --username test --verbose

Полезные советы
---------------

1. **Координаты**: Игровое поле имеет размер 10x10, координаты от (0,0) до (9,9)
2. **Кольцевание**: При выходе за границы поля игрок появляется с противоположной стороны
3. **Монстры**: Используйте команду `cowsay.list_cows()` в Python для получения списка доступных монстров
4. **Оружие**: Разное оружие наносит разный урон (меч: 10, копье: 15, топор: 20)
5. **Локализация**: Смена языка влияет только на системные сообщения сервера