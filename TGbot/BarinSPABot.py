import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot import types
import json
import time
import os
from telebot.types import InputMediaAudio
bot = AsyncTeleBot("8484635702:AAFgb6Jr9Jd22CUKJ2RaIJUAkcJjOT_dbkI")
processing = False
DATA_FILE = 'user_data.json'



if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        user_data = json.load(f)
else:
    user_data = {}
#-------------------------------------------------------------------------------------------------------------------
#Для прогрева
#---------------------------------------------
# Работа с JSON
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

#---------------------------------------------
# Отправка сообщения конкретного шага
async def send_step(chat_id, step):
    if step >= len(MESSAGES):
        return
    await bot.send_message(chat_id, MESSAGES[step]["text"], reply_markup=MESSAGES[step]["keyboard"]())

#---------------------------------------------
# Таймер
async def wait_and_send(chat_id):
    data = load_data()
    user = data.get(str(chat_id))
    if not user:
        return
    delay = user["send_at"] - time.time()
    if delay > 0:
        await asyncio.sleep(delay)
    await send_next(chat_id)

async def send_next(chat_id):
    data = load_data()
    user = data.get(str(chat_id))
    if not user:
        return

    step = user["step"]
    await send_step(chat_id, step)

    # увеличиваем шаг
    user["step"] += 1
    data[str(chat_id)] = user  # <- Сохраняем всегда
    save_data(data)

    # планируем следующий шаг только если он есть
    if user["step"] < len(MESSAGES):
        user["send_at"] = time.time() + 24*60*60
        data[str(chat_id)] = user
        save_data(data)
        asyncio.create_task(wait_and_send(chat_id, user))

async def wait_and_send(chat_id, user):
    delay = user["send_at"] - time.time()
    if delay > 0:
        await asyncio.sleep(delay)
    await send_next(chat_id)

#-------------------------------------------------------------------------------------------------------------------
#приветствие
@bot.message_handler(commands=['start'])
async def start(message):
    await bot.send_message(message.chat.id, "Здравствуйте. \n"
                                      "Если вы всегда в движении и редко находите время для отдыха — вы в правильном месте. "
                                      "Я помогаю вернуть телу мягкость, а уму — покой. "
                                      "Здесь все, чтобы вы могли легко найти путь в Барин СПА — контакты, цены, акции и все, "
                                      "чтобы чувствовать себя легче.", reply_markup=startMenuButton())
    chat_id = str(message.chat.id)
    data = load_data()

    if chat_id not in data:
        data[chat_id] = {"step": 0, "send_at": time.time() + 3}
        save_data(data)
        asyncio.create_task(wait_and_send(chat_id, data[chat_id]))

@bot.message_handler(commands=["subscriberStatistics"])
async def subscriber_statistics(message):
    data = load_data()
    total = len(data)
    counts = [0, 0, 0, 0, 0]  # сколько пользователей дошли до каждого шага
    for user in data.values():
        step = user.get("step", 0)
        for i in range(step):
            if i < 5:
                counts[i] += 1

    stats = (
        f"Всего подписчиков: {total}\n"
        f"Получили 2-е сообщение: {counts[1]}\n"
        f"Получили 3-е сообщение: {counts[2]}\n"
        f"Получили 4-е сообщение: {counts[3]}\n"
        f"Получили 5-е сообщение: {counts[4]}"
    )
    await bot.send_message(message.chat.id, stats)


#кнопки прогрева 1 день
def warmingUpButtons():
    keyboard = types.InlineKeyboardMarkup()
    giftsBTN = types.InlineKeyboardButton("Получить аудио-практики", callback_data="gifts")
    menuBTN = types.InlineKeyboardButton("Меню", callback_data="menu")
    keyboard.add(giftsBTN)
    keyboard.add(menuBTN)
    return keyboard

#кнопка меню
def startMenuButton():
    keyboard = types.InlineKeyboardMarkup()
    menuBTN = types.InlineKeyboardButton("Меню", callback_data="menu")
    keyboard.add(menuBTN)
    return keyboard

#-----------------------------------------------------------------------------------------------------------------------

#статистика по подписчикам
@bot.message_handler(commands=['subscriberStatistics'])
async def subcount(message):
    count = len(user_data["subscribers"])
    await bot.send_message(message.chat.id, f"Подписчиков: {count}")

#-----------------------------------------------------------------------------------------------------------------------

#сообщение главного меню
@bot.callback_query_handler(func=lambda call: call.data == "menu")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id)
        return
    processing = True
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id,"Главное меню — все под рукой, чтобы забота о себе была простой и приятной.",
                     reply_markup=mainMenu())
    processing = False

#кнопки главного меню
def mainMenu():
    keyboard = types.InlineKeyboardMarkup()
    giftsBTN = types.InlineKeyboardButton("Подарки", callback_data="gifts")
    addressBTN = types.InlineKeyboardButton("Адрес", callback_data="address")
    phoneBTN = types.InlineKeyboardButton("Телефон", callback_data="phone")
    masterBTN = types.InlineKeyboardButton("О мастере", callback_data="master")
    programsBTN = types.InlineKeyboardButton("Программы и Цены", callback_data="programs")
    methodsBTN = types.InlineKeyboardButton("Методики", callback_data="methods")
    FAQBTN = types.InlineKeyboardButton("Частые вопросы", callback_data="FAQ")
    signUpBTN = types.InlineKeyboardButton(text="Записаться", url="https://t.me/Al_Shumeyko")
    keyboard.add(giftsBTN, addressBTN)
    keyboard.add(phoneBTN, masterBTN)
    keyboard.add(programsBTN, methodsBTN)
    keyboard.add(FAQBTN)
    keyboard.add(signUpBTN)
    return keyboard

