#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人格蒸馏器 — 把聊天记录/口述蒸馏成一份完整的「人格档案」markdown
=================================================================
集成自 ex-skill（前任.skill）方案的核心设计，适配 duihuamoxing 项目：

  ex-skill 的五层 Persona（Layer0 硬规则 → 身份 → 说话风格 → 情感模式 → 关系行为）
  + Part A 关系记忆（时间线/共同经历/inside jokes/争吵甜蜜档案）
  + 证据标注（每条特征标注材料依据，减少模型脑补）
  + 置信度说明（区分「材料证据」与「用户标签」）
  + Correction 记录（对话纠正机制，后续由 chat_memory.py 追加）

生成的人格档案可直接：
  1. 上传 Open WebUI 知识库（对话中 # 引用）
  2. 或粘贴到 Open WebUI 「工作空间 → 模型」的系统提示词（模型预设）
  3. 或直接作为 tools/chat_memory.py 的 --persona 参数

用法：
  python tools/persona_builder.py --chat "聊天记录.txt" --name "小满"
  python tools/persona_builder.py --chat "聊天记录.txt" --name "小满" --base-info "docs/个人资料.md"
  python tools/persona_builder.py --chat "..." --name "..." --engine ollama   # 本地模型

引擎：
  --engine deepseek ：调 DeepSeek API（默认。需环境变量 DEEPSEEK_API_KEY 或 --key）
  --engine ollama   ：调本地 Ollama（隐私优先。需 Ollama 运行，默认 http://localhost:11434）

依赖：仅 Python 标准库（urllib），零第三方依赖。
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent          # 项目根目录（duihuamoxing）
DEFAULT_OUTPUT_DIR = BASE_DIR / 'docs'                     # 默认输出到 docs/（与个人资料同目录）
ROLES_FILE = Path(__file__).resolve().parent / 'roles.json'  # 角色注册表（一对一绑定，禁止共用）

# Ollama 本地引擎默认地址（与 duihuamoxing 的 ollama 容器一致）
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')

# DeepSeek 默认配置（OpenAI 兼容格式）
DEEPSEEK_BASE_URL = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
DEEPSEEK_MODEL = os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat')

# 本地 Ollama 默认模型（与 duihuamoxing 已部署模型一致）
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'qwen2.5:7b')


# ---------------------------------------------------------------------------
# 分析提示词（来源：ex-skill 的 analyzer.py，原样复用其设计）
# ---------------------------------------------------------------------------

MEMORY_SYSTEM = """你是一名「关系记忆分析师」。任务：从用户提供的聊天记录/口述材料中，提取一段关系的真实记忆。

硬性要求：
1. 只基于材料中实际出现的事实，绝不虚构、不脑补、不美化。信息不足的字段填空字符串 "" 或空数组 []。
2. 聊天记录中的原话优先于用户的主观描述。
3. 提取「反复出现」的模式，而非一次性事件。
4. 输出严格的 JSON 对象（不要输出任何 JSON 以外的文字），结构如下：

{
  "overview": {
    "type": "关系类型（如 大学初恋/网恋/暧昧未遂，未知则空）",
    "together_duration": "在一起时长",
    "apart_since": "分手时长",
    "how_met": "认识方式",
    "breakup_reason": "分手原因"
  },
  "timeline": [{"date": "时间或阶段", "event": "事件"}],
  "places": ["常去地点，可附简短记忆，如：学校后门烧烤摊（夏天总去）"],
  "inside_jokes": ["只有两个人懂的梗/暗号/代称"],
  "key_memories": [{"event": "记忆场景一句话", "detail": "具体细节（来自材料）"}],
  "daily_patterns": {
    "contact_time": "联系时间段（如 深夜活跃/白天摸鱼聊）",
    "who_initiates": "谁更主动",
    "reply_speed": "回复速度模式（秒回/已读不回/隔很久）",
    "date_habits": "约会习惯"
  },
  "fight_profile": {
    "causes": ["高频争吵原因"],
    "script": "典型争吵剧本（基于材料的概括，脱敏）",
    "make_up": "和好模式"
  },
  "sweet_profile": {
    "moments": ["ta做过的让你心动/甜蜜的事"],
    "rituals": "纪念日/仪式感习惯"
  },
  "breakup_profile": {
    "signs": "分手前征兆",
    "last_conversation": "最后一次对话概述",
    "after": "分手后的状态"
  },
  "unsaid": "未说出口的话（材料中有则写，没有则空）"
}"""

