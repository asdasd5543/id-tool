#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互 + CLI 混合版：身份证序列生成与校验工具（含无限生成模式）
- 当在生成过程中按 Ctrl+C：中止当前生成并返回主菜单（不退出程序）
- 交互式与 CLI 均支持无限生成（输入 inf 或 --infinite）
免责声明：仅用于学习/测试/模拟用途，严禁用于任何非法用途。
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

# 校验位计算常量
_WEIGHTS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
_MAPPING = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']


class UserInterruptedToMenu(Exception):
    """用于在生成过程中捕获 Ctrl+C 并返回交互式菜单的信号"""
    def __init__(self, generated: int = 0):
        self.generated = generated
        super().__init__("用户中断，返回菜单")


def get_system_location_info() -> Tuple[datetime, str, str]:
    local_now = datetime.now()
    is_dst = time.localtime().tm_isdst
    try:
        tz_name = time.tzname[1] if is_dst else time.tzname[0]
    except Exception:
        tz_name = "Local"
    utc_offset_seconds = (datetime.now() - datetime.utcnow()).total_seconds()
    utc_offset_hours = utc_offset_seconds / 3600.0
    offset_str = f"UTC{utc_offset_hours:+.1f}"
    return local_now, tz_name, offset_str


def calculate_check_digit(num_str: str) -> str:
    if len(num_str) != 17 or not num_str.isdigit():
        raise ValueError("calculate_check_digit: 输入必须为 17 位纯数字字符串")
    total = sum(int(num_str[i]) * _WEIGHTS[i] for i in range(17))
    return _MAPPING[total % 11]


def load_area_codes_from_file(path: Path) -> List[str]:
    codes: List[str] = []
    if not path.exists():
        raise FileNotFoundError(f"区域码文件不存在: {path}")
    with path.open(encoding="utf-8") as f:
        try:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                code = row[0].strip()
                if code and code.isdigit():
                    codes.append(code)
        except Exception:
            f.seek(0)
            for line in f:
                code = line.strip()
                if code and code.isdigit():
                    codes.append(code)
    return codes


# 默认示例区域码：为避免泄露或滥用，使用少量示例码
_DEFAULT_AREA_CODES = ['110000', '120000', '310000', '440000', '500000']


def random_id_sequence(
    area_codes: Iterable[str],
    start_date: datetime,
    end_date: datetime,
    count: Optional[int],
) -> Iterable[Tuple[str, str, str]]:
    """
    生成身份证序列。
    - 如果 count 为 None 则表示无限生成（yield 不断产生）
    - 每条结果为 (full_id, birthday_friendly, area_code)
    """
    if start_date >= end_date:
        raise ValueError("开始日期必须早于结束日期")
    delta_days = (end_date - start_date).days
    if delta_days <= 0:
        raise ValueError("日期范围至少一天以上")

    area_list = list(area_codes)
    if not area_list:
        raise ValueError("未提供任何区域码")

    if count is None:
        # 无限模式
        while True:
            area = random.choice(area_list)
            random_days = random.randint(0, delta_days - 1)
            target_date = start_date + timedelta(days=random_days)
            birthday_str = target_date.strftime("%Y%m%d")
            friendly_birthday = target_date.strftime("%Y年%m月%d日")
            sequence_num = str(random.randint(0, 999)).zfill(3)
            front_17 = f"{area}{birthday_str}{sequence_num}"
            check_char = calculate_check_digit(front_17)
            full_id = front_17 + check_char
            yield full_id, friendly_birthday, area
    else:
        for _ in range(count):
            area = random.choice(area_list)
            random_days = random.randint(0, delta_days - 1)
            target_date = start_date + timedelta(days=random_days)
            birthday_str = target_date.strftime("%Y%m%d")
            friendly_birthday = target_date.strftime("%Y年%m月%d日")
            sequence_num = str(random.randint(0, 999)).zfill(3)
            front_17 = f"{area}{birthday_str}{sequence_num}"
            check_char = calculate_check_digit(front_17)
            full_id = front_17 + check_char
            yield full_id, friendly_birthday, area