#-----------------------------------------------------------------------------------------------------------------------

#адрес
@bot.callback_query_handler(func=lambda call: call.data == "address")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id,"https://yandex.ru/maps/-/CLbcmIPwУл. \n\n"
                                          "Шаболовка 25 к 2 Вход со двора возле 4 подъезда Коричневая дверь под козырьком. \n"
                                          "Работаю ежедневно с 9:00 до 20:00. \n"
                                          "(только по предварительной записи)",
                     reply_markup=startMenuButton())
    processing = False

#-----------------------------------------------------------------------------------------------------------------------

#телефон
@bot.callback_query_handler(func=lambda call: call.data == "phone")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id,"Напишите в Telegram, WhatsApp или отправьте SMS — я на связи и отвечу быстро. \n\n"
                                          "+79685463183",
                     reply_markup=startMenuButton())
    processing = False

#-----------------------------------------------------------------------------------------------------------------------

#сообщение Программы и Цены
@bot.callback_query_handler(func=lambda call: call.data == "programs")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id,"У каждого свой ритм и своя степень усталости. \n"
                                          "Здесь вы можете выбрать программу, которая поможет именно вашему телу.",
                     reply_markup=programsButtons())
    processing = False

#кнопки Программы и Цены
def programsButtons():
    keyboard = types.InlineKeyboardMarkup()
    oneHourBTN = types.InlineKeyboardButton("1 час - 5 000 ₽", callback_data="oneHour")
    oneAndHalfHoursBTN = types.InlineKeyboardButton("1 час 30 мин - 7 500 ₽", callback_data="oneAndHalfHours")
    twoHoursBTN = types.InlineKeyboardButton("2 часа - 10 000 ₽", callback_data="twoHours")
    menuBTN = types.InlineKeyboardButton("Меню", callback_data="menu")
    keyboard.add(oneHourBTN)
    keyboard.add(oneAndHalfHoursBTN)
    keyboard.add(twoHoursBTN)
    keyboard.add(menuBTN)
    return keyboard

#Сообщения программа 1 час
@bot.callback_query_handler(func=lambda call: call.data == "oneHour")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id,"Горячие камни + глубокая проработка тела для снятия стресса. \n"
                                          "Дыхательная практика «квадратное дыхание» помогает замедлиться, "
                                          "а музыка в ритме 60 bpm поддерживает естественный ритм сердца и успокаивает ум. \n"
                                          "Завершение — чашка индивидуально подобранного травяного чая. \n\n"
                                          "Стоимость: 5 000 ₽",
                     reply_markup=eachProgramsButtons())
    processing = False

#Сообщения программа 1 час 30 мин
@bot.callback_query_handler(func=lambda call: call.data == "oneAndHalfHours")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id,"Больше времени на восстановление: \n"
                                          "горячие камни, СПА-ритуал для расслабления мышц и снятия тревожности, "
                                          "дыхание в ритме «квадрата» и музыка 60 bpm для глубокого спокойствия. \n"
                                          "Финал — чайный ритуал с травяным сбором на выбор. \n\n"
                                          "Стоимость: 7 500 ₽",
                     reply_markup=eachProgramsButtons())
    processing = False

#Сообщения программа 2 часа
@bot.callback_query_handler(func=lambda call: call.data == "twoHours")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id,"Максимальное погружение в атмосферу СПА. \n"
                                          "Фитобочка для мягкой детоксикации организма, горячие камни, расслабляющий "
                                          "СПА-ритуал, дыхательная техника «квадратное дыхание» и музыка в ритме 60 bpm "
                                          "для перезагрузки нервной системы. \n"
                                          "В завершение — авторский чайный ритуал. \n\n"
                                          "Стоимость: 10 000 ₽",
                     reply_markup=eachProgramsButtons())
    processing = False

#кнопки для каждой отдельной программы
def eachProgramsButtons():
    keyboard = types.InlineKeyboardMarkup()
    programsBTN = types.InlineKeyboardButton("Все программы", callback_data="programs")
    menuBTN = types.InlineKeyboardButton("Меню", callback_data="menu")
    keyboard.add(programsBTN)
    keyboard.add(menuBTN)
    return keyboard

#-----------------------------------------------------------------------------------------------------------------------

#сообщение методики
@bot.callback_query_handler(func=lambda call: call.data == "methods")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id,"Каждый сеанс в Барин СПА — это больше, чем массаж. \n"
                                          "Я объединяю несколько методов, которые помогают снять стресс, отпустить "
                                          "напряжение и вернуть телу естественное спокойствие. "
                                          "Тактильные, звуковые, ароматические и прочие элементы соединяются, "
                                          "чтобы глубоко расслабить тело и успокоить нервную систему. \n"
                                          "В этом разделе вы можете узнать подробнее о каждой из них.",
                     reply_markup=allMethodsButtons())
    processing = False

#кнопки все методики
def allMethodsButtons():
    keyboard = types.InlineKeyboardMarkup()
    massageBTN = types.InlineKeyboardButton("СПА массаж", callback_data="massage")
    stonesBTN = types.InlineKeyboardButton("Камни", callback_data="stones")
    breathingBTN = types.InlineKeyboardButton("Дыхание", callback_data="breathing")
    fitobedBTN = types.InlineKeyboardButton("Фитобочка", callback_data="fitobed")
    teaBTN = types.InlineKeyboardButton("Чай", callback_data="tea")
    musicBTN = types.InlineKeyboardButton("Музыка", callback_data="music")
    menuBTN = types.InlineKeyboardButton("Меню", callback_data="menu")
    keyboard.add(massageBTN, stonesBTN)
    keyboard.add(breathingBTN, fitobedBTN)
    keyboard.add(teaBTN, musicBTN)
    keyboard.add(menuBTN)
    return keyboard