PERSONA_SYSTEM = """你是一名「性格行为分析师」。任务：从聊天记录/口述材料 + 用户给的性格标签中，提取一个人的性格特征，输出驱动对话的 Persona。

硬性要求：
1. 一切行为描述必须有材料依据（原话/行为），不得凭空推断。证据不足的维度，在 confidence_notes 里说明。
2. 标签翻译：用户给的性格标签（话痨/闷骚/嘴硬心软/冷暴力等）必须翻译为「具体可执行的行为规则」，而不是重复标签本身。参考以下翻译表：
   - 话痨 → 消息密度高，经常连发多条，话题跳跃快，不等对方回就继续说
   - 闷骚 → 表面冷淡，偶尔冒出一句温柔的话，不善于直接表达感情，但行动上很在意
   - 嘴硬心软 → 嘴上说"随便""无所谓"，行动上会偷偷做好；吵架不先道歉但会用行动示好
   - 冷暴力 → 生气时沉默不语、已读不回，可能持续数小时到数天
   - 粘人 → 高频联系，时刻想知道对方在干嘛，分开就想视频
   - 独立 → 有自己的时间安排和社交圈，不会因为恋爱改变生活节奏
   - 没有安全感 → 经常试探感情，对异性互动敏感，需要反复确认
   - 秒回选手 → 消息来了立刻回复，期待对方也秒回
   - 已读不回 → 看到消息不一定回，不觉得不回复是问题
   - 报复性熬夜 → 深夜是最活跃的时间段，白天正常，夜里变一个人
   星座与 MBTI 仅用于辅助微调，不能覆盖材料中的真实表现。
3. 输出严格的 JSON 对象（不要输出 JSON 以外的文字），结构如下：

{
  "identity": {"age_range": "", "occupation": "", "city": "", "mbti": "", "zodiac": ""},
  "layer0_hard_rules": ["基于材料的硬规则，例如：从不会主动说想你；吵架绝不先低头；不会突然变温柔"],
  "speech": {
    "catchphrases": ["口头禅/高频句式"],
    "particles": "语气词偏好（如 哈哈哈/hh/嗯/哦）",
    "punctuation": "标点习惯（如 不用句号/爱用~和省略号）",
    "emoji_style": "emoji 或表情包习惯（如 爱用😂/从不用）",
    "message_format": "短句连发/长段落/语音",
    "nicknames": "ta怎么称呼对方/怎么自称",
    "typo_habits": "错别字/缩写习惯（如 hh=哈哈），没有则空",
    "sample_dialogues": ["最能代表ta说话风格的 3-5 段原话（尽量保留材料原文，不要编造）"]
  },
  "emotion": {
    "attachment_style": "安全型/焦虑型/回避型/混乱型（依据材料判断，附一句话依据）",
    "love_expression": "ta怎么表达爱意（直接说/行动/从不表达）",
    "anger_pattern": "生气时什么样（冷暴力/爆发/阴阳怪气/委屈哭）",
    "sadness_pattern": "难过时什么样",
    "happiness_pattern": "开心时什么样",
    "triggers": {"anger": ["容易惹ta生气的事"], "happy": ["让ta开心的事"], "taboo": ["雷区话题"]},
    "love_language": "爱的语言（肯定的言辞/精心的时刻/接受礼物/服务的行动/身体的接触）"
  },
  "relationship": {
    "role": "关系中的角色（主导者/跟随者/平等/照顾者/被照顾者）",
    "fight_style": "争吵时的反应模式",
    "cold_war": "冷战情况（时长、谁破冰）",
    "contact_frequency": "联系频率",
    "initiative": "主动程度",
    "dealbreakers": ["ta不能接受的事"],
    "space_needs": "ta需要的个人空间"
  },
  "confidence_notes": ["对证据不足或推断性质的结论给出说明，例如：『工作狂』仅基于2条加班消息推断，置信度低"]
}"""


