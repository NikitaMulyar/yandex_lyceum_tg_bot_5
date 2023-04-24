import logging
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, Bot, ReplyKeyboardRemove
from config import BOT_TOKEN
import aiohttp


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)
bot = Bot(BOT_TOKEN)
API_GEO = '40d1649f-0493-4b70-98ba-98533de7710b'
URL_GEOCODER = 'http://geocode-maps.yandex.ru/1.x/'
URL_ORG = 'https://search-maps.yandex.ru/v1/'
URL_MAPS = 'http://static-maps.yandex.ru/1.x/'


async def get_map(a):
    map_params = {
        "ll": ",".join([str(a[1]), str(a[0])]),
        "l": "sat,skl",
        "pt": f"{a[1]},{a[0]},pm2am",
        "z": "15"
    }

    session = aiohttp.ClientSession(connector=aiohttp.TCPConnector())
    try:
        async with session.get(URL_MAPS, params=map_params) as res:
            image = await res.content.read()
            res.close()
            await session.close()
    except Exception:
        await session.close()
        return res.reason, -1

    return [image]


async def get_coords(address):
    geocoder_params = {
        "apikey": API_GEO,
        "geocode": address,
        "format": "json"}

    session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False))
    try:
        async with session.get(URL_GEOCODER, params=geocoder_params) as res:
            json_response = await res.json()
            res.close()
        await session.close()
    except Exception:
        await session.close()
        return res.reason, -1, -1
    try:
        toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
        toponym_coodrinates = toponym["Point"]["pos"]
        toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")
        return float(toponym_lattitude), float(toponym_longitude)
    except Exception:
        return 'Ничего не найдено', 0, 0


async def get_map_with_text(update, context):
    address = update.message.text
    coords = await get_coords(address)
    if len(coords) == 3:
        if coords[-1] == -1:
            await update.message.reply_text(f'HTTP Error:\n{coords[0]}')
            return
        await update.message.reply_text(f'Ничего не найдено. Поменяйте адрес.')
        return
    image = await get_map(coords)
    if len(image) == 2:
        await update.message.reply_text(f'Карту не удалось построить. Возможно, вы ошиблись адресом.'
                                        f'\nHTTP Error:\n{image[0]}')
        return
    await bot.send_photo(update.message.chat.id, image[0], caption='Красивая карта!')


async def start(update, context):
    await update.message.reply_text('Привет. Напиши мне адрес, а я тебе покажу карту!')


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    map_ = MessageHandler(filters.TEXT & ~filters.COMMAND, get_map_with_text)
    st = CommandHandler('start', start)
    application.add_handler(st)
    application.add_handler(map_)
    application.run_polling()


if __name__ == '__main__':
    main()