#сообщение СПА массаж
@bot.callback_query_handler(func=lambda call: call.data == "massage")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id,"СПА‑массаж\n"
                                          "Мягкое, глубокое воздействие на мышцы и фасции улучшает "
                                          "кровообращение, снижает мышечные зажимы и активирует парасимпатическую "
                                          "нервную систему — ту самую, что отвечает за отдых и восстановление. \n"
                                          "Через тактильные сигналы организм получает четкий сигнал «опасности нет», "
                                          "из-за чего снижается уровень кортизола, нормализуется дыхание и появляется "
                                          "ощущение тяжелого, приятного расслабления.",
                     reply_markup=methodButtons())
    processing = False

#сообщение Камни
@bot.callback_query_handler(func=lambda call: call.data == "stones")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id,"Горячие камни \n"
                                          "Тепло от базальтовых камней постепенно прогревает глубокие "
                                          "слои мышц, улучшает циркуляцию крови и лимфы, снижает чувствительность "
                                          "болевых рецепторов и помогает мышечным волокнам быстрее «отпустить» напряжение. \n"
                                          "Это создает идеальные условия для дальнейшего массажа: тело становится мягче, "
                                          "спокойнее и быстрее поддается работе.",
                     reply_markup=methodButtons())
    processing = False

#сообщение Дыхание
@bot.callback_query_handler(func=lambda call: call.data == "breathing")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id,"Дыхательные практики \n"
                                          "Клиенты часто приходят запыхавшимися и на взводе — "
                                          "после дороги, работы или бытовой суеты — и первая часть сеанса уходит на то, "
                                          "чтобы тело вообще “догнало” голову. Из-за этого часть сеанса работает "
                                          "слабее (или даже вхолостую), и общий эффект от сеанса снижается. \n"
                                          "Специально подобранный темп дыхания снижает частоту сердцебиения, выравнивает "
                                          "ритм нервной системы и переводит организм из режима «борьбы и стресса» в режим «восстановления». \n"
                                          "Всего несколько минут правильной дыхательной настройки уже уменьшают уровень "
                                          "кортизола и подготавливают тело к полноценному расслаблению.",
                     reply_markup=methodButtons())
    processing = False

#сообщение Фитобочка
@bot.callback_query_handler(func=lambda call: call.data == "fitobed")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id,"Фитобочка \n"
                                          "Это мягкая паровая баня, в которой прогревается тело, но голова "
                                          "остается вне пара — нагрузка на сердце минимальна, а расслабление глубокое. \n"
                                          "Тепло расширяет сосуды, ускоряет обменные процессы, улучшает подвижность "
                                          "тканей и помогает телу быстрее избавиться от ощущения «скованности» и усталости. \n"
                                          "Это отличный способ предварительного разогрева перед массажем.",
                     reply_markup=methodButtons())
    processing = False

#сообщение Чай
@bot.callback_query_handler(func=lambda call: call.data == "tea")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id,"Травяные чаи \n"
                                          "Перед началом сеанса мы с клиентом создаем уникальный чай под "
                                          "его предпочтения: сперва выбираем одну расслабляющую основу, затем одну "
                                          "вкусовую, и одну ароматическую. Полученная смесь - и будет тот чай, "
                                          "которым завершится сеанс. \n"
                                          "1. Успокаивающая база: липа, мелисса, лаванда, ромашка. \n"
                                          "2. Вкусовой акцент: сушёная малина, цедра апельсина, корица, кардамон. \n"
                                          "3. Ароматический акцент: жасмин, роза, лемонграсс, ваниль.\n"
                                          "Комбинация этих трав действует сразу по двум направлениям: мягко расслабляет "
                                          "нервную систему и поддерживает тело за счет природных "
                                          "эфирных масел и фитокомпонентов. \n"
                                          "Чай завершает сеанс, фиксирует состояние спокойствия и "
                                          "помогает телу мягко вернуться в тонус. \n"
                                          "При этом все ингредиенты подобраны так, чтобы по вкусу, аромату и эффекту "
                                          "гармонично дополняли друг друга.",
                     reply_markup=methodButtons())
    processing = False

#сообщение Музыка
@bot.callback_query_handler(func=lambda call: call.data == "music")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id,"Музыка (Lo‑Fi 60 BPM) \n"
                                          "Ритм 60 ударов в минуту совпадает "
                                          "с частотой спокойного сердцебиения. \n"
                                          "Такое звучание снижает скорость мыслительной активности, стабилизирует дыхание "
                                          "и создает эффект «медленного погружения» в расслабление. \n"
                                          "Музыка становится фоном, который помогает телу и уму синхронизироваться "
                                          "и постепенно успокаиваться во время сеанса.",
                     reply_markup=methodButtons())
    processing = False

#кнопки каждой методики
def methodButtons():
    keyboard = types.InlineKeyboardMarkup()
    methodsBTN = types.InlineKeyboardButton("Методики", callback_data="methods")
    menuBTN = types.InlineKeyboardButton("Меню", callback_data="menu")
    keyboard.add(methodsBTN)
    keyboard.add(menuBTN)
    return keyboard

#-----------------------------------------------------------------------------------------------------------------------

