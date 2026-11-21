"""以“建房资料空表.xlsx”为底稿填值，导出可直接打印的两张表。"""

import math
import os
import shutil
import tempfile
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Alignment

TEMPLATE = Path(__file__).resolve().parents[3] / 'house_build_templates' / '建房资料空表.xlsx'

BUILD_TYPES = [(1, '原址翻建'), (2, '改扩建'), (3, '异址新建')]
LAND_TYPES = [(1, '建设用地'), (2, '未利用地'), (3, '农用地(耕地、林地、草地、其它  )')]


def _s(value):
    return '' if value is None else str(value).strip()


def _tick(options, selected, head, sep='\n'):
    """把选项文本按选中项打 √：支持传序号 "1" 或选项名。"""
    sel = _s(selected)
    return '%s%s' % (head, sep.join(
        '%d.%s%s' % (no, name, '√' if (sel == str(no) or sel == name or sel in name) else '')
        for no, name in options
    ))


def _four_to(app):
    return '东至：%s        南至：%s' % (_s(app.get('east_to')), _s(app.get('south_to')))


def _four_from(app):
    return '西至：%s             北至：%s' % (_s(app.get('west_to')), _s(app.get('north_to')))


def _date_cn(value):
    text = _s(value)
    if len(text) >= 10:
        return '%s年%s月%s日' % (text[0:4], int(text[5:7]), int(text[8:10]))
    return ''


def _disposal_text(app):
    mode = _s(app.get('current_disposal'))
    area = _s(app.get('current_land_area'))
    other = _s(app.get('current_disposal_other'))
    keep = '√' if (mode in ('1', '保留') or mode.startswith('保留')) else ''
    back = '√' if (mode in ('2', '退给村集体') or '退' in mode) else ''
    oth = '√' if (mode in ('3', '其他') or mode == '其他') else ''
    return '1.保留( %s m²)%s;2.退给村集体%s；3.其他(%s)%s' % (area, keep, back, other, oth)


def _set(ws, coord, value, wrap=False):
    cell = ws[coord]
    cell.value = value
    if wrap:
        align = cell.alignment
        cell.alignment = Alignment(
            horizontal=align.horizontal or 'left',
            vertical=align.vertical or 'center',
            wrap_text=True,
            shrink_to_fit=False,
            indent=align.indent or 0,
        )


def _autofit(ws, row, char_units, base_height, min_height=None):
    """按文本长度估算所需行高，超过原行高才放大，避免长文本被裁掉。"""
    values = []
    for col in range(1, 10):
        value = ws.cell(row=row, column=col).value
        if value:
            values.append(str(value))
    text = '\n'.join(values)
    if not text:
        return
    per_line = max(6, int(char_units / 2))
    lines = 0
    for seg in text.split('\n'):
        lines += max(1, math.ceil(len(seg) / per_line))
    need = lines * 15.5 + 6
    have = min_height or base_height
    if need > have:
        ws.row_dimensions[row].height = round(need, 1)


