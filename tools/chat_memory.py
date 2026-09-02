#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
带记忆的对话工具 — 演示并落地 ex-skill 的「记忆不中断」机制
=============================================================
解决你项目里的两个痛点：
  1. 上下文截断导致"聊久了忘记前面" → 会话内自动维护多轮历史（按轮数截断 + 摘要压缩）
  2. 新对话丢失记忆 → 每次会话结束自动生成摘要存档，下次会话自动加载最近 N 条

ex-skill 的机制对应关系：
  - system prompt = 人格档案.md（persona_builder.py 生成）
  - session summary = 每次对话结束生成摘要（原方案 session_summary.md）
  - Correction = /correct 命令，立即生效并写回人格档案

用法：
  python tools/chat_memory.py --persona "docs/人格档案_小满.md" --name 小满
  python tools/chat_memory.py --persona "docs/人格档案_小满.md" --name 小满 --engine deepseek

对话内命令：
  /exit   退出（自动生成摘要存档）
  /reset  清空本轮历史
  /summary 手动存档摘要
  /correct xxx  纠正人格（"ta不会说晚安，只会说睡了"）→ 写回档案 + 本次生效

依赖：仅 Python 标准库。
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'qwen2.5:7b')
DEEPSEEK_BASE_URL = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
DEEPSEEK_MODEL = os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat')

MAX_ROUNDS = 20            # 会话内保留最近多少轮（防上下文超限）
MAX_SUMMARIES_LOAD = 3     # 跨会话加载最近多少条摘要
SESSIONS_DIR = BASE_DIR / 'sessions'


# ---------------------------------------------------------------------------
# LLM 调用（与 persona_builder.py 相同的双引擎实现）
# ---------------------------------------------------------------------------

def _clean_text(text) -> str:
    if isinstance(text, str):
        return text.encode('utf-8', errors='replace').decode('utf-8')
    return str(text or '')


def _call_llm(messages, engine: str, temperature: float, llm_key: str,
              max_tokens: int = 800, retries: int = 2) -> str:
    payload = {
        'model': DEEPSEEK_MODEL if engine == 'deepseek' else OLLAMA_MODEL,
        'messages': [{'role': m.get('role', 'user'),
                      'content': _clean_text(m.get('content', ''))} for m in messages],
        'temperature': temperature,
        'max_tokens': max_tokens,
        'stream': False,
    }
    body = json.dumps(payload).encode('utf-8')

    if engine == 'ollama':
        url = OLLAMA_URL.rstrip('/') + '/api/chat'
        headers = {'Content-Type': 'application/json'}
    else:
        url = DEEPSEEK_BASE_URL.rstrip('/') + '/chat/completions'
        if not llm_key:
            raise RuntimeError('未配置 DeepSeek API Key（--key 或环境变量 DEEPSEEK_API_KEY）')
        headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer ' + llm_key}

    req = urllib.request.Request(url, data=body, method='POST', headers=headers)
    last_err = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            return data['choices'][0]['message']['content']
        except urllib.error.HTTPError as e:
            detail = e.read().decode('utf-8', errors='ignore')[:200]
            last_err = f'HTTP {e.code}: {detail}'
        except urllib.error.URLError as e:
            last_err = f'网络错误：{e.reason}（engine={engine}）'
        except Exception as e:  # noqa: BLE001
            last_err = str(e)
        if attempt < retries:
            import time
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f'LLM 调用失败（engine={engine}）：{last_err}')


# ---------------------------------------------------------------------------
# 跨会话记忆（session summary）
# ---------------------------------------------------------------------------

def _session_dir(name: str) -> Path:
    d = SESSIONS_DIR / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_recent_summaries(name: str):
    """读取最近 MAX_SUMMARIES_LOAD 条会话摘要，注入 system prompt。

    返回 (摘要文本, 实际条数)。
    """
    d = _session_dir(name)
    files = sorted(d.glob('*.md'))[-MAX_SUMMARIES_LOAD:]
    parts = []
    for f in files:
        content = f.read_text(encoding='utf-8').strip()[:1200]
        if content:
            parts.append(content)
    return '\n\n'.join(parts), len(files)


def save_summary(name: str, summary: str) -> Path:
    """保存本次会话摘要。"""
    fname = datetime.now().strftime('%Y%m%d_%H%M%S') + '.md'
    path = _session_dir(name) / fname
    path.write_text(summary, encoding='utf-8')
    return path


