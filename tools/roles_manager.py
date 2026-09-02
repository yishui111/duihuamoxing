#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
角色管理器 — 维护「角色 ↔ 独立人格档案」的一一对应关系
======================================================
保证每个角色（音色/数字人）有自己的独立人格档案，禁止共用。

用法：
  python tools/roles_manager.py list                 # 列出所有角色及状态
  python tools/roles_manager.py init-skeletons       # 为缺材料的角色批量生成骨架档案
  python tools/roles_manager.py show <role>          # 查看单个角色绑定详情

角色状态说明：
  pending   = 有材料，待蒸馏（运行 persona_builder.py --role xxx --chat 材料 后变 built）
  built     = 人格档案已蒸馏生成
  skeleton  = 缺材料，仅有骨架档案（提供材料后运行 build 蒸馏为 built）
"""

import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ROLES_FILE = Path(__file__).resolve().parent / 'roles.json'
PERSONA_DIR = BASE_DIR / 'docs' / '人格档案'


def load_roles() -> dict:
    if not ROLES_FILE.exists():
        print(f'❌ 角色注册表不存在：{ROLES_FILE}')
        sys.exit(1)
    return json.loads(ROLES_FILE.read_text(encoding='utf-8'))


def cmd_list(_args):
    roles = load_roles().get('roles', {})
    if not roles:
        print('角色注册表为空。')
        return
    print(f'共 {len(roles)} 个角色（每个角色独立人格档案，禁止共用）：\n')
    for rid, cfg in sorted(roles.items()):
        persona = Path(cfg.get('persona_file', ''))
        exists = '✅' if persona.exists() else '—'
        status_map = {'pending': '🕐 待蒸馏(有材料)', 'built': '✅ 已生成',
                      'skeleton': '🧱 仅骨架(缺材料)'}
        status = status_map.get(cfg.get('status', ''), cfg.get('status', '?'))
        print(f"  {rid:<12} {cfg.get('display_name', '?'):<6} [{status}] {exists} 档案: {cfg.get('persona_file', '?')}")
        note = cfg.get('note', '')
        if note:
            print(f"                ↳ {note}")
        print()


def cmd_show(args):
    roles = load_roles().get('roles', {})
    if args.role not in roles:
        print(f'❌ 角色「{args.role}」不存在。可用：{", ".join(roles) or "（空）"}')
        sys.exit(1)
    cfg = roles[args.role]
    print(f"角色：{args.role}（{cfg.get('display_name', '?')}）")
    for k, v in cfg.items():
        print(f"  {k}: {v}")
    persona = Path(cfg.get('persona_file', ''))
    print(f"  档案存在: {'是' if persona.exists() else '否'}")
    if not persona.exists():
        print('  提示：运行 python tools/persona_builder.py --role '
              f'{args.role} --chat "聊天记录.txt" 蒸馏生成（需提供该角色的材料）')


def cmd_init_skeletons(_args):
    """为 status=skeleton 且档案不存在的角色批量生成骨架档案。"""
    roles = load_roles().get('roles', {})
    # 复用 persona_builder 的骨架渲染，避免逻辑重复
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from persona_builder import render_skeleton_profile, set_role_status

    PERSONA_DIR.mkdir(parents=True, exist_ok=True)
    done, skipped = 0, 0
    for rid, cfg in sorted(roles.items()):
        persona = Path(cfg.get('persona_file', ''))
        if persona.exists():
            skipped += 1
            print(f'  — {rid}: 档案已存在，跳过')
            continue
        persona.parent.mkdir(parents=True, exist_ok=True)
        persona.write_text(render_skeleton_profile(rid, cfg), encoding='utf-8')
        set_role_status(rid, 'skeleton')
        done += 1
        print(f'  ✅ {rid}: 骨架档案已生成 {persona}')
    print(f'\n完成：生成 {done} 个，跳过 {skipped} 个。')


def main():
    parser = argparse.ArgumentParser(description='角色管理器（人格档案一对一绑定）')
    sub = parser.add_subparsers(dest='cmd')
    sub.add_parser('list', help='列出所有角色及状态')
    p_show = sub.add_parser('show', help='查看单个角色')
    p_show.add_argument('role')
    sub.add_parser('init-skeletons', help='为缺材料的角色批量生成骨架档案')
    args = parser.parse_args()

    if args.cmd == 'list':
        cmd_list(args)
    elif args.cmd == 'show':
        cmd_show(args)
    elif args.cmd == 'init-skeletons':
        cmd_init_skeletons(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