def cmd_generate(args: argparse.Namespace) -> int:
    """
    批量生成身份证样例。
    - 如果 args.infinite 为 True，则无限生成直到 Ctrl+C（必须确认）
    - 若输出到文件，在无限模式下采取流式写入
    在捕获到 KeyboardInterrupt 时抛出 UserInterruptedToMenu，以便返回交互式菜单而不是退出程序。
    """
    is_infinite = bool(getattr(args, "infinite", False))
    # 确认保护：无限模式必须确认，有限模式若未确认也弹交互确认
    if is_infinite or not getattr(args, "confirm", False):
        print("警告：批量生成身份证号码可能具有敏感性，仅限学术/测试/模拟用途。")
        if not getattr(args, "confirm", False):
            try:
                ans = input("是否继续？请输入 y 确认: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print("\n已取消。")
                return 1
            if ans != 'y':
                print("已取消。")
                return 1

    # 加载区域码（若提供文件则优先）
    if getattr(args, "area_codes_file", None):
        try:
            area_codes = load_area_codes_from_file(Path(args.area_codes_file))
            if not area_codes:
                print("从文件加载到的区域码为空，退出。")
                return 1
        except Exception as e:
            print(f"加载区域码文件失败: {e}")
            return 1
    else:
        area_codes = _DEFAULT_AREA_CODES

    # 解析日期
    try:
        start_date = datetime.strptime(getattr(args, "start", "2000-01-01"), "%Y-%m-%d")
        end_date = datetime.strptime(getattr(args, "end", "2020-01-01"), "%Y-%m-%d")
    except ValueError as e:
        print(f"日期格式错误: {e}")
        return 1

    # 确定 count：None 表示无限
    count_param: Optional[int] = None if is_infinite else int(getattr(args, "count", 10))

    generated = 0

    # 如果输出到文件且是无限模式，使用流式写入
    outfile = None
    if getattr(args, "output", None):
        out_path = Path(args.output)
        try:
            outfile = out_path.open("w", encoding="utf-8")
        except Exception as e:
            print(f"无法打开输出文件: {e}")
            return 1

    try:
        seq_iter = random_id_sequence(area_codes, start_date, end_date, count_param)
        for full_id, birthday, area in seq_iter:
            generated += 1
            line = f"[{generated}] {full_id}  ->  {birthday} (area:{area})"
            print(line)
            if outfile:
                outfile.write(f"{full_id},{birthday},{area}\n")
                if is_infinite:
                    outfile.flush()
    except KeyboardInterrupt:
        # 捕获 Ctrl+C：不要退出程序，转为返回主菜单
        if outfile:
            try:
                outfile.flush()
            except Exception:
                pass
        print(f"\n[⚠️] 已由用户中止。共生成 {generated} 条记录。返回主菜单...")
        raise UserInterruptedToMenu(generated)
    except Exception as e:
        print(f"\n生成过程中出现错误: {e}")
        if outfile:
            outfile.close()
        return 1
    finally:
        if outfile:
            outfile.close()

    if not is_infinite:
        print(f"完成：共生成 {generated} 条记录（范围: {getattr(args, 'start', '2000-01-01')} 至 {getattr(args, 'end', '2020-01-01')}）。")
    else:
        print(f"无限模式结束：本次共生成 {generated} 条记录（正常结束）")
    return 0


def cmd_calc17(args: argparse.Namespace) -> int:
    s = args.value.strip()
    if len(s) != 17 or not s.isdigit():
        print("错误：请输入严格的 17 位纯数字。")
        return 1
    try:
        check_char = calculate_check_digit(s)
    except ValueError as e:
        print(f"校验位计算错误: {e}")
        return 1

    year = s[6:10]
    month = s[10:12]
    day = s[12:14]
    gender_digit = int(s[-1])
    gender_symbol = "🚹 男生" if gender_digit % 2 != 0 else "🚺 女生"

    print("-" * 50)
    print(f"📅 拆解生日 : {year}年 {month}月 {day}日")
    print(f"🧬 识别性别 : {gender_symbol}")
    print(f"🧠 第18位码 : {check_char}")
    print(f"🆔 完整序列 : {s}{check_char}")
    print("-" * 50)
    return 0


def cmd_exhaust14(args: argparse.Namespace) -> int:
    base = args.value.strip()
    if len(base) != 14 or not base.isdigit():
        print("错误：请输入严格的 14 位纯数字。")
        return 1

    filter_choice = args.filter.lower()
    if filter_choice not in ('male', 'female', 'all'):
        print("无效筛选项，请选择 male / female / all")
        return 1

    print(f"准备对基底 {base} 进行穷举（最多 1000 种顺序号） 筛选: {filter_choice}")
    if not getattr(args, "confirm", False):
        try:
            ans = input("是否继续？请输入 y 确认: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\n已取消。")
            return 1
        if ans != 'y':
            print("已取消。")
            return 1

    results = []
    count = 0
    try:
        for i in range(1000):
            seq_str = str(i).zfill(3)
            gender_digit = int(seq_str[-1])
            is_male = (gender_digit % 2 != 0)

            if filter_choice == 'male' and not is_male:
                continue
            if filter_choice == 'female' and is_male:
                continue

            front_17 = base + seq_str
            check_character = calculate_check_digit(front_17)
            gender_symbol = "🚹 男生" if is_male else "🚺 女生"
            count += 1
            line = f"[{count}][{seq_str}] {front_17}{check_character} | {gender_symbol}"
            print(line)
            results.append((front_17 + check_character, gender_symbol))
    except KeyboardInterrupt:
        print("\n[⚠️] 已由用户中止穷举。")

    if getattr(args, "output", None):
        try:
            p = Path(args.output)
            with p.open("w", encoding="utf-8") as f:
                for fullid, gender in results:
                    f.write(f"{fullid},{gender}\n")
            print(f"结果已写入: {p}")
        except Exception as e:
            print(f"写出文件失败: {e}")
            return 1

    print(f"完成：共输出 {count} 条符合条件的数据。")
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="身份证序列工具（受限、安全默认）",
        epilog="免责声明：仅用于学习/测试/模拟用途，严禁用于任何非法用途。",
    )
    p.add_argument("--version", action="version", version="id-tool 1.3")
    sub = p.add_subparsers(dest="cmd")

    gen = sub.add_parser("generate", help="批量生成身份证样例（受控）")
    gen.add_argument("--count", type=int, default=10, help="生成条数（默认 10，若与 --infinite 同时存在则以 --infinite 为准）")
    gen.add_argument("--infinite", action="store_true", help="启用无限生成，直到用户中断（需确认）")
    gen.add_argument("--start", default="2000-01-01", help="起始日期 (YYYY-MM-DD)，默认 2000-01-01")
    gen.add_argument("--end", default="2020-01-01", help="结束日期 (YYYY-MM-DD)，默认 2020-01-01 (不含)")
    gen.add_argument("--area-codes-file", default=None, help="区域码文件路径（CSV 或每行一个码）")
    gen.add_argument("--output", default=None, help="可选：输出到文件 (CSV 格式)")
    gen.add_argument("--confirm", action="store_true", help="跳过交互确认")
    gen.set_defaults(func=cmd_generate)

    c17 = sub.add_parser("calc17", help="计算第18位校验码并解析生日/性别（输入 17 位）")
    c17.add_argument("value", help="17 位数字")
    c17.set_defaults(func=cmd_calc17)

    ex = sub.add_parser("exhaust14", help="对 14 位基底进行 000-999 穷举（可筛选性别）")
    ex.add_argument("value", help="14 位数字基底")
    ex.add_argument("--filter", default="all", help="筛选: male / female / all (默认 all)")
    ex.add_argument("--output", default=None, help="可选：输出到文件 (CSV)")
    ex.add_argument("--confirm", action="store_true", help="跳过交互确认")
    ex.set_defaults(func=cmd_exhaust14)

    return p