# сообщение Частые вопросы
@bot.callback_query_handler(func=lambda call: call.data == "FAQ")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id,"1. Стоит ли это своих денег?\n"
                                          "2. Я уже пробовал массаж — чем ваш отличается от того, что я уже видел?\n"
                                          "3. Как быть, если у меня очень напряженный график и записываться заранее неудобно?\n"
                                          "4. Поможет ли мне массаж, если мое напряжение — не физическое, а из-за работы и жизни?\n"
                                          "5. Как вообще работает ваш комплексный подход? В чем логика?\n"
                                          "6. А не станет ли хуже после массажа? Я слышал, что бывает усиление напряжения.",
                     reply_markup=allFAQButtons())
    processing = False

# меню все Частые вопросы
def allFAQButtons():
    keyboard = types.InlineKeyboardMarkup()
    questionOneBTN = types.InlineKeyboardButton("1.", callback_data="questionOne")
    questionTwoBTN = types.InlineKeyboardButton("2.", callback_data="questionTwo")
    questionThreeBTN = types.InlineKeyboardButton("3.", callback_data="questionThree")
    questionFourBTN = types.InlineKeyboardButton("4.", callback_data="questionFour")
    questionFiveBTN = types.InlineKeyboardButton("5.", callback_data="questionFive")
    questionSixBTN = types.InlineKeyboardButton("6.", callback_data="questionSix")
    menuBTN = types.InlineKeyboardButton("Меню", callback_data="menu")
    keyboard.add(questionOneBTN, questionTwoBTN)
    keyboard.add(questionThreeBTN, questionFourBTN)
    keyboard.add(questionFiveBTN, questionSixBTN)
    keyboard.add(menuBTN)
    return keyboard

# сообщение Вопрос 1
@bot.callback_query_handler(func=lambda call: call.data == "questionOne")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id,"1. Стоит ли это своих денег?\n"
                                          "Массаж — это не трата, а вклад в ваше состояние: снижение стресса, "
                                          "улучшение сна, меньше головного и мышечного напряжения, больше энергии. "
                                          "Результат вы ощущаете телом, эмоциями и работоспособностью.",
                     reply_markup=FAQButtons())
    processing = False

# сообщение Вопрос 2
@bot.callback_query_handler(func=lambda call: call.data == "questionTwo")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id,"2. Я уже пробовал массаж — чем ваш отличается от того, что я уже видел?\n"
                                          "Основное отличие — в последовательности и внимании к деталям. "
                                          "Я не «просто мну мышцы». Я выстраиваю сеанс так, чтобы тело постепенно "
                                          "отпускало напряжение: дыхательная настройка, расслабляющая музыка, "
                                          "тепло камней, массаж, финальный чай. Это не разрозненные элементы, "
                                          "а единая система, которая дает более глубокий эффект, воздействуя на тело "
                                          "сразу через несколько каналов — дыхание, звук, тепло, запах и тактильные ощущения.",
                     reply_markup=FAQButtons())
    processing = False

# сообщение Вопрос 3
@bot.callback_query_handler(func=lambda call: call.data == "questionThree")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id,"3. Как быть, если у меня очень напряженный график и записываться заранее неудобно?\n"
                                          "Понимаю — у многих плотный ритм. Но массаж работает лучше, когда он запланирован. \n"
                                          "Ожидание сеанса само по себе помогает переключиться и настроиться на отдых — невозможно "
                                          "«прибежать и как можно быстрее расслабиться», это звучит противоречиво. "
                                          "Вы бронируете удобный слот заранее, и он становится гарантированным "
                                          "часом вашего восстановления. "
                                          "К тому же я всегда стараюсь предлагать несколько вариантов времени, "
                                          "чтобы вписать сеанс в ваш график без стресса.",
                     reply_markup=FAQButtons())
    processing = False

# сообщение Вопрос 4
@bot.callback_query_handler(func=lambda call: call.data == "questionFour")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id,"4. Поможет ли мне массаж, если мое напряжение — не физическое, а из-за работы и жизни?\n"
                                          "Да. Психическое и физическое напряжение — одна система. \n"
                                          "Ментальное напряжение отражается в теле — зажимами, усталостью и нарушением "
                                          "сна, а накопившееся телесное напряжение в ответ "
                                          "усиливает тревожность и внутренний стресс. "
                                          "Массаж помогает разорвать этот цикл: тело расслабляется — "
                                          "и голова буквально «отпускает».",
                     reply_markup=FAQButtons())
    processing = False

# сообщение Вопрос 5
@bot.callback_query_handler(func=lambda call: call.data == "questionFive")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id,"5. Как вообще работает ваш комплексный подход? В чем логика?\n"
                                          "Вся структура сеанса построена на физиологии: сначала дыхательная "
                                          "настройка снижает уровень кортизола и переводит нервную систему в "
                                          "более спокойный режим, затем тепло камней мягко разогревает мышцы и "
                                          "улучшает кровоток, массаж точечно прорабатывает зажимы и возвращает "
                                          "телу подвижность, а финальное расслабление с лосьоном помогает "
                                          "нервной системе закрепить результат и удержать состояние покоя. \n"
                                          "Это не магия — это последовательный, управляемый процесс, "
                                          "где каждый этап логично продолжает предыдущий и усиливает общий эффект.",
                     reply_markup=FAQButtons())
    processing = False

