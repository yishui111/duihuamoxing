# tools —— 人格蒸馏与角色工具（自研）

把「聊天记录 / 口述 / 个人资料」蒸馏成**人格档案**（markdown），并把档案绑定到具体角色
（音色/数字人）。全部**仅用 Python 标准库**（urllib 调 LLM），零第三方依赖。

```
tools\
├── persona_builder.py    人格蒸馏器：材料 → 五层人格档案（Layer0 硬规则/身份/说话风格/情感模式/关系行为
│                         + 关系记忆 + 证据标注 + 置信度说明 + Correction 记录）
├── chat_memory.py        带记忆的对话演示：多轮历史自动维护 + 跨会话摘要记忆 + /correct 纠正
├── roles_manager.py      角色注册表维护：list / show / init-skeletons
├── roles.example.json    角色注册表模板（复制为 roles.json 后使用）
└── sensevoice_stt.py     SenseVoice 语音识别子进程脚本（可选，供语音输入实验）
```

## 快速上手

```bash
# 1) 注册表模板（如需按角色绑定档案；不绑定角色可跳过）
copy tools\roles.example.json tools\roles.json

# 2) 蒸馏人格档案（引擎二选一）
python tools/persona_builder.py --chat "聊天记录.txt" --name "小满"          # 默认 deepseek（需 DEEPSEEK_API_KEY）
python tools/persona_builder.py --chat "聊天记录.txt" --name "小满" --engine ollama   # 本地 qwen2.5:7b
# 可选 --base-info "docs/个人资料模板.md"（先按模板整理简历式资料）

# 3) 生成结果默认写到 docs\人格档案_小满.md，接入方式（二选一）：
#    - 知识库：Open WebUI 工作空间 → 知识库上传该 md，对话时输入 # 引用
#    - 模型预设：工作空间 → 模型 → 创建模型，把档案全文粘贴进系统提示词（推荐）

# 4) 带记忆对话（可选）
python tools/chat_memory.py --persona "docs\人格档案_小满.md" --name 小满
#    对话内: /exit 退出并存摘要 /correct xxx 纠正并写回档案
```

## 角色一对一绑定（可选功能）

`roles.json` 中每个角色（音色/数字人）绑定自己独立的档案，禁止共用：

```jsonc
{ "roles": { "<角色id>": {
    "display_name": "显示名",
    "persona_file": "docs/人格档案/<id>.md",   // 该角色独立档案
    "voice_model": "<id>",                     // 音色模型名
    "avatar_lib": "",                          // 数字人素材库名（可空）
    "chat_model": "qwen2.5:7b",
    "material_files": ["材料路径(本地,勿提交)"],
    "status": "pending | built | skeleton",
    "note": "备注"
}}}
```

- 用 `--role` 操作时自动定位该角色自己的档案；不在注册表的角色会直接报错（防串用）。
- 初始化骨架：`python tools/roles_manager.py init-skeletons`（为缺材料的角色生成骨架档案）。

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DEEPSEEK_API_KEY` | 无（deepseek 引擎必需） | DeepSeek API Key |
| `DEEPSEEK_BASE_URL` | https://api.deepseek.com | 兼容端点 |
| `DEEPSEEK_MODEL` | deepseek-chat | 模型名 |
| `OLLAMA_URL` | http://localhost:11434 | 本地 Ollama |
| `OLLAMA_MODEL` | qwen2.5:7b | 本地模型 |

## ⚠️ 隐私提醒

**个人材料（真实聊天记录、真实个人资料、真人音色 ref 音频等）属于隐私数据，请勿提交到公开仓库。**
- 材料放在仓库外或加入 `.gitignore`；
- 生成的档案若含真实个人信息，同样不要提交；`docs\个人资料模板.md` 只是虚构示例。