def _fill_apply(ws, app):
    members = app.get('members') or []

    _set(ws, 'C2', _s(app.get('owner_name')))
    _set(ws, 'E2', _s(app.get('owner_gender')))
    _set(ws, 'G2', _s(app.get('owner_age')))
    _set(ws, 'I2', _s(app.get('owner_phone')))
    _set(ws, 'C3', _s(app.get('owner_id_card')))
    _set(ws, 'G3', _s(app.get('owner_hukou')))

    for index in range(5):
        row = 5 + index
        member = members[index] if index < len(members) else {}
        _set(ws, 'B%d' % row, _s(member.get('name')))
        _set(ws, 'C%d' % row, _s(member.get('age')))
        _set(ws, 'D%d' % row, _s(member.get('relation')))
        _set(ws, 'E%d' % row, _s(member.get('id_card')))
        _set(ws, 'G%d' % row, _s(member.get('hukou')))

    _set(ws, 'D10', _s(app.get('apply_land_area')))
    _set(ws, 'F10', _s(app.get('building_area')))
    _set(ws, 'H10', _s(app.get('cert_no')))
    _set(ws, 'D11', _disposal_text(app), wrap=True)
    _set(ws, 'D12', _s(app.get('current_land_area')))
    _set(ws, 'H12', _s(app.get('foundation_area')))
    _set(ws, 'C13', _four_to(app))
    _set(ws, 'C14', _four_from(app))
    _set(ws, 'G13', _tick(BUILD_TYPES, app.get('build_type'), '建房类型：'))
    _set(ws, 'C15', _tick(LAND_TYPES, app.get('land_type'), '', '    '))
    _set(ws, 'D17', _s(app.get('house_floor_area')))
    _set(ws, 'F17', _s(app.get('floors')))
    _set(ws, 'H17', _s(app.get('building_height')))

    neighbor = _s(app.get('neighbor_opinion'))
    yes = '√' if neighbor in ('1', '是') else ''
    no = '√' if neighbor in ('2', '否') else ''
    _set(ws, 'B18', '是否征求相邻权利人意见：   1.是%s      2.否%s' % (yes, no))

    design = _s(app.get('design_plan'))
    yes = '√' if design in ('1', '是') else ''
    no = '√' if design in ('2', '否') else ''
    _set(ws, 'B19', '是否有农村住宅设计方案或拟采用的住宅建设通用图集：  1.是%s     2.否%s' % (yes, no), wrap=True)

    reason = _s(app.get('apply_reason'))
    date = _date_cn(app.get('created_at'))
    _set(ws, 'B20', '%s\n\n申请人：%s          %s' % (reason, _s(app.get('owner_name')), date), wrap=True)

    opinion = _s(app.get('village_opinion'))
    leader = _s(app.get('village_leader'))
    vdate = _s(app.get('village_date'))
    _set(ws, 'B22', '%s\n\n负责人：%s          %s' % (opinion, leader, vdate), wrap=True)

    _autofit(ws, 20, 8 * 5 + 8.43, 25.0, min_height=25.0)
    _autofit(ws, 22, 8 * 5 + 8.43, 69.0, min_height=69.0)


def _fill_approval(ws, app):
    approvals = app.get('approvals') or {}

    _set(ws, 'C2', _s(app.get('owner_name')))
    _set(ws, 'E2', _s(app.get('owner_gender')))
    _set(ws, 'G2', _s(app.get('owner_id_card')))
    _set(ws, 'C3', _s(app.get('approval_address')) or _s(app.get('owner_hukou')))
    _set(ws, 'C4', _s(app.get('apply_reason')), wrap=True)
    _set(ws, 'C5', _s(app.get('approval_land_area')))
    _set(ws, 'G5', _s(app.get('approval_foundation_area')))
    _set(ws, 'C6', _s(app.get('approval_address')))
    _set(ws, 'C7', _four_to(app))
    _set(ws, 'C8', _four_from(app))
    _set(ws, 'G7', _tick(BUILD_TYPES, app.get('approval_build_type'), '建房类型：'))
    _set(ws, 'C9', _tick(LAND_TYPES, app.get('approval_land_type'), '', '    '))
    _set(ws, 'D11', _s(app.get('approval_house_floor_area')))
    _set(ws, 'F11', _s(app.get('approval_floors')))
    _set(ws, 'I11', _s(app.get('approval_height')))

    mapping = [('natural', 12), ('housing', 13), ('agriculture', 14), ('other', 15), ('government', 16)]
    for key, row in mapping:
        item = approvals.get(key) or {}
        opinion = _s(item.get('opinion'))
        leader = _s(item.get('leader'))
        date = _s(item.get('date'))
        tail = []
        if key in ('other', 'government'):
            tail.append('(盖章)')
        tail.append('')
        tail.append('负责人：%s          %s' % (leader, date))
        _set(ws, 'B%d' % row, '%s\n\n%s' % (opinion, '\n'.join(tail)), wrap=True)

    for row in (12, 13, 14, 15, 16):
        _autofit(ws, row, 8 * 5 + 8.43, 75.0, min_height=75.0)


def export_app_xlsx(app):
    """返回生成好的 xlsx 绝对路径，调用方负责清理临时目录。"""
    if app is None:
        raise ValueError('申请记录不存在')

    tmp_dir = tempfile.mkdtemp(prefix='hb_export_')
    out_name = '宅基地建房申请_%s_%s.xlsx' % (_s(app.get('owner_name')) or '未命名', _s(app.get('app_no')) or '')
    out_path = os.path.join(tmp_dir, out_name)
    shutil.copyfile(TEMPLATE, out_path)

    wb = load_workbook(out_path)
    apply_ws = wb.worksheets[0]
    approval_ws = wb.worksheets[1] if len(wb.worksheets) > 1 else None
    _fill_apply(apply_ws, app)
    if approval_ws is not None:
        _fill_approval(approval_ws, app)
    wb.save(out_path)
    return out_path