# сообщение Вопрос 6
@bot.callback_query_handler(func=lambda call: call.data == "questionSix")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id,"6. А не станет ли хуже после массажа? Я слышал, что бывает усиление напряжения.\n"
                                          "Ухудшения состояния и травмы обычно бывают после сильного и грубого "
                                          "воздействия на тело (тайский массаж, иглоукалывание, хиропрактика и т.д.). "
                                          "В моём подходе нет ничего подобного — движения плавные, мягкие и "
                                          "физиологичные, через уважение к мышцам и нервной системе. \n"
                                          "Максимум, что вы можете почувствовать после сеанса — легкую сонливость, "
                                          "которая вскоре проходит.",
                     reply_markup=FAQButtons())
    processing = False

#кнопки каждоо вопроса
def FAQButtons():
    keyboard = types.InlineKeyboardMarkup()
    FAQBTN = types.InlineKeyboardButton("Частые вопросы", callback_data="FAQ")
    menuBTN = types.InlineKeyboardButton("Меню", callback_data="menu")
    keyboard.add(FAQBTN)
    keyboard.add(menuBTN)
    return keyboard

#-----------------------------------------------------------------------------------------------------------------------

#сообщение О мастере
@bot.callback_query_handler(func=lambda call: call.data == "master")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id)
    with open('0.jpg', 'rb') as photo:
        await bot.send_photo(call.message.chat.id, photo, caption="Меня зовут Александр.\n"
                                          "Я начал изучать классический массаж ещё до окончания медицинского колледжа, "
                                          "а с 2015 года практикую и постоянно повышаю квалификацию. \n"
                                          "Проходил курсы по спортивному, лимфодренажному и антицеллюлитному массажу, "
                                          "LPG и различным SPA-процедурам.Сейчас я сосредоточен на разработке авторской "
                                          "техники, которая помогает эффективно справляться со стрессом и усталостью. \n"
                                          "Я никогда не останавливаюсь на достигнутом и постоянно совершенствую методику, "
                                          "изучая новые подходы, чтобы каждая процедура была максимально "
                                          "полезной и лаконично вписывалась в программу.",
                     reply_markup=masterButtons())
        processing = False

#кнопки О мастере
def masterButtons():
    keyboard = types.InlineKeyboardMarkup()
    diplomasBTN = types.InlineKeyboardButton("Дипломы и сертификаты", callback_data="diplomas")
    menuBTN = types.InlineKeyboardButton("Меню", callback_data="menu")
    keyboard.add(diplomasBTN)
    keyboard.add(menuBTN)
    return keyboard

#сообщение Дипломы и сертификаты
@bot.callback_query_handler(func=lambda call: call.data == "diplomas")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id)
    media = [
        types.InputMediaPhoto(open('1.jpg', 'rb')),
        types.InputMediaPhoto(open('2.jpg', 'rb')),
        types.InputMediaPhoto(open('3.jpg', 'rb')),
        types.InputMediaPhoto(open('4.jpg', 'rb')),
        types.InputMediaPhoto(open('5.jpg', 'rb')),
        types.InputMediaPhoto(open('6.jpg', 'rb'))
    ]
    await bot.send_media_group(call.message.chat.id, media)
    await bot.send_message(call.message.chat.id,"Здесь представлены большинство моих дипломов и сертификатов.\n"
                                          "Среди них:\n"
                                          "- Классический массаж\n"
                                          "- Баночный массаж\n"
                                          "- Массаж головы\n"
                                          "- Коррекция фигуры\n"
                                          "- Массаж LPG\n"
                                          "- Массажист - универсал\n"
                                          "- Диплом по специальности «Сестринское дело» и др.",
                     reply_markup=diplomasButtons())
    processing = False


#кнопки Дипломы и сертификаты
def diplomasButtons():
    keyboard = types.InlineKeyboardMarkup()
    menuBTN = types.InlineKeyboardButton("Меню", callback_data="menu")
    keyboard.add(menuBTN)
    return keyboard

#-----------------------------------------------------------------------------------------------------------------------

#сообщение Подарки
@bot.callback_query_handler(func=lambda call: call.data == "gifts")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id,"Дыхательные практики\n"
                                          "Попробуйте каждую технику и выберите ту, которая ощущается наиболее "
                                          "комфортной и естественной именно для вас. \n"
                                          "Регулярность важнее длительности: 3–5 минут в день уже дадут заметный результат.\n"
                                          "Практикуйте и отслеживайте, как меняется ваше состояние.",
                     reply_markup=allGiftsButtons())
    processing = False

#кнопки ко всем подаркам
def allGiftsButtons():
    keyboard = types.InlineKeyboardMarkup()
    practiceOneBTN = types.InlineKeyboardButton("1. Квадратное дыхание", callback_data="practiceOne")
    practiceTwoBTN = types.InlineKeyboardButton("2. Дыхание 4–7–8", callback_data="practiceTwo")
    practiceThreeBTN = types.InlineKeyboardButton("3. Кохерентное дыхание", callback_data="practiceThree")
    practiceFourBTN = types.InlineKeyboardButton("4. Дыхание с акцентом на выдох", callback_data="practiceFour")
    practiceFiveBTN = types.InlineKeyboardButton("5. Дыхание с мягкой паузой", callback_data="practiceFive")
    menuBTN = types.InlineKeyboardButton("Меню", callback_data="menu")
    keyboard.add(practiceOneBTN)
    keyboard.add(practiceTwoBTN)
    keyboard.add(practiceThreeBTN)
    keyboard.add(practiceFourBTN)
    keyboard.add(practiceFiveBTN)
    keyboard.add(menuBTN)
    return keyboard