def interactive_mode() -> int:
    """
    交互式菜单（当用户双击或未提供 CLI 参数时使用）
    捕获并处理 UserInterruptedToMenu，以确保 Ctrl+C 不会退出程序。
    """
    while True:
        local_now, tz_name, offset_str = get_system_location_info()
        print("\n" + "=" * 50)
        print("🎛️  自动化数据控制中心（交互式）")
        print(f"🌐 节点位置: {tz_name} ({offset_str}) | {local_now.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        print("1. 批量生成（generate）")
        print("2. 17位校验计算（calc17）")
        print("3. 14位穷举（exhaust14）")
        print("4. 退出")
        print("=" * 50)
        try:
            choice = input("请选择功能 (1-4): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n已取消，退出。")
            return 0

        if choice == '1':
            # 支持输入 inf/infinite 表示无限生成
            cnt_raw = input("生成条数（输入 inf 表示无限，默认10）: ").strip() or "10"
            if cnt_raw.lower() in ("inf", "infinite"):
                count = 0  # placeholder
                infinite = True
            else:
                infinite = False
                try:
                    count = int(cnt_raw)
                    if count < 0:
                        print("无效数字，使用默认 10。")
                        count = 10
                except ValueError:
                    print("无效输入，使用默认 10。")
                    count = 10
            start = input("起始日期 (YYYY-MM-DD) [默认 2000-01-01]: ").strip() or "2000-01-01"
            end = input("结束日期 (YYYY-MM-DD) [默认 2020-01-01]: ").strip() or "2020-01-01"
            acf = input("区域码文件路径（留空使用示例区域码）: ").strip() or None
            out = input("输出文件（留空为不写文件）: ").strip() or None
            # 构造 Namespace 与调用
            ns = argparse.Namespace(
                count=count,
                infinite=infinite,
                start=start,
                end=end,
                area_codes_file=acf,
                output=out,
                confirm=True,  # 交互模式默认跳过二次确认以便顺畅体验
            )
            try:
                cmd_generate(ns)
            except UserInterruptedToMenu as e:
                # 已在 cmd_generate 中打印提示，这里仅让交互继续
                pass
            # 等待用户回到菜单：即便用户在生成时按过 Ctrl+C，也不要因为上次 Ctrl+C 而跳过这个等待
            try:
                input("\n按回车返回主菜单...")
            except (KeyboardInterrupt, EOFError):
                # 忽略，直接回到菜单
                pass
        elif choice == '2':
            val = input("请输入 17 位数字: ").strip()
            ns = argparse.Namespace(value=val)
            try:
                cmd_calc17(ns)
            except UserInterruptedToMenu:
                pass
            try:
                input("\n按回车返回主菜单...")
            except (KeyboardInterrupt, EOFError):
                pass
        elif choice == '3':
            val = input("请输入 14 位数字基底: ").strip()
            filt = input("筛选 (male/female/all) [默认 all]: ").strip() or "all"
            out = input("输出文件（留空为不写文件）: ").strip() or None
            ns = argparse.Namespace(value=val, filter=filt, output=out, confirm=True)
            try:
                cmd_exhaust14(ns)
            except UserInterruptedToMenu:
                pass
            try:
                input("\n按回车返回主菜单...")
            except (KeyboardInterrupt, EOFError):
                pass
        elif choice == '4':
            print("退出。")
            return 0
        else:
            print("无效选项，请输入 1-4。")


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_arg_parser()

    # 如果没有提供命令行参数（例如双击运行或直接 python script.py），进入交互式菜单
    if argv is None and len(sys.argv) == 1:
        return interactive_mode()

    # 常规 CLI 路径：解析并执行子命令
    args = parser.parse_args(argv)
    local_now, tz_name, offset_str = get_system_location_info()
    print(f"节点: {tz_name} ({offset_str}) | 当前时间: {local_now.strftime('%Y-%m-%d %H:%M:%S')}")
    print("注意：本工具默认使用较保守的示例区域码，如需真实区域码，请提供 --area-codes-file。")
    print("---------")
    try:
        if hasattr(args, "func"):
            try:
                return args.func(args)
            except UserInterruptedToMenu:
                # 在 CLI 模式下按 Ctrl+C 也不要直接退出程序，转而进入交互式菜单
                print("已中止当前命令，进入交互式菜单。")
                return interactive_mode()
        else:
            # 如果没有 func（例如没有子命令），进入交互式模式
            return interactive_mode()
    except Exception as e:
        print(f"发生未捕获异常: {e}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())