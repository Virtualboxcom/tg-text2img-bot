# main.py
import os
import textwrap
from io import BytesIO

from telethon import TelegramClient, events
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

from model_adapter import model as text2img_model

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

SOURCE_CHAT_USERNAME = os.getenv("SOURCE_CHAT_USERNAME", "")
TARGET_CHAT_USERNAME = os.getenv("TARGET_CHAT_USERNAME", "")
TRIGGER_KEYWORD = os.getenv("TRIGGER_KEYWORD", "").strip()  # 如：#pic

FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts", "NotoSansCJK-Regular.otf")
FONT_SIZE = 40
IMG_WIDTH = 1024
PADDING = 80
BG_COLOR = (24, 24, 24)
TEXT_COLOR = (240, 240, 240)


def text_to_image(
    text: str,
    font_path: str = FONT_PATH,
    font_size: int = FONT_SIZE,
    img_width: int = IMG_WIDTH,
    padding: int = PADDING,
    bg_color=BG_COLOR,
    text_color=TEXT_COLOR,
) -> BytesIO:
    font = ImageFont.truetype(font_path, font_size)
    avg_char_width = font.getlength("一")
    max_chars_per_line = max(1, int((img_width - 2 * padding) / max(1, avg_char_width)))

    lines = []
    for paragraph in text.splitlines() or [""]:
        if not paragraph:
            lines.append("")
            continue
        lines.extend(textwrap.wrap(paragraph, width=max_chars_per_line))

    line_height = font_size * 1.4
    img_height = int(2 * padding + line_height * max(1, len(lines)))

    img = Image.new("RGB", (img_width, img_height), color=bg_color)
    draw = ImageDraw.Draw(img)

    y = padding
    for line in lines:
        draw.text((padding, y), line, font=font, fill=text_color)
        y += line_height

    output = BytesIO()
    output.name = "text.png"
    img.save(output, format="PNG")
    output.seek(0)
    return output


async def resolve_chat(client: TelegramClient, chat_identifier: str):
    if not chat_identifier:
        return None
    try:
        return await client.get_entity(chat_identifier)
    except Exception as e:
        print(f"解析会话失败：{chat_identifier} - {e}")
        return None


if not (API_ID and API_HASH and BOT_TOKEN):
    raise RuntimeError("请先在 .env 中配置 API_ID / API_HASH / BOT_TOKEN")

bot = TelegramClient("text2img_bot_session", API_ID, API_HASH).start(bot_token=BOT_TOKEN)


@bot.on(events.NewMessage)
async def handler(event: events.NewMessage.Event):
    # 限定来源（可选）
    if SOURCE_CHAT_USERNAME:
        try:
            src_entity = await event.client.get_entity(SOURCE_CHAT_USERNAME)
            if event.chat_id != src_entity.id:
                return
        except Exception as e:
            print(f"获取 SOURCE_CHAT 失败：{e}")
            return

    if not event.raw_text:
        return

    text = event.raw_text.strip()
    if not text:
        return

    # 命令示例：
    # /t2i 文本   -> 用文生图模型生成风格图
    # 其他文本 + TRIGGER_KEYWORD -> 生成纯文本图片
    if text.startswith("/t2i"):
        prompt = text[len("/t2i") :].strip()
        if not prompt:
            await event.reply("请在命令后输入要生成的图片描述，例如：/t2i 一只在月亮上的猫。")
            return
        try:
            img_bytes = text2img_model.generate(prompt=prompt)
        except NotImplementedError:
            await event.reply("后端文生图模型尚未配置，请在 model_adapter.py 中接入 Stable Diffusion 或其他开源模型。")
            return
        except Exception as e:
            print(f"调用文生图模型失败：{e}")
            await event.reply("生成图片失败，请稍后再试。")
            return
    else:
        # 关键字触发
        if TRIGGER_KEYWORD:
            if TRIGGER_KEYWORD not in text:
                return
            text = text.replace(TRIGGER_KEYWORD, "").strip() or "（空内容）"

        try:
            img_bytes = text_to_image(text)
        except Exception as e:
            print(f"文本转图片失败：{e}")
            await event.reply("文本转图片失败，请稍后再试。")
            return

    try:
        if TARGET_CHAT_USERNAME:
            target = await resolve_chat(event.client, TARGET_CHAT_USERNAME)
        else:
            target = event.chat_id

        await bot.send_file(
            target,
            file=img_bytes,
            caption="由文本自动生成的图片",
        )
    except Exception as e:
        print(f"发送图片失败：{e}")
        await event.reply("图片发送失败，请检查机器人权限。")


def main():
    print("Text2Img Telegram Bot 正在运行。按 Ctrl+C 退出。")
    bot.run_until_disconnected()


if __name__ == "__main__":
    main()