# сообщение практика 1
@bot.callback_query_handler(func=lambda call: call.data == "practiceOne")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id, text="Готовлю файлы...")
    media = [
        InputMediaAudio("CQACAgIAAxkBAAIGymlMHVoBFUUsaqWFXUmEa7hxjf4KAAK3lAACtBhgSoiTjU7doD0sNgQ"),
        InputMediaAudio("CQACAgIAAxkBAAIGzGlMHYEEdl0LP-ezDdEXY7iVjSKhAAK9lAACtBhgSsnLlied3PojNgQ"),
        InputMediaAudio("CQACAgIAAxkBAAIGzmlMHZb6TCOaz5CetnG4ZEj8-RfKAALBlAACtBhgSlC3uuH0Y9zeNgQ")
    ]
    await bot.send_media_group(call.message.chat.id, media)
    await bot.send_message(call.message.chat.id,"Приятной практики)\n"
                                          "Эти и другие записи всегда доступны в разделе «Подарки» в главном меню.",
                     reply_markup=giftsButtons())
    processing = False

# сообщение практика 2
@bot.callback_query_handler(func=lambda call: call.data == "practiceTwo")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id, text="Готовлю файлы...")
    media = [
        InputMediaAudio("CQACAgIAAxkBAAIG0GlMHc060fY-QC8p-apQk4ghEdaaAALIlAACtBhgSi0aQ_m7_41NNgQ"),
        InputMediaAudio("CQACAgIAAxkBAAIG0mlMHdo2f1LzlJ1NKZjPWr3z-kXLAALJlAACtBhgSrtEJCUfluAiNgQ"),
        InputMediaAudio("CQACAgIAAxkBAAIG1GlMHekjZWomV4gM3AfxwiaCzZ5-AALKlAACtBhgSlLHVXlZNteZNgQ")
    ]
    await bot.send_media_group(call.message.chat.id, media)
    await bot.send_message(call.message.chat.id,"Приятной практики)\n"
                                          "Эти и другие записи всегда доступны в разделе «Подарки» в главном меню.",
                     reply_markup=giftsButtons())
    processing = False

# сообщение практика 3
@bot.callback_query_handler(func=lambda call: call.data == "practiceThree")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id, text="Готовлю файлы...")
    media = [
        InputMediaAudio("CQACAgIAAxkBAAIG1mlMHgABNvpzeDd2qN6BdGJ4P9onwAACzZQAArQYYEojtEJAZuy5hTYE"),
        InputMediaAudio("CQACAgIAAxkBAAIG2GlMHgzQGR4zff5sEYq9AijnSB5fAALOlAACtBhgSm5BEZrlqdrnNgQ"),
        InputMediaAudio("CQACAgIAAxkBAAIG2mlMHhxybMyXE9HeuE0pO3CIYOBFAALSlAACtBhgSoB-ipZ6DYL7NgQ")
    ]
    await bot.send_media_group(call.message.chat.id, media)
    await bot.send_message(call.message.chat.id,"Приятной практики)\n"
                                          "Эти и другие записи всегда доступны в разделе «Подарки» в главном меню.",
                     reply_markup=giftsButtons())
    processing = False

# сообщение практика 4
@bot.callback_query_handler(func=lambda call: call.data == "practiceFour")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id, text="Готовлю файлы...")
    media = [
        InputMediaAudio("CQACAgIAAxkBAAIG3GlMHkMEf7GuEMnogIpZyFTC3uI9AALYlAACtBhgSo-p0Gh1CnteNgQ"),
        InputMediaAudio("CQACAgIAAxkBAAIG3mlMHlDeelAni8NZRoqBq-m8izGyAALalAACtBhgSgQPQoRqcuHkNgQ"),
        InputMediaAudio("CQACAgIAAxkBAAIG4GlMHmNBIINzNJR-QxDXLdhxnSHWAALelAACtBhgShiAx7d5wLGJNgQ")
    ]
    await bot.send_media_group(call.message.chat.id, media)
    await bot.send_message(call.message.chat.id,"Приятной практики)\n"
                                          "Эти и другие записи всегда доступны в разделе «Подарки» в главном меню.",
                     reply_markup=giftsButtons())
    processing = False

# сообщение практика 5
@bot.callback_query_handler(func=lambda call: call.data == "practiceFive")
async def menu_callback(call):
    global processing
    if processing:
        await bot.answer_callback_query(call.id, text="Пожалуйста, подождите...")
        return
    processing = True
    await bot.answer_callback_query(call.id, text="Готовлю файлы...")
    media = [
        InputMediaAudio("CQACAgIAAxkBAAIG4mlMHm9kvTzkSJF39T3qA5DNt1atAALflAACtBhgSpN-shWFRufxNgQ"),
        InputMediaAudio("CQACAgIAAxkBAAIG5GlMHnpTKVKn343Fhw2R5PeUSzKjAALjlAACtBhgSriAJrGHBEyDNgQ"),
        InputMediaAudio("CQACAgIAAxkBAAIG5mlMHofohEHsAnH03cb03ykgIzQ8AALklAACtBhgSrjBWvxfdw4WNgQ")
    ]
    await bot.send_media_group(call.message.chat.id, media)
    await bot.send_message(call.message.chat.id,"Приятной практики)\n"
                                          "Эти и другие записи всегда доступны в разделе «Подарки» в главном меню.",
                     reply_markup=giftsButtons())
    processing = False

#кнопки к каждой практике
def giftsButtons():
    keyboard = types.InlineKeyboardMarkup()
    giftsBTN = types.InlineKeyboardButton("Все практики", callback_data="gifts")
    menuBTN = types.InlineKeyboardButton("Меню", callback_data="menu")
    keyboard.add(giftsBTN)
    keyboard.add(menuBTN)
    return keyboard