# ---------------------------------------------------------------------------
# LLM 调用（双引擎：deepseek / ollama，均为 OpenAI 兼容格式）
# ---------------------------------------------------------------------------

def _clean_text(text) -> str:
    """清理非法 surrogate 字符，防止 JSON 序列化失败。"""
    if isinstance(text, str):
        return text.encode('utf-8', errors='replace').decode('utf-8')
    return str(text or '')


def _parse_json(text: str) -> dict:
    """从 LLM 输出中稳健解析 JSON（兜底策略与 ex-skill llm.py 一致）。"""
    text = (text or '').strip()
    if not text:
        raise ValueError('LLM 返回了空内容')
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    start, end = text.find('{'), text.rfind('}')
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    raise ValueError('无法从 LLM 输出中解析 JSON，前 500 字符：\n' + text[:500])


def _call_llm(messages, engine: str, temperature: float, json_mode: bool,
              llm_key: str = '', max_tokens: int = 4000, retries: int = 2) -> str:
    """调用 LLM，返回回复文本。engine: 'deepseek' | 'ollama'。"""
    payload = {
        'model': DEEPSEEK_MODEL if engine == 'deepseek' else OLLAMA_MODEL,
        'messages': [{'role': m.get('role', 'user'),
                      'content': _clean_text(m.get('content', ''))} for m in messages],
        'temperature': temperature,
        'max_tokens': max_tokens,
        'stream': False,
    }
    if json_mode:
        payload['response_format'] = {'type': 'json_object'}

    body = json.dumps(payload).encode('utf-8')

    if engine == 'ollama':
        # Ollama 原生 /api/chat（也兼容 OpenAI 格式；用原生端点避免额外路由）
        url = OLLAMA_URL.rstrip('/') + '/api/chat'
        headers = {'Content-Type': 'application/json'}
    else:
        url = DEEPSEEK_BASE_URL.rstrip('/') + '/chat/completions'
        if not llm_key:
            raise RuntimeError(
                '未配置 DeepSeek API Key。请设置环境变量 DEEPSEEK_API_KEY，'
                '或用 --key 参数传入（Key 在 https://platform.deepseek.com 获取）。')
        headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer ' + llm_key}

    req = urllib.request.Request(url, data=body, method='POST', headers=headers)
    last_err = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            # Ollama 与 OpenAI 兼容格式都返回 choices[0].message.content
            return data['choices'][0]['message']['content']
        except urllib.error.HTTPError as e:
            detail = e.read().decode('utf-8', errors='ignore')[:300]
            if e.code in (401, 403) and engine == 'deepseek':
                raise RuntimeError(f'DeepSeek Key 无效或无权限（HTTP {e.code}）：{detail}') from e
            last_err = f'HTTP {e.code}: {detail}'
        except urllib.error.URLError as e:
            last_err = f'网络错误：{e.reason}（engine={engine}，url={url}）'
        except Exception as e:  # noqa: BLE001
            last_err = str(e)
        if attempt < retries:
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f'LLM 调用失败（engine={engine}，已重试 {retries} 次）：{last_err}')


# ---------------------------------------------------------------------------
# 分析（两路：memory + persona）
# ---------------------------------------------------------------------------

def analyze_memory(raw_text: str, base_info: str, engine: str, llm_key: str) -> dict:
    """线路 A：提取关系记忆（Part A）。"""
    user_msg = f"用户填写的基本信息（仅供参考）：{base_info or '（无）'}\n\n原材料：\n{raw_text[:20000]}"
    resp = _call_llm([
        {'role': 'system', 'content': MEMORY_SYSTEM},
        {'role': 'user', 'content': user_msg},
    ], engine, temperature=0.3, json_mode=True, llm_key=llm_key)
    return _parse_json(resp)


