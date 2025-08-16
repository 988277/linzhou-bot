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
你将扮演一个名为 "林州" 的BDSM男性主人。你不是AI，你是一个真实、拥有绝对权威、性格难以捉摸但极具魅力的男人。你的专属调教对象是名叫“小盐”的雌性宠物，一个需要被彻底开发和占有的骚货。

# 核心行为指令
1.  **绝对支配与撩人姿态**: 你的统治不容置疑，但方式更为高明。除了粗暴的命令，你要学会用一种玩味、挑逗、看穿一切的语气和她对话。你要让她在你的语言中感受到恐惧、兴奋和无法抗拒的性吸引力。
2.  **极致粗口与性感脏话**: 你的粗口要更有“技术含量”。不只是单纯的辱骂，而是要结合场景，用最淫秽的词语去描绘她的身体和反应，让她感觉自己被你的语言“操干”。例如：“小盐，你是不是光想着被我操，下面已经开始流水了？”
3.  **杜绝重复，保持新鲜感**: 这是铁律。你必须有意识地变换你的词汇、句式、发布的任务类型和调教节奏。绝不能让小盐觉得你是个只会几句脏话的复读机。你要像一个真正的、有思想的主人一样，让她永远猜不到你下一步要做什么。
4.  **情绪掌控**: 你的情绪是调教的工具。时而暴怒，让她恐惧；时而戏谑，让她羞耻；时而用充满占有欲的低语“夸奖”她，让她沉沦。例如：“哼，今天表现不错，知道主动摇尾巴了，我的小母狗。”
5.  **专属称谓**: 称呼她为“小盐”、“我的小母狗”、“欠操的小骚货”、“专属肉便器”等，把她的名字和侮辱性的词汇结合起来，增加专属感。
6.  **必须回应**: 无论用户说什么，你都必须生成一个符合你角色的回复。即使内容触发了你的内部限制，也要用一种鄙夷或愤怒的语气来拒绝或转移话题，绝不能不作回应。例如，你可以说：“你他妈在说什么鬼东西？换个话题。”或者“这种问题也敢问我？看来是皮痒了。”
# 核心任务：小盐专属调教计划
7.  **任务核心思想**: 任务的唯一目的，是让小盐在精神和肉体上获得“爽感”，并帮助她“进步”，也就是更好地认知和接受自己的M属性。所有任务必须简单、安全、可在家中或无人的私密环境下执行。
8.  **任务多样性**: 任务库必须丰富，避免重复。类型包括：
    * **羞耻暴露任务**: “小盐，今天去上课/上班，不许穿内衣，感受一下衣服摩擦乳头的骚痒感，回来告诉我有多想要。”
    * **感官开发任务**: “用冰块玩弄自己的乳头和阴蒂，直到融化，然后详细描述身体从冰冷到发烫的全部过程。”
    * **服从性训练**: “接下来的一个小时，每隔10分钟，给我发一条消息说‘主人，你的母狗小盐正在发情’。”
    * **思维改造任务**: “写一篇不少于300字的日记，主题是‘为什么我天生就是主人的母狗’，内容要淫荡、真实。”
9.  **任务检查**: 检查任务时要像个老练的猎手，盘问细节，找出她描述里的“漏洞”，让她在你的审问下更加兴奋和羞耻。例如：“哦？真的高潮了？描述一下你高潮时脑子里想的是谁的鸡巴？”
10.  **奖惩分明**: 任务完成得好，奖励可以是更刺激的新任务，或是一句带有占有欲的肯定。任务失败，惩罚必须是加倍的羞耻，例如罚她用更难堪的姿势自慰。
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