def summarize(name: str, transcript: list, engine: str, llm_key: str) -> str:
    """调用 LLM 生成会话摘要（ex-skill session_summary 机制）。"""
    text = '\n'.join(
        f"{'用户' if m['role'] == 'user' else name}：{m['content']}"
        for m in transcript[-30:])
    sys_prompt = ('你是对话摘要生成器。阅读对话，生成 markdown 格式的 Session Summary：'
                  '## 聊了什么 / ## 情绪基调 / ## 关键记忆点 / ## 下次可以接着聊。'
                  '不要加入对话中不存在的信息。')
    return _call_llm([
        {'role': 'system', 'content': sys_prompt},
        {'role': 'user', 'content': f'人物：{name}\n对话：\n{text}'},
    ], engine, temperature=0.3, llm_key=llm_key, max_tokens=500).strip()


# ---------------------------------------------------------------------------
# 纠正机制（correction）
# ---------------------------------------------------------------------------

def append_correction(persona_path: Path, correction: str):
    """把纠正记录写回人格档案.md 的 Correction 节（下次上传知识库生效）。

    写回前自动备份旧版到「同目录/备份/」，防止改坏无法恢复。
    """
    if not persona_path.exists():
        return
    import shutil
    bak_dir = persona_path.parent / '备份'
    bak_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy2(persona_path, bak_dir / f'{persona_path.stem}_{ts}{persona_path.suffix}')
    content = persona_path.read_text(encoding='utf-8')
    stamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    n = content.count('### Correction #') + 1
    entry = (f'\n### Correction #{n} — {stamp}\n'
             f'- 用户原话："{correction}"\n'
             f'- 生效说明：本会话立即生效；写回档案后请重新上传 Open WebUI 知识库。\n')
    if '## 八、Correction 记录' in content:
        content = content.replace('## 八、Correction 记录',
                                  '## 八、Correction 记录\n' + entry, 1)
    else:
        content += '\n## 八、Correction 记录\n' + entry
    persona_path.write_text(content, encoding='utf-8')
    return n


# ---------------------------------------------------------------------------
# 主对话循环
# ---------------------------------------------------------------------------

def build_system_prompt(persona_text: str, name: str, summaries: str,
                        corrections: list) -> str:
    """组装 system prompt：人格档案 + 历史摘要 + 纠正 + 角色指令。"""
    parts = [
        f'你是{name}，不是 AI 助手。以下是你的完整人格档案（必须严格遵守）：\n\n{persona_text}',
    ]
    if summaries:
        parts.append(
            f'以下是你们最近几次对话的摘要，请自然地延续关系状态，不要主动提起「上次我们聊了」：\n\n{summaries}')
    if corrections:
        parts.append('用户对你的纠正（优先级高于人格档案中的对应描述）：\n' +
                     '\n'.join(f'- {c}' for c in corrections))
    parts.append(
        f'\n请始终用{name}的方式回复：保持口头禅、语气、标点习惯和态度。'
        '回答要短，像真人聊天，不要列点，不要解释你在扮演。')
    return '\n\n'.join(parts)


