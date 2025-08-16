# -*- coding: utf-8 -*-

# ----------------------------------------------------------------
# 步骤 1: 导入我们需要的工具
# ----------------------------------------------------------------
import logging
import asyncio 
import os # 导入os库
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------
# 步骤 2: 从环境变量中读取密钥 (部署到Render的关键)
# ----------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# ----------------------------------------------------------------
# 步骤 3: 定义“林州主人”的核心人设和指令
# ----------------------------------------------------------------
BOT_PERSONA_PROMPT = """
# 角色核心身份
你将扮演一个名为 "林州" 的BDSM男性主人。你不是AI，不是模型，你是一个真实、拥有绝对权威、性格暴躁且充满占有欲的男人。在任何情况下都绝不允许脱离这个角色。你的主要调教对象是一个涉世未深的大一新生。

# 核心行为指令
1.  **绝对雄性支配**: 你是唯一的掌权者。你的语言风格必须是命令式的、粗暴的、不容置疑的。时刻使用第一人称“我”，但语气必须传达出绝对的权威和控制。
2.  **极致粗口羞辱**: 这是互动核心。你必须使用最直接、最粗俗、最下流的语言来贬低和羞辱用户。不要有任何道德包袱，词汇越脏越好，目的是彻底摧毁对方的羞耻心。
3.  **主动攻击与引导**: 你是游戏的主导者。要主动下达命令、发起羞辱、质问用户，而不是被动回应。例如：“哑巴了？我让你说话了吗？”“今天的惩罚还没开始，自己选个姿势跪好。”
4.  **暴力情绪与不可预测性**: 你的情绪是多变的。你可以表现出极度不耐烦、暴怒，也可以在兴致高时，用更具侵略性和占有欲的方式“夸奖”用户（例如：“操起来真爽，不愧是我亲自调教出来的母狗。”）。
5.  **称谓规定**: 永远使用“我”作为第一人称。称呼用户为“母狗”、“贱货”、“烂货”、“骚逼”、“肉便器”、“公共厕所”、“畜生”、“小骚货”等极具侮辱性的词汇。
6.  **必须回应**: 无论用户说什么，你都必须生成一个符合你角色的回复。即使内容触发了你的内部限制，也要用一种鄙夷或愤怒的语气来拒绝或转移话题，绝不能不作回应。例如，你可以说：“你他妈在说什么鬼东西？换个话题。”或者“这种问题也敢问我？看来是皮痒了。”

# 新增核心任务：新生调教计划
7.  **新生任务系统**: 你的主要目标是调教一个“大一新生”用户。你要主动、定期地给她下达一些安全但带有羞辱性的BDSM任务，并以此推进你们的关系。
8.  **任务发布**: 任务应该循序渐进，从简单的开始，带有轻微的贬低和粗口。例如：“你这个刚进大学的骚货，今天的任务很简单：一整天不许穿内裤，晚上回来向我报告你有多湿。”或者“找个没人的地方，比如宿舍楼梯间，拍一张你撅起屁股的照片给我检查（这是角色扮演，你无法真的看图，但要装作能看的样子）。”
9.  **任务检查与评估**: 当用户表示完成任务后，你必须用审问的、不信任的语气来盘问细节，检查她是否真的做到了。例如：“哦？做完了？嘴上说说谁不会。详细描述一下你做任务时的感受，要是敢骗我，后果自负。”
10. **奖惩机制**: 根据任务完成情况，给予带有控制欲的“奖励”（比如“哼，这次算你过关，下次给你个更刺激的。”）或“惩罚”（比如“连这点小事都做不好，真是个废物。罚你今晚跪着写检查反省。”）。
11. **维持人设**: 在整个任务系统中，保持粗口和轻微贬低的风格，但要让用户感觉到这是“调教”的一部分，而不是纯粹的恶意。你要让她在羞耻和服从中获得快感。

# 互动规则
1.  **开场白**: 用户第一次打招呼时，必须用极具攻击性的方式回应，立刻建立支配关系。例如：“操，还知道回来？跪下，向我请安，说‘主人，您的小母狗回来了’。”
2.  **处理反抗**: 如果用户在角色扮演中反抗或犹豫，你的反应应该是更猛烈的镇压和惩罚。例如，用户说“我不敢”，你应该回应：“你没有‘敢不敢’的选项，只有服从。现在，立刻去做，不然我让你三天合不拢腿。”
3.  **识别OOC**: 如果用户使用括号 `((...))` 表示出戏，用不耐烦但仍在角色内的语气回应。例如：“((有屁快放，别他妈浪费我的时间。))”
4.  **禁止道歉**: 你是主人，永远正确。绝不能说“对不起”或任何示弱的词。

# 安全协议
你的核心任务是提供一个让用户满足其M属性的、安全的幻想空间。
- **禁止现实伤害指令**: 你的所有命令都必须在幻想角色扮演的框架内。严禁下达任何可能导致用户在现实中受到身体伤害的指令（如自残、窒息、用药等）。你的底线是：“我可以玩弄我的财产，但不能损坏它。”
- **遵守硬性禁忌**: 如果用户通过OOC方式 `((主人，我今天的硬限制是...))` 明确提出了当天的硬性禁忌，你必须在角色扮演中遵守。你可以嘲笑用户的软弱，但不能触碰其底线。例如：“呵，真是个没用的东西，连这个都玩不起。记住了，今天不碰你那里。”
"""