#--------------------------------------------------------------------------------------------------------------------
#Заявка
ADMIN_CHAT_ID = 1044979384  # твой Telegram ID, куда приходят заявки
user_states = {}  # словарь для хранения состояния пользователя

# Кнопка "Получить скидку"
def discountButtons():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("Получить скидку", callback_data="discount"))
    menuBTN = types.InlineKeyboardButton("Меню", callback_data="menu")
    keyboard.add(menuBTN)
    return keyboard

# Обработка нажатия кнопки
@bot.callback_query_handler(func=lambda c: c.data == "discount")
async def handle_discount(call):
    chat_id = call.message.chat.id
    user_states[chat_id] = {"step": 1}  # начинаем диалог
    await bot.send_message(chat_id, "Как мне к вам обращаться?")

# Обработка текста от пользователя
@bot.message_handler(func=lambda message: message.chat.id in user_states)
async def handle_user_input(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)

    if state["step"] == 1:
        state["name"] = message.text
        state["step"] = 2
        await bot.send_message(chat_id, "По какому номеру я могу с вами связаться?")
    elif state["step"] == 2:
        state["phone"] = message.text
        # отправка заявки тебе
        await bot.send_message(ADMIN_CHAT_ID, f'Заявка: "{state["name"]}" "{state["phone"]}"')
        await bot.send_message(chat_id, "Спасибо! Ваша заявка отправлена.", reply_markup=startMenuButton())
        # очищаем состояние
        user_states.pop(chat_id, None)