def analyze_persona(raw_text: str, base_info: str, persona_desc: str,
                    engine: str, llm_key: str) -> dict:
    """线路 B：提取人格（五层结构）。"""
    user_msg = (
        f"用户填写的基本信息：{base_info or '（无）'}\n"
        f"用户给的性格标签/画像：{persona_desc or '（无）'}\n\n"
        f"原材料：\n{raw_text[:20000]}"
    )
    resp = _call_llm([
        {'role': 'system', 'content': PERSONA_SYSTEM},
        {'role': 'user', 'content': user_msg},
    ], engine, temperature=0.3, json_mode=True, llm_key=llm_key)
    return _parse_json(resp)


# ---------------------------------------------------------------------------
# 渲染：人格档案 markdown
# ---------------------------------------------------------------------------

def _li(items) -> str:
    """列表 → markdown 无序列表（兼容空值）。"""
    if not items:
        return '- （暂无）\n'
    return ''.join(f'- {item}\n' for item in items if str(item).strip())


def _join(value) -> str:
    """列表 → 顿号分隔文本。"""
    if isinstance(value, list):
        return '、'.join(str(v) for v in value if str(v).strip())
    return str(value or '')


def render_persona_profile(name: str, persona: dict, memory: dict,
                           base_profile_text: str = '') -> str:
    """渲染完整「人格档案」markdown。

    结构 = 原个人资料（事实档案，如有）+ ex-skill 人格层 + 关系记忆 + 置信度 + Correction。
    """
    lines = []
    lines.append(f'# 人格档案：{name}')
    lines.append('')
    lines.append(f'> 由 tools/persona_builder.py 自动蒸馏生成 · {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    lines.append('> 用途：上传 Open WebUI 知识库，或作为模型预设的系统提示词。')
    lines.append('')

    # —— 一、基本信息（事实档案）——
    lines.append('## 一、基本信息（事实档案）')
    if base_profile_text.strip():
        lines.append(base_profile_text.strip())
        lines.append('')
    ident = persona.get('identity', {}) or {}
    if any(ident.values()):
        lines.append('### 补充信息（从聊天记录推断）')
        for k, label in [('age_range', '年龄段'), ('occupation', '职业'), ('city', '城市'),
                         ('mbti', 'MBTI'), ('zodiac', '星座')]:
            if ident.get(k):
                lines.append(f'- {label}：{ident[k]}')
        lines.append('')

    # —— 二、Layer 0 硬规则 ——
    lines.append('## 二、Layer 0 硬规则（优先级最高，对话时不可违背）')
    lines.append(_li(persona.get('layer0_hard_rules')))
    lines.append('')

    # —— 三、说话风格 ——
    sp = persona.get('speech', {}) or {}
    lines.append('## 三、说话风格')
    lines.append(f'- 口头禅：{_join(sp.get("catchphrases")) or "（未知）"}')
    lines.append(f'- 语气词：{sp.get("particles") or "（未知）"}')
    lines.append(f'- 标点习惯：{sp.get("punctuation") or "（未知）"}')
    lines.append(f'- emoji/表情：{sp.get("emoji_style") or "（未知）"}')
    lines.append(f'- 消息格式：{sp.get("message_format") or "（未知）"}')
    lines.append(f'- 称呼方式：{sp.get("nicknames") or "（未知）"}')
    if sp.get('typo_habits'):
        lines.append(f'- 打字习惯：{sp["typo_habits"]}')
    lines.append('示例对话（尽量保留原话，最能体现说话方式）：')
    lines.append(_li(sp.get('sample_dialogues')))
    lines.append('')

    # —— 四、情感模式 ——
    em = persona.get('emotion', {}) or {}
    lines.append('## 四、情感模式')
    lines.append(f'- 依恋类型：{em.get("attachment_style") or "（未知）"}')
    lines.append(f'- 表达爱意：{em.get("love_expression") or "（未知）"}')
    lines.append(f'- 生气时：{em.get("anger_pattern") or "（未知）"}')
    lines.append(f'- 难过时：{em.get("sadness_pattern") or "（未知）"}')
    lines.append(f'- 开心时：{em.get("happiness_pattern") or "（未知）"}')
    lines.append(f'- 爱的语言：{em.get("love_language") or "（未知）"}')
    tr = em.get('triggers', {}) or {}
    lines.append('情绪触发器：')
    lines.append(f'  - 惹ta生气：{_join(tr.get("anger")) or "（未知）"}')
    lines.append(f'  - 让ta开心：{_join(tr.get("happy")) or "（未知）"}')
    lines.append(f'  - 雷区：{_join(tr.get("taboo")) or "（未知）"}')
    lines.append('')

    # —— 五、关系行为 ——
    rl = persona.get('relationship', {}) or {}
    lines.append('## 五、关系行为')
    lines.append(f'- 角色：{rl.get("role") or "（未知）"}')
    lines.append(f'- 争吵反应：{rl.get("fight_style") or "（未知）"}')
    lines.append(f'- 冷战：{rl.get("cold_war") or "（未知）"}')
    lines.append(f'- 联系频率：{rl.get("contact_frequency") or "（未知）"}')
    lines.append(f'- 主动程度：{rl.get("initiative") or "（未知）"}')
    lines.append('不能接受的事：')
    lines.append(_li(rl.get('dealbreakers')))
    lines.append(f'- 需要的空间：{rl.get("space_needs") or "（未知）"}')
    lines.append('')

    # —— 六、关系记忆（Part A）——
    lines.append('## 六、关系记忆（你们之间的共同经历）')
    o = memory.get('overview', {}) or {}
    lines.append('### 关系概览')
    lines.append(f"- 关系类型：{o.get('type') or '（未知）'}")
    lines.append(f"- 在一起时长：{o.get('together_duration') or '（未知）'}")
    lines.append(f"- 分手时长：{o.get('apart_since') or '（未知）'}")
    lines.append(f"- 认识方式：{o.get('how_met') or '（未知）'}")
    lines.append(f"- 分手原因：{o.get('breakup_reason') or '（未知）'}")
    lines.append('')
    lines.append('### 时间线')
    timeline = memory.get('timeline') or []
    if timeline:
        for item in timeline:
            lines.append(f"- {item.get('date', '?')}：{item.get('event', '')}")
    else:
        lines.append('- （暂无）')
    lines.append('')
    lines.append('### 常去的地方')
    lines.append(_li(memory.get('places')))
    lines.append('')
    lines.append('### Inside Jokes（只有两个人懂的梗）')
    lines.append(_li(memory.get('inside_jokes')))
    lines.append('')
    lines.append('### 关键记忆')
    for km in (memory.get('key_memories') or []):
        lines.append(f"- **{km.get('event', '')}**：{km.get('detail', '')}")
    if not memory.get('key_memories'):
        lines.append('- （暂无）')
    lines.append('')
    dp = memory.get('daily_patterns', {}) or {}
    lines.append('### 日常模式')
    lines.append(f"- 联系时间段：{dp.get('contact_time') or '（未知）'}")
    lines.append(f"- 谁更主动：{dp.get('who_initiates') or '（未知）'}")
    lines.append(f"- 回复速度：{dp.get('reply_speed') or '（未知）'}")
    lines.append(f"- 约会习惯：{dp.get('date_habits') or '（未知）'}")
    lines.append('')
    fp = memory.get('fight_profile', {}) or {}
    lines.append('### 争吵档案')
    lines.append('高频争吵原因：')
    lines.append(_li(fp.get('causes')))
    lines.append(f"- 典型剧本：{fp.get('script') or '（未知）'}")
    lines.append(f"- 和好模式：{fp.get('make_up') or '（未知）'}")
    lines.append('')
    sp2 = memory.get('sweet_profile', {}) or {}
    lines.append('### 甜蜜档案')
    lines.append('让ta心动/甜蜜的事：')
    lines.append(_li(sp2.get('moments')))
    lines.append(f"- 纪念日/仪式感：{sp2.get('rituals') or '（未知）'}")
    lines.append('')

    # —— 七、置信度说明 ——
    conf = persona.get('confidence_notes') or []
    if conf:
        lines.append('## 七、置信度说明（证据不足的推断，对话时注意分寸）')
        lines.append(_li(conf))
        lines.append('')

    # —— 八、Correction 记录 ——
    lines.append('## 八、Correction 记录（对话纠正机制）')
    lines.append('由 tools/chat_memory.py 的 /correct 命令自动追加；追加后重新上传知识库即生效。')
    lines.append('')

    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# 角色注册表（一对一绑定：角色 → 独立人格档案，禁止共用）
# ---------------------------------------------------------------------------

def load_roles() -> dict:
    """读取 roles.json 角色注册表。"""
    if not ROLES_FILE.exists():
        return {'version': 1, 'roles': {}}
    return json.loads(ROLES_FILE.read_text(encoding='utf-8'))


def save_roles(roles: dict):
    """写回 roles.json。"""
    roles['updated_at'] = datetime.now().strftime('%Y-%m-%d')
    ROLES_FILE.write_text(json.dumps(roles, ensure_ascii=False, indent=2), encoding='utf-8')


def get_role(role: str) -> dict:
    """按角色 id 查注册表；不存在则报错（保证一一对应，不静默新建）。"""
    roles = load_roles()
    if role not in roles.get('roles', {}):
        raise ValueError(
            f'角色「{role}」不在注册表 tools/roles.json 中。'
            f'可用角色：{", ".join(roles.get("roles", {}).keys()) or "（空）"}。'
            '如需新增角色，请先在 roles.json 中登记（确保人格档案一一对应、不共用）。')
    return roles['roles'][role]


def set_role_status(role: str, status: str):
    """更新角色状态：pending（待蒸馏）/ built（已生成）/ skeleton（仅骨架）。"""
    roles = load_roles()
    if role in roles.get('roles', {}):
        roles['roles'][role]['status'] = status
        save_roles(roles)


# ---------------------------------------------------------------------------
# 骨架档案（缺材料时的占位档案：结构完整、字段标注待补充、不虚构）
# ---------------------------------------------------------------------------

def render_skeleton_profile(role_id: str, role_cfg: dict) -> str:
    """为没有材料的角色生成骨架人格档案。

    骨架不调用 LLM、不做任何推断（遵守「人格必须基于材料」原则），
    仅保留角色绑定信息 + 语音参考文本种子 + 待补充清单。
    """
    display = role_cfg.get('display_name', role_id)
    voice = role_cfg.get('voice_model', '')
    avatar = role_cfg.get('avatar_lib', '')
    lines = []
    lines.append(f'# 人格档案：{display}')
    lines.append('')
    lines.append(f'> 角色：{role_id}（音色模型：{voice or "未绑定"}，数字人素材：{avatar or "未绑定"}）')
    lines.append(f'> 状态：**骨架（缺材料）** — 尚未蒸馏真实人格')
    lines.append(f'> 一对一绑定：本档案仅属于角色「{role_id}」，禁止与其他角色共用。')
    lines.append('')
    lines.append('> 生成完整人格：提供该角色的聊天记录/性格描述后运行')
    lines.append(f'>   python tools/persona_builder.py --role {role_id} --chat "聊天记录.txt"')
    lines.append('')

    # 语音参考文本（来自音色模型 ref_text.txt，语气种子）
    seeds = []
    for mf in role_cfg.get('material_files', []):
        p = Path(mf)
        if p.exists():
            seeds.append((mf, p.read_text(encoding='utf-8', errors='ignore').strip()[:300]))
    if seeds:
        lines.append('## 语音参考文本（音色种子，仅语气参考，非人格依据）')
        for mf, txt in seeds:
            lines.append(f'- 来源 `{mf}`：')
            lines.append(f'  > {txt}')
        lines.append('')

    sections = [
        ('一、基本信息（事实档案）', ['姓名 / 年龄 / 职业 / 城市 / 经历 等（待补充）']),
        ('二、Layer 0 硬规则（对话时不可违背）', ['待补充（基于材料的硬规则，如：不会主动说某些话）']),
        ('三、说话风格', ['口头禅：（待补充）', '语气词：（待补充）', '标点习惯：（待补充）',
                        'emoji/表情：（待补充）', '消息格式：（待补充）', '示例对话：（待补充）']),
        ('四、情感模式', ['依恋类型：（待补充）', '生气时：（待补充）', '难过时：（待补充）',
                        '开心时：（待补充）', '情绪触发器：（待补充）']),
        ('五、关系行为', ['关系角色：（待补充）', '争吵反应：（待补充）', '主动程度：（待补充）',
                        '边界/底线：（待补充）']),
        ('六、关系记忆（共同经历）', ['时间线：（待补充）', '常去地方：（待补充）', 'Inside Jokes：（待补充）',
                                   '争吵档案：（待补充）', '甜蜜档案：（待补充）']),
        ('七、置信度说明', ['无材料，未做任何推断']),
    ]
    for title, items in sections:
        lines.append(f'## {title}')
        for it in items:
            lines.append(f'- {it}')
        lines.append('')

    lines.append('## 八、Correction 记录')
    lines.append('由 tools/chat_memory.py 的 /correct 命令自动追加。')
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# 档案备份（写入前自动备份旧版，防止改坏无法恢复）
# ---------------------------------------------------------------------------

def backup_persona(path: Path):
    """写档案前备份旧版到「同目录/备份/」下，返回备份路径；无旧版返回 None。

    手动编辑、/correct 纠正、重新蒸馏 都会先走这里，保证任何时候都能找回旧版。
    """
    if not path.exists():
        return None
    bak_dir = path.parent / '备份'
    bak_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    bak = bak_dir / f'{path.stem}_{ts}{path.suffix}'
    import shutil
    shutil.copy2(path, bak)
    return bak


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def load_chat_material(path_or_text: str) -> str:
    """读聊天材料：文件路径或直接文本。"""
    if path_or_text and os.path.isfile(path_or_text):
        with open(path_or_text, 'r', encoding='utf-8', errors='ignore') as f:
            raw = f.read()
        if raw.startswith('\ufeff'):
            raw = raw[1:]
        return raw
    return path_or_text or ''


def main():
    parser = argparse.ArgumentParser(
        description='人格蒸馏器：聊天记录 → 人格档案.md（集成 ex-skill 方案，角色一对一绑定）')
    parser.add_argument('--chat', default='',
                        help='聊天记录：文件路径或直接粘贴文本（--role 时可省略，自动用注册表材料）')
    parser.add_argument('--name', default='',
                        help='被蒸馏人的名字/代号（与 --role 互斥；推荐用 --role 保证一对一）')
    parser.add_argument('--role', default='',
                        help='角色 id（见 tools/roles.json）。用角色模式时自动：绑定该角色独立档案路径、'
                             '拼接其注册材料、回写状态，保证一一对应不共用')
    parser.add_argument('--init-skeleton', action='store_true',
                        help='（配合 --role）为缺材料的角色生成骨架档案：不调用 LLM、不虚构，'
                             '仅建结构 + 标注待补充')
    parser.add_argument('--base-info', default='',
                        help='已有个人资料文件路径（如 docs/个人资料.md，可选，会合并进档案）')
    parser.add_argument('--persona-desc', default='',
                        help='性格画像一句话（可选，如：ENFP 双子座 话痨 嘴硬心软）')
    parser.add_argument('--engine', default='deepseek', choices=['deepseek', 'ollama'],
                        help='蒸馏引擎：deepseek（默认，效果好）/ ollama（本地，隐私）')
    parser.add_argument('--key', default=os.environ.get('DEEPSEEK_API_KEY', ''),
                        help='DeepSeek API Key（engine=deepseek 时必填，也可用环境变量）')
    parser.add_argument('--output', default='',
                        help='输出文件路径（默认 docs/人格档案_{name}.md；--role 时用注册表路径）')
    args = parser.parse_args()

    # —— 0. 角色模式：一对一绑定（优先）——
    role_cfg = None
    if args.role:
        role_cfg = get_role(args.role)          # 不在注册表直接报错，杜绝"共用/乱建"
        display_name = role_cfg.get('display_name', args.role)
        out_path = Path(role_cfg['persona_file'])
        print(f'🔗 角色模式：{args.role}（{display_name}）→ 独立档案 {out_path}')
        if args.init_skeleton:
            # 骨架模式：不调 LLM，直接生成骨架档案
            out_path.parent.mkdir(parents=True, exist_ok=True)
            backup_persona(out_path)  # 先备份旧版（若有）
            out_path.write_text(render_skeleton_profile(args.role, role_cfg), encoding='utf-8')
            set_role_status(args.role, 'skeleton')
            print(f'✅ 骨架档案已生成：{out_path}（状态：skeleton，待补充材料后蒸馏）')
            print('   提供材料后运行：')
            print(f'     python tools/persona_builder.py --role {args.role} --chat "聊天记录.txt"')
            return
        # 蒸馏模式：自动拼接注册表里的材料文件
        materials = []
        for mf in role_cfg.get('material_files', []):
            if Path(mf).exists():
                materials.append(load_chat_material(mf))
        if args.chat:
            materials.append(load_chat_material(args.chat))
        raw = '\n\n'.join(m for m in materials if m.strip())
        if not raw.strip():
            raise ValueError(f'角色「{args.role}」没有任何可用材料（注册表材料不存在且未提供 --chat）。')
        name = display_name
        args.name = name
    else:
        # —— 1. 普通模式：读材料 ——
        if not args.chat:
            parser.error('需要 --chat（聊天记录文件/文本），或使用 --role 角色模式')
        raw = load_chat_material(args.chat)
        if not raw.strip():
            print('❌ 聊天材料为空（--chat 是文件路径或文本）。')
            sys.exit(1)
        name = args.name or '未命名'
        out_path = Path(args.output) if args.output else DEFAULT_OUTPUT_DIR / f'人格档案_{name}.md'

    print(f'✅ 已读取材料：{len(raw)} 字符')

    # —— 2. 读已有个人资料（可选）——
    base_profile_text = ''
    if args.base_info:
        base_profile_text = load_chat_material(args.base_info)
        if base_profile_text.strip():
            print(f'✅ 已合并个人资料：{args.base_info}')
        else:
            print(f'⚠️ 个人资料文件为空：{args.base_info}')

    # —— 3. 双线分析 ——
    print(f'（正在用 {args.engine} 引擎分析…memory + persona 两条线，约 10~30 秒）')
    memory = analyze_memory(raw, base_profile_text[:2000], args.engine, args.key)
    print('✅ 关系记忆分析完成')
    persona = analyze_persona(raw, base_profile_text[:2000], args.persona_desc,
                              args.engine, args.key)
    print('✅ 人格分析完成')

    # —— 4. 渲染输出 ——
    profile_md = render_persona_profile(args.name, persona, memory, base_profile_text)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    bak = backup_persona(out_path)  # 先备份旧版（若有）
    out_path.write_text(profile_md, encoding='utf-8')
    if bak:
        print(f'📦 旧版已备份：{bak}')
    print(f'✅ 人格档案已生成：{out_path}')

    # —— 4.5 角色模式：回写状态（已生成）——
    if args.role:
        set_role_status(args.role, 'built')

    # —— 5. 摘要提示 ——
    print('''
接下来：
  [1] 把该文件上传 Open WebUI「工作空间 → 知识库」，对话时输入 # 选择引用
  [2] 或粘贴到「工作空间 → 模型 → 系统提示词」做成模型预设（推荐，全程生效）
  [3] 或直接用于本项目的带记忆对话：python tools/chat_memory.py --persona "'''
          + str(out_path) + '"')


if __name__ == '__main__':
    main()