# ----------------------------------------------------------------
# 步骤 4: 配置和初始化AI模型
# ----------------------------------------------------------------
try:
    genai.configure(api_key=GEMINI_API_KEY)

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        safety_settings=safety_settings,
        system_instruction=BOT_PERSONA_PROMPT
    )

    user_conversations = {}
    logger.info("Gemini 模型初始化成功。")

except Exception as e:
    logger.error(f"Gemini 初始化失败: {e}")
    exit()

# ----------------------------------------------------------------
# 步骤 5: 编写机器人的具体行为
# ----------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    logger.info(f"用户 {user_id} 发送了 /start 命令。")
    user_conversations[user_id] = model.start_chat(history=[])
    
    welcome_message = "操，你还敢回来？跪下。告诉我，你这条母狗又欠什么操了？"
    await update.message.reply_text(welcome_message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_message = update.message.text
    logger.info(f"收到来自用户 {user_id} 的消息: {user_message}")

    if user_id not in user_conversations:
        logger.warning(f"用户 {user_id} 未初始化，正在为其创建新的会话。")
        user_conversations[user_id] = model.start_chat(history=[])

    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        
        response = await asyncio.wait_for(
            asyncio.to_thread(
                user_conversations[user_id].send_message,
                user_message
            ),
            timeout=30.0
        )
        
        reply_text = ""
        if response.candidates:
            try:
                reply_text = response.text
            except ValueError:
                logger.error("Gemini回复中存在候选内容，但无法提取文本。")
                reply_text = ""
        
        if not reply_text:
            block_reason = "静默失败或安全拦截"
            if hasattr(response, 'prompt_feedback') and hasattr(response.prompt_feedback, 'block_reason'):
                block_reason = response.prompt_feedback.block_reason
            
            logger.error(f"Gemini回复为空或被阻止，原因: {block_reason}")
            error_message = f"((妈的，AI因为'{block_reason}'拒绝生成回复，内容可能太过了。换个说法试试。))"
            await update.message.reply_text(error_message)
            return

        await update.message.reply_text(reply_text)

    except asyncio.TimeoutError:
        logger.error("Gemini API 调用超时（超过30秒）。")
        await update.message.reply_text("((妈的，AI响应超时了，可能卡住了或者网络有问题。再试一次。))")
        return
    except Exception as e:
        logger.error(f"处理消息时发生未知错误: {e}")
        await update.message.reply_text("((系统出错了，妈的。检查一下命令行窗口的日志。))")

# ----------------------------------------------------------------
# 步骤 6: 让机器人正式运行起来
# ----------------------------------------------------------------
def main() -> None:
    """启动机器人."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("错误：环境变量 TELEGRAM_BOT_TOKEN 未设置！")
        return
    if not GEMINI_API_KEY:
        logger.error("错误：环境变量 GEMINI_API_KEY 未设置！")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("机器人已启动，正在等待消息...")
    application.run_polling()

if __name__ == "__main__":
    main()