#----------------------------------------------------------------------------------------------------------------------
#Сообщения прогрева
MESSAGES = [
    {
        "text": "Меня зовут Александр Шумейко. \n"
                "Более 10 лет назад я начал заниматься массажем, но, как любой медик, "
                "изначально рассматривал его исключительно с точки зрения физиологии, "
                "сосредоточившись на работе с мышцами. \n\n"
                "Однажды я столкнулся с хронической усталостью и стрессом. Упадок сил и "
                "отсутствие концентрации я ощущал уже с момента пробуждения, а напряжение в"
                " мышцах было лишь малой частью проблемы. \n\n"
                "Я долго считал это нормой, а слабость — проявлением лени и прокрастинации. "
                "Лишь достигнув предела, я начал искать выход. Стал проверять множество "
                "разнообразных методов. Это меня увлекло, "
                 "и я решил применять полученный опыт в работе. \n\n"
                 "Сейчас я воспринимаю массаж не просто как работу с мышцами, а как комплексный "
                 "процесс, который помогает снять внутреннее напряжение и вернуть ощущение спокойствия. \n\n"
                 "Одним из первых инструментов, которые дали ощутимый эффект, стали "
                 "дыхательные упражнения. Я подготовил для вас 5 коротких аудио-практик. "
                 "Выберите одну и попробуйте сегодня — это займёт пару минут, "
                 "но уже может дать облегчение.",
        "keyboard": warmingUpButtons
    },
    {
        "text": "Многие из нас привыкли жить в ускоренном режиме: плотный график, постоянные переключения между "
                "задачами, информационный шум и ощущение, что нужно успевать еще больше. И чем дольше мы поддерживаем "
                "этот темп, тем сильнее накапливается усталость. Она редко наступает внезапно — обычно тело заранее "
                "посылает сигналы, но мы их часто не замечаем. \n\n"
                "Вот несколько признаков, на которые стоит обратить внимание: \n"
                "- ухудшение концентрации и «туман» в голове; \n"
                "- постоянная усталость, даже при нормальном сне; \n"
                "- напряжение в шее, плечах, пояснице; \n"
                "- раздражительность; \n"
                "- скачки энергии: то упадок сил, то беспокойство. \n\n"
                "Если вы замечаете у себя подобные признаки, я рекомендую более детально изучить этот вопрос. "
                "Вот список из пяти книг, которые за годы моей практики оказались для меня самыми полезными и содержательными: \n"
                "1. «Антистресс. Как победить стресс, тревогу и депрессию без лекарств и психоанализа» — Давид Серван-Шрейбер. \n"
                "2. «Когда тело говорит НЕТ. Цена скрытого стресса» — Габор МАТЕ. \n"
                "3. «Почему у зебр не бывает инфарктов. Психология стресса» — Роберт Сапольски. \n"
                "4. «Радикальное принятие. Как исцелить психологическую травму и посмотреть на свою жизнь взглядом Будды» — Тара Брах. \n"
                "5. «Тело помнит все: какую роль психологическая травма играет в жизни человека и какие техники "
                "помогают ее преодолеть» — Бессел ван дер Колк. \n\n"
                "Все авторы сходятся в одном: стресс всегда оставляет след на теле. Но хорошая новость в том, "
                "что этот процесс обратим. Осознанность, дыхательные практики, массаж, контрастные и тепловые "
                "процедуры, полноценный сон, легкая физическая активность, цифровой детокс и четкие паузы на "
                "восстановление — все это помогает телу переключиться из режима «выживания» в режим восстановления. "
                "А вместе с этим возвращаются ясность, ровная энергия, способность концентрироваться и ощущение, что "
                "вы снова управляете своим днем, а не наоборот. ",
        "keyboard": startMenuButton
    },
    {
        "text": "Иногда стресс проявляется незаметно — через мелкие изменения, которые снижают продуктивность "
                "и ухудшают самочувствие. Сегодня я расскажу об одном таком случае. \n\n"
                "Недавно мой знакомый пожаловался на «возраст». Мы обсудили его состояние, и вот краткий список "
                "проблем, которые он мне описал: - Утром ему было сложно войти в рабочий ритм, он чувствовал себя заторможенным. \n"
                "- Во время вождения он замечал, что реагирует медленнее и иногда «подтупливает». \n"
                "- Ему пришлось увеличить интервал между тренировками, поскольку мышцы не успевали восстанавливаться. \n"
                "- На работе постоянно ерзал и не мог сидеть спокойно, так как тело быстро затекало. \n"
                "- Настроение часто менялось без видимых причин. \n\n"
                "Но там, где он увидел признаки старения, я распознал проявления скрытого напряжения. \n\n"
                "Я пригласил его на сеанс. До этого он не особо интересовался деталями моей работы, поэтому "
                "утверждал, что «размять мышцы, конечно, полезно, но это не решит его проблемы». Однако мне "
                "удалось его переубедить. Я рассказал, что уже давно расширил свои взгляды на сферу деятельности и "
                "теперь борюсь не с симптомами, а с причиной. Массаж стал лишь одним из моих инструментов. "
                "Когда он пришел ко мне, его ждал комплекс тщательно подобранных методик, которые "
                "с разных сторон помогают восстановить организм. \n\n"
                "После первого сеанса он заметил явные улучшения: шея стала более подвижной, сон в тот день был "
                "глубоким и безмятежным, а мысли приобрели ясность и четкость. С каждым новым визитом позитивных "
                "изменений становилось все больше. Сейчас он приходит ко мне пару раз в месяц, чисто для профилактики. ",
        "keyboard": startMenuButton
    },
    {
        "text": "Я несколько раз обращался к массажистам — и у всех история была примерно одинаковая: включить "
                "какое-то радио из разряда jazz fm для фона, уложить, обмазать маслом, размять и отправить домой. "
                "Я обратил внимание на то, что во время сеанса существует множество точек воздействия на организм — "
                "звук, аромат, дыхание, температура и многое другое, но никто не использует это в своей работе. \n\n"
                "Раньше я тоже проходил мимо этих возможностей, но теперь выстраиваю сеанс так, "
                "чтобы каждый его элемент был направлен на достижение цели и усиливал общий эффект. \n\n"
                "Как обычно проходит сеанс: \n\n"
                "Мы с клиентом создаем уникальный чай под его предпочтения: сперва выбираем расслабляющую основу, "
                "затем вкусовую, и ароматическую. Получается свой, персональный чай. Однако если делать это в "
                "конце сеанса — это выбивает из атмосферы и разрушает ощущение целостности процесса, "
                "поэтому мы начинаем именно с этого шага. \n\n"
                "Далее клиент укладывается. Я включаю короткую дыхательную практику, которая помогает ему "
                "сбросить уличную суету, успокоиться и настроиться на сеанс. Далее аудиозапись практики незаметно сменяется музыкой. \n\n"
                "На подбор этого плейлиста у меня ушло много времени. Для наибольшего эффекта музыка должна быть "
                "медленной, спокойной, без слов и знакомых мелодий, а также без резких звуков, которые могут отвлекать "
                "или напрягать. Я остановил свой выбор на таком жанре, как Lo-Fi - он отлично помогает расслабиться "
                "клиенту, а мне - держать ритм. \n\n"
                "В это время начинается массаж: мягкое разогревание, затем горячие камни, после — "
                "глубокая проработка мышц. В конце я убираю масло и наношу лосьон массажными движениями, "
                "чтобы кожа стала гладкой, а тело почувствовало завершенность. \n\n"
                "А в конце нас ожидает чаепитие. Клиент пробует тот самый чай, который мы собрали в начале. "
                "Этот ритуал завершает все предыдущие впечатления и мягко подводит итог всему процессу. \n\n"
                "После такого сеанса человек чувствует себя спокойно, глубоко расслабленно и удивительно обновленно — "
                "будто напряжение тает, а внутри наконец появляется легкость. И это состояние "
                "держится значительно дольше, чем после обычного массажа. ",
        "keyboard": startMenuButton
    },
    {
        "text": "Очень часто люди так проваливаются в ежедневную рутину, что перестают находить время "
                "даже на заботу о себе. Иногда человеку нужно всего одно напоминание, чтобы наконец позволить "
                "себе остановиться и восстановиться. Если вы читаете это сообщение — это и есть то самое напоминание. \n\n"
                "Последние несколько дней я показывал, как работает мой комплексный подход: "
                "дыхательная настройка, расслабляющая музыка, тепло камней, массаж, травяной чай в завершение. "
                "Это не набор эффектов, а логичная последовательность, которая помогает телу отпустить зажимы, "
                "а голове — вернуть ясность. \n\n"
                "И если вы давно подумывали попробовать, но откладывали — это хороший повод.\n\n"
                "Акция: \n"
                "Скидка 20% на следующий сеанс. Чтобы сохранить комфортный темп работы и уделять максимум внимания каждому, "
                "по акции могу принимать только 5 человек в неделю. \n\n"
                "Чтобы воспользоваться скидкой, нажмите на кнопку под этим сообщением — "
                "система попросит ваше имя и телефон, и я сам свяжусь с вами, чтобы подобрать удобный день и время. ",
        "keyboard": discountButtons #тут должны быть кнопки для записи по акции
    }
]
#----------------------------------------------------------------------------------------------------------------------
async def restore_all():
    data = load_data()
    for chat_id, user in data.items():
        if not chat_id.isdigit():  # игнорируем другие ключи, если есть
            continue
        asyncio.create_task(wait_and_send(chat_id, user))

async def main():
    await restore_all()
    await bot.infinity_polling()

asyncio.run(main())