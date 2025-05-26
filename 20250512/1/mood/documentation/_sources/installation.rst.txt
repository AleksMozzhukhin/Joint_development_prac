Установка и настройка
=====================

Требования
----------

* Python 3.12 или выше
* pipenv (рекомендуется)

Зависимости
-----------

Проект использует следующие основные зависимости:

* **cowsay** - для отображения монстров в ASCII-арт
* **babel** - для поддержки локализации
* **sphinx** - для генерации документации (только для разработки)

Установка через pipenv
----------------------

1. Клонируйте репозиторий:

   .. code-block:: bash

      git clone <repository-url>
      cd mood-game

2. Установите зависимости:

   .. code-block:: bash

      pipenv install

3. Активируйте виртуальное окружение:

   .. code-block:: bash

      pipenv shell

Установка через pip
-------------------

1. Установите пакет:

   .. code-block:: bash

      pip install mood-game

2. Или установите из исходников:

   .. code-block:: bash

      git clone <repository-url>
      cd mood-game
      pip install -e .

Настройка локализации
---------------------

Для работы русской локализации необходимо скомпилировать файлы переводов:

.. code-block:: bash

   # Если используете dodo
   doit i18n

   # Или вручную
   msgfmt mood/server/locale/ru/LC_MESSAGES/messages.po -o mood/server/locale/ru/LC_MESSAGES/messages.mo

Генерация документации
----------------------

Для генерации документации:

.. code-block:: bash

   # Если используете dodo
   doit html

   # Или вручную
   cd docs
   make html

Структура проекта
-----------------

.. code-block:: text

   mood/
   ├── __init__.py
   ├── client/
   │   ├── __init__.py
   │   ├── __main__.py
   │   └── game_client.py
   ├── common/
   │   ├── __init__.py
   │   └── constants.py
   └── server/
       ├── __init__.py
       ├── __main__.py
       ├── game_server.py
       └── locale/
           ├── babel.cfg
           ├── messages.pot
           └── ru/
               └── LC_MESSAGES/
                   ├── messages.po
                   └── messages.mo

Проверка установки
------------------

Для проверки корректной установки запустите:

.. code-block:: bash

   python -m mood.server --help
   python -m mood.client --help

Если команды выполняются без ошибок, установка прошла успешно.