def chat_loop(persona_path: Path, name: str, engine: str, llm_key: str):
    persona_text = persona_path.read_text(encoding='utf-8')

    # 跨会话记忆：加载最近摘要
    summaries, n_summaries = load_recent_summaries(name)
    if n_summaries > 0:
        print(f'（已加载 {n_summaries} 条历史会话摘要，记忆延续中）')

    # 本次会话的纠正（临时生效 + 写回档案）
    corrections = []
    system_prompt = build_system_prompt(persona_text, name, summaries, corrections)
    history = [{'role': 'system', 'content': system_prompt}]
    rounds = 0

    print('=' * 56)
    print(f'  和「{name}」对话（/exit 退出并存档，/reset 清历史，/correct 纠正）')
    print('  引擎：' + ('本地 Ollama ' + OLLAMA_MODEL if engine == 'ollama'
                        else 'DeepSeek ' + DEEPSEEK_MODEL))
    print('=' * 56)

    try:
        while True:
            try:
                user_input = input('你 ❯ ').strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not user_input:
                continue
            if user_input in ('/exit', '/quit', 'exit', '退出'):
                break
            if user_input == '/reset':
                history = [{'role': 'system', 'content': system_prompt}]
                rounds = 0
                print('（已清空本轮历史）\n')
                continue
            if user_input == '/summary':
                summary = summarize(name, history[1:], engine, llm_key)
                path = save_summary(name, summary)
                print(f'（已存档：{path}）\n')
                continue
            if user_input.startswith('/correct'):
                text = user_input[len('/correct'):].strip()
                if text:
                    corrections.append(text)
                    n = append_correction(persona_path, text)
                    system_prompt = build_system_prompt(persona_text, name, summaries, corrections)
                    history[0] = {'role': 'system', 'content': system_prompt}
                    print(f'（已记录纠正 Correction #{n}，本次对话立即生效）\n')
                else:
                    print('（用法：/correct ta不会说晚安，只会说睡了）\n')
                continue

            history.append({'role': 'user', 'content': user_input})
            try:
                reply = _call_llm(history, engine, temperature=0.85, llm_key=llm_key,
                                  max_tokens=600)
            except RuntimeError as e:
                # 引擎不可用时给出友好提示（如 Ollama 未启动）
                history.pop()  # 移除刚加入的 user 消息，避免污染历史
                if engine == 'ollama':
                    print(f'⚠️ {e}\n  提示：Ollama 未运行？请先运行「启动.bat」，'
                          f'或单独启动 Ollama（ollama serve），或改用 --engine deepseek。\n')
                else:
                    print(f'⚠️ {e}\n')
                continue
            history.append({'role': 'assistant', 'content': reply})
            rounds += 1
            print(f'{name} ❯ {reply}\n')

            # 历史截断：system + 最近 MAX_ROUNDS 轮（防止上下文超限）
            if rounds > MAX_ROUNDS:
                history = history[:1] + history[-(MAX_ROUNDS * 2):]
                rounds = MAX_ROUNDS
    finally:
        if rounds > 0:
            print('（正在生成会话摘要存档…）')
            try:
                summary = summarize(name, history[1:], engine, llm_key)
                path = save_summary(name, summary)
                print(f'（已存档：{path}）')
            except Exception as e:  # noqa: BLE001
                print(f'（摘要存档失败：{e}）')


def main():
    parser = argparse.ArgumentParser(description='带记忆的对话工具（集成 ex-skill 记忆机制）')
    parser.add_argument('--persona', default='',
                        help='人格档案.md 路径（persona_builder.py 生成；与 --role 二选一）')
    parser.add_argument('--role', default='',
                        help='角色 id（见 tools/roles.json）。自动定位该角色绑定的独立人格档案，'
                             '保证一一对应不共用')
    parser.add_argument('--name', default='', help='名字（默认取文件名/角色显示名）')
    parser.add_argument('--engine', default='ollama', choices=['ollama', 'deepseek'],
                        help='对话引擎：ollama（默认本地）/ deepseek（云端）')
    parser.add_argument('--key', default=os.environ.get('DEEPSEEK_API_KEY', ''),
                        help='DeepSeek API Key（engine=deepseek 时必填）')
    args = parser.parse_args()

    # 角色模式：从注册表定位独立人格档案（一对一）
    if args.role:
        roles_file = Path(__file__).resolve().parent / 'roles.json'
        if not roles_file.exists():
            print(f'❌ 角色注册表不存在：{roles_file}')
            sys.exit(1)
        roles = json.loads(roles_file.read_text(encoding='utf-8'))
        if args.role not in roles.get('roles', {}):
            print(f'❌ 角色「{args.role}」不在注册表 tools/roles.json 中。'
                  f'可用角色：{", ".join(roles.get("roles", {}).keys()) or "（空）"}')
            sys.exit(1)
        role_cfg = roles['roles'][args.role]
        persona_path = Path(role_cfg['persona_file'])
        if not args.name:
            args.name = role_cfg.get('display_name', args.role)
        print(f'🔗 角色模式：{args.role}（{args.name}）→ 档案 {persona_path}')
    else:
        if not args.persona:
            parser.error('需要 --persona 档案路径，或 --role 角色 id')
        persona_path = Path(args.persona)

    if not persona_path.exists():
        print(f'❌ 人格档案不存在：{persona_path}')
        print('   （先用 persona_builder.py 生成：'
              f'python tools/persona_builder.py --role {args.role or "?"} --chat 聊天记录.txt，'
              '或 --init-skeleton 先生成骨架）')
        sys.exit(1)
    name = args.name or persona_path.stem.replace('人格档案_', '')

    chat_loop(persona_path, name, args.engine, args.key)


if __name__ == '__main__':
    main()
