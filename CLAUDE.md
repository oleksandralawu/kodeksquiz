# Квіз «20 пасток Сімейного кодексу»

Освітній веб-квіз Адвокатського бюро Олександри Стасюк (lawconsult.com.ua). Мова інтерфейсу й спілкування — українська.

## Структура
- `index.html` — увесь квіз в одному файлі: стилі, маскот Кодик (SVG), логіка і банк питань.
- `docs/vypravlena-redaktsiia-kvizu.docx` — затверджена редакція текстів (джерело правди для формулювань).
- `simeynepravo-kviz-svitlyi.png` — картинка для соцмереж 1200×630 (og:image, twitter:image).
- `tests/qa.py` — автотест (Playwright, 108 перевірок): `python3 tests/qa.py "$PWD/index.html"`.

## Де що в index.html
- `BLOCKS` — 5 тем: назва, кнопка фіналу, якір послуги.
- `QUESTIONS` — 60 питань (по 12 на тему): id, block, type, diff, trap, sensitive, help, situation, options, correct, short, full, norm, cta.
- `SITUATIONS` — вибір ситуації на старті: підказка й кнопка фіналу.
- `CONSULT_URL`, `consultLink()` — посилання на консультацію: якір + utm_source=kviz, utm_content=q<id> або final_…
- `QUIZ_URL` — адреса квізу для QR і картки сторіс: https://lawconsult.com.ua/kviz (підтверджено).
- `GA_ID` — ID Google Analytics 4, якщо на сайті немає GA/GTM. Події: quiz_start, quiz_situation, quiz_answer, quiz_more, quiz_cheer, quiz_consult_click, quiz_complete, quiz_share_copy, quiz_restart.

## Правила редагування
- Норми — лише за чинним текстом СК України; дата редакції вказана в примітці шторки.
- Кнопки (CTA): дія від першої особи, без обіцянок результату (етика адвоката).
- `sensitive: true` — заголовок «Що каже закон» без оцінки; `help: true` — блок гарячих ліній (лише питання про домашнє насильство, 3.3).
- Бажано: «Коротко» ≤ 25 слів, варіант відповіді ≤ 60 знаків, кожна стаття з «Норми» згадана в «Детальніше».
- Після змін — запускати `tests/qa.py`; файл має лишатися одним самодостатнім HTML.

## Відкриті питання
- `QUIZ_URL` підтверджено: https://lawconsult.com.ua/kviz.
- Публікація: квіз розміщено на GitHub Pages (https://oleksandralawu.github.io/kodeksquiz/) і вбудовано через iframe у сайт на Weblium. `<link rel="canonical">` вказує на https://lawconsult.com.ua/kviz. Щоб працювала кнопка «Скопіювати текст», iframe має мати `allow="clipboard-write"`.
- Папки `docs/` і `tests/` додано в репозиторій. Правки 1.8, 4.5 і 5.7 поки не перенесено в docx.
- Створити на сторінці сімейного права якорі: #shlyubnyi-dohovir, #podil-mayna, #rozluchennya, #alimenty, #dity, #za-kordonom, #konsultatsiya.
- Звірити пункти чек-листа з docx (2.3, 4.4, 5.8 тощо) і оновити дату редакції.
