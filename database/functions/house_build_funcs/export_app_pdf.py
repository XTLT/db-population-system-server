"""用 reportlab 按原表版式重排两张表，每张一页 A4 纵向，中文字体 simhei。"""

import os
import re
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, PageBreak, Spacer, Table, TableStyle

from .template_texts import (
    APPLICANT_SIGN,
    VILLAGE_SIGN,
    APPROVAL_HEADS,
    APPROVAL_SEAL,
    APPROVAL_SIGN,
)

FONT_PATH = Path(__file__).resolve().parents[3] / 'house_build_templates' / 'simhei.ttf'
FONT_NAME = 'HBFont'
_registered = False

BUILD_TYPES = [(1, '原址翻建'), (2, '改扩建'), (3, '异址新建')]
LAND_TYPES = [(1, '建设用地'), (2, '未利用地'), (3, '农用地(耕地、林地、草地、其它)')]

# 落款与机构意见文案见 template_texts（与空表原文一致）

AREA_UNIT_RE = re.compile(r'\s*(平方米|平米|m²|m2|㎡)\s*$', re.IGNORECASE)


def _ensure_font():
    global _registered
    if _registered:
        return FONT_NAME
    if FONT_PATH.exists():
        pdfmetrics.registerFont(TTFont(FONT_NAME, str(FONT_PATH)))
    else:
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
        return 'STSong-Light'
    _registered = True
    return FONT_NAME


def _s(value):
    return '' if value is None else str(value).strip()


def _area_text(value):
    """面积值统一成 "120.5"，单位在渲染时单独画上标。"""
    text = _s(value)
    if not text:
        return ''
    return AREA_UNIT_RE.sub('', text).strip()


def _area_p(value, size=10, align=1):
    """面积段落：数字 + 上标 m²（simhei 没有 ² 字形，用上标画出来）。"""
    text = _area_text(value)
    if not text:
        return ''
    font = _ensure_font()
    style = ParagraphStyle(
        'hbarea%d_%d' % (size, align),
        fontName=font,
        fontSize=size,
        leading=size * 1.45,
        alignment=align,
        wordWrap='CJK',
    )
    return Paragraph('%s m<super rise=2 size=6>2</super>' % escape(text), style)


def _area_markup(value, size=10):
    """面积的内联标记：数字 + 上标 2，前后不再带单位文字。"""
    text = _area_text(value)
    if not text:
        return ''
    return '%s m<super rise=2 size=%d>2</super>' % (escape(text), max(4, int(size * 0.6)))


def _pick(options, selected):
    """把选中值归一到一个选项名：支持序号、选项名、"1.原址翻建"、部分关键词。
    空值返回 None，绝不再因为空串而把所有选项都打勾。"""
    sel = _s(selected)
    if not sel:
        return None
    for no, name in options:
        if sel == str(no) or sel == name:
            return name
    for no, name in options:
        if sel.startswith('%d.' % no) or ('%d.' % no) in sel:
            return name
    for no, name in options:
        if len(sel) >= 2 and (sel in name or name in sel):
            return name
    return None


def _tick(options, selected, head, sep='\n'):
    """只勾唯一命中的那一个选项。"""
    pick = _pick(options, selected)
    return '%s%s' % (head, sep.join(
        '%d.%s%s' % (no, name, '√' if name == pick else '')
        for no, name in options
    ))


def _p(text, size=10, align=0, leading=None):
    font = _ensure_font()
    style = ParagraphStyle(
        'hb%d_%d' % (size, align),
        fontName=font,
        fontSize=size,
        leading=leading or size * 1.45,
        alignment=align,
        wordWrap='CJK',
    )
    return Paragraph(escape(_s(text)).replace('\n', '<br/>'), style)


def _raw_p(markup, size=10, align=0):
    """已是 reportlab 标记的段落，不再转义。"""
    font = _ensure_font()
    style = ParagraphStyle(
        'hbraw%d_%d' % (size, align),
        fontName=font,
        fontSize=size,
        leading=size * 1.45,
        alignment=align,
        wordWrap='CJK',
    )
    return Paragraph(markup.replace('\n', '<br/>'), style)


def _need_height(text, width, size=10):
    text = _s(text)
    if not text:
        return 0
    per_line = max(4, int(width / (size * 1.02)))
    lines = 0
    for seg in text.split('\n'):
        lines += max(1, (len(seg) + per_line - 1) // per_line)
    return lines * (size * 1.45) + 8


def _fit_heights(heights, limit, floor=16.0):
    """总高超过一页可用高度时等比压缩，保证整表落在一页内。"""
    total = sum(heights)
    if total <= limit:
        return heights
    ratio = limit / total
    return [max(floor, round(h * ratio, 1)) for h in heights]


def _date_cn(value):
    text = _s(value)
    if len(text) >= 10:
        return '%s年%s月%s日' % (text[0:4], int(text[5:7]), int(text[8:10]))
    return ''


def _disposal_text(app):
    """现宅基地处置情况：纯文本版（供高度估算）。"""
    mode = _s(app.get('current_disposal'))
    area = _area_text(app.get('current_land_area'))
    other = _s(app.get('current_disposal_other'))
    keep = '√' if mode in ('1', '保留') else ''
    back = '√' if (mode in ('2', '退给村集体') or '退' in mode) else ''
    oth = '√' if mode in ('3', '其他') else ''
    return '1.保留( %s m² )%s;2.退给村集体%s；3.其他(%s)%s' % (area, keep, back, other, oth)


def _disposal_markup(app, size=9):
    """现宅基地处置情况：带 m 上标 2 的段落标记。"""
    mode = _s(app.get('current_disposal'))
    area = _area_markup(app.get('current_land_area'), size)
    other = escape(_s(app.get('current_disposal_other')))
    keep = '√' if mode in ('1', '保留') else ''
    back = '√' if (mode in ('2', '退给村集体') or '退' in mode) else ''
    oth = '√' if mode in ('3', '其他') else ''
    return '1.保留( %s )%s;2.退给村集体%s；3.其他(%s)%s' % (area, keep, back, other, oth)


def _build_apply(app, width, limit):
    """申请表：9 列网格，按模板合并区拼装。"""
    col = [width * r for r in (61.1 / 474.2, 49.1 / 474.2, 49.1 / 474.2, 49.1 / 474.2,
                               49.1 / 474.2, 49.1 / 474.2, 53.8 / 474.2, 49.1 / 474.2,
                               64.7 / 474.2)]
    members = app.get('members') or []

    grid = [['' for _ in range(9)] for _ in range(23)]

    def put(row, colno, text, size=10, align=0):
        grid[row][colno] = _p(text, size, align) if text is not None else ''

    def put_area(row, colno, value, size=10, align=1):
        grid[row][colno] = _area_p(value, size, align)

    def put_raw(row, colno, markup, size=9, align=0):
        grid[row][colno] = _raw_p(markup, size, align)

    def put_sign(row, colno, text, sign, size=10):
        flow = []
        if text:
            flow.append(_p(text, size, 0))
        flow.append(Spacer(1, 14))
        flow.append(_p(sign, size, 2))
        grid[row][colno] = flow

    put(0, 0, '农村宅基地和建房(规划许可)申请表', 16, 1)
    put(1, 0, '申请人信息', 11, 1)
    put(1, 1, '姓名', 10, 1); put(1, 2, _s(app.get('owner_name')), 10, 1)
    put(1, 3, '性别', 10, 1); put(1, 4, _s(app.get('owner_gender')), 10, 1)
    put(1, 5, '年龄', 10, 1); put(1, 6, _s(app.get('owner_age')), 10, 1)
    put(1, 7, '联系电话', 10, 1); put(1, 8, _s(app.get('owner_phone')), 10, 1)

    put(2, 1, '身份证号', 10, 1); put(2, 2, _s(app.get('owner_id_card')), 10, 1)
    put(2, 4, '户口所在地', 10, 1); put(2, 6, _s(app.get('owner_hukou')), 10, 1)

    put(3, 0, '家庭成员\n信息', 11, 1)
    put(3, 1, '姓名', 10, 1); put(3, 2, '年龄', 10, 1)
    put(3, 3, '与户主关系', 10, 1); put(3, 4, '身份证号', 10, 1)
    put(3, 6, '户口所在地', 10, 1)

    for index in range(5):
        row = 4 + index
        member = members[index] if index < len(members) else {}
        put(row, 1, _s(member.get('name')), 10, 1)
        put(row, 2, _s(member.get('age')), 10, 1)
        put(row, 3, _s(member.get('relation')), 10, 1)
        put(row, 4, _s(member.get('id_card')), 10, 1)
        put(row, 6, _s(member.get('hukou')), 10, 1)

    put(9, 0, '拟申请\n宅基地\n及建房\n(规划许可)\n情况', 11, 1)
    put(9, 1, '宅基地面积', 10, 1); put_area(9, 3, app.get('apply_land_area'), 10, 1)
    put(9, 4, '建筑面积', 10, 1); put_area(9, 5, app.get('building_area'), 10, 1)
    put(9, 6, '权属证书号', 9, 1); put(9, 7, _s(app.get('cert_no')), 9, 1)

    put(10, 1, '现宅基地处置情况', 10, 1)
    put_raw(10, 3, _disposal_markup(app, 9), 9, 0)
    put(11, 1, '宅基地面积', 10, 1); put_area(11, 3, app.get('current_land_area'), 10, 1)
    put(11, 5, '房基占地面积', 10, 1); put_area(11, 7, app.get('foundation_area'), 10, 1)

    put(12, 1, '四至', 10, 1)
    put(12, 2, '东至：%s        南至：%s' % (_s(app.get('east_to')), _s(app.get('south_to'))), 9, 0)
    put(13, 2, '西至：%s             北至：%s' % (_s(app.get('west_to')), _s(app.get('north_to'))), 9, 0)
    put(12, 6, _tick(BUILD_TYPES, app.get('build_type'), '建房类型：'), 9, 0)

    put(14, 1, '地类', 10, 1)
    put(14, 2, _tick(LAND_TYPES, app.get('land_type'), '', '    '), 9, 0)

    put(16, 1, '住房建筑面积', 10, 1); put_area(16, 3, app.get('house_floor_area'), 10, 1)
    put(16, 4, '建筑\n层数', 10, 1); put(16, 5, _s(app.get('floors')), 10, 1)
    put(16, 6, '建筑高度', 10, 1); put(16, 7, _s(app.get('building_height')), 10, 1)

    neighbor = _s(app.get('neighbor_opinion'))
    yes = '√' if neighbor in ('1', '是') else ''
    no = '√' if neighbor in ('2', '否') else ''
    put(17, 1, '是否征求相邻权利人意见：   1.是%s      2.否%s' % (yes, no), 10, 0)

    design = _s(app.get('design_plan'))
    yes = '√' if design in ('1', '是') else ''
    no = '√' if design in ('2', '否') else ''
    put(18, 1, '是否有农村住宅设计方案或拟采用的住宅建设通用图集：  1.是%s     2.否%s' % (yes, no), 9, 0)

    put(19, 0, '申请理由', 11, 1)
    put_sign(19, 1, _s(app.get('apply_reason')), APPLICANT_SIGN, 10)

    put(21, 0, '村集体经济\n组织或村民\n委员会意见', 11, 1)
    put_sign(21, 1, _s(app.get('village_opinion')), VILLAGE_SIGN, 10)

    put(22, 0, '备注', 10, 1)
    put(22, 1, '宅基地涉及占用耕地的，宅基地面积最高不超过170平方米；宅基地不涉及占用耕地的，\n'
               '宅基地面积最高不超过200平方米。', 10, 0)

    spans = [
        ('SPAN', (0, 0), (8, 0)),
        ('SPAN', (0, 1), (0, 2)),
        ('SPAN', (2, 2), (3, 2)), ('SPAN', (4, 2), (5, 2)), ('SPAN', (6, 2), (8, 2)),
        ('SPAN', (0, 3), (0, 8)),
        ('SPAN', (4, 3), (5, 3)), ('SPAN', (6, 3), (8, 3)),
    ]
    for index in range(5):
        row = 4 + index
        spans.append(('SPAN', (4, row), (5, row)))
        spans.append(('SPAN', (6, row), (8, row)))
    spans += [
        ('SPAN', (0, 9), (0, 18)),
        ('SPAN', (1, 9), (2, 9)), ('SPAN', (7, 9), (8, 9)),
        ('SPAN', (1, 10), (2, 10)), ('SPAN', (3, 10), (8, 10)),
        ('SPAN', (1, 11), (2, 11)), ('SPAN', (3, 11), (4, 11)),
        ('SPAN', (5, 11), (6, 11)), ('SPAN', (7, 11), (8, 11)),
        ('SPAN', (1, 12), (1, 13)), ('SPAN', (2, 12), (5, 12)),
        ('SPAN', (2, 13), (5, 13)), ('SPAN', (6, 12), (8, 15)),
        ('SPAN', (1, 14), (1, 15)), ('SPAN', (2, 14), (5, 15)),
        ('SPAN', (1, 16), (2, 16)), ('SPAN', (7, 16), (8, 16)),
        ('SPAN', (1, 17), (8, 17)),
        ('SPAN', (1, 18), (8, 18)),
        ('SPAN', (0, 19), (0, 20)),
        ('SPAN', (1, 19), (8, 20)),
        ('SPAN', (1, 21), (8, 21)),
        ('SPAN', (1, 22), (8, 22)),
    ]

    heights = [28.0] + [25.0] * 18 + [25.0, 25.0] + [69.0, 30.0]

    reason_text = '%s\n\n%s' % (_s(app.get('apply_reason')), APPLICANT_SIGN)
    need = _need_height(reason_text, width - col[0], 10)
    if need > heights[19] + heights[20]:
        heights[20] += need - heights[19] - heights[20]

    village_text = '%s\n\n%s' % (_s(app.get('village_opinion')), VILLAGE_SIGN)
    need = _need_height(village_text, width - col[0], 10)
    if need > heights[21]:
        heights[21] = need

    heights = _fit_heights(heights, limit, 14.0)
    table = Table(grid, colWidths=col, rowHeights=heights)
    table.setStyle(TableStyle(
        spans + [
            ('GRID', (0, 0), (-1, -1), 0.6, '#000000'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('VALIGN', (1, 19), (8, 20), 'BOTTOM'),
            ('VALIGN', (1, 21), (8, 21), 'BOTTOM'),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]
    ))
    return table


def _build_approval(app, width, limit):
    """审批表：9 列网格，按模板合并区拼装。"""
    ratios = (70.8, 49.2, 49.2, 49.2, 49.2, 49.2, 49.2, 41.6, 49.2)
    total = sum(ratios)
    col = [width * r / total for r in ratios]

    grid = [['' for _ in range(9)] for _ in range(17)]

    def put(row, colno, text, size=10, align=0):
        grid[row][colno] = _p(text, size, align) if text is not None else ''

    def put_area(row, colno, value, size=10, align=1):
        grid[row][colno] = _area_p(value, size, align)

    put(0, 0, '农村宅基地和建房(规划许可)审批表', 16, 1)
    put(1, 0, '申请人信息', 11, 1)
    put(1, 1, '姓名', 10, 1); put(1, 2, _s(app.get('owner_name')), 10, 1)
    put(1, 3, '性别', 10, 1); put(1, 4, _s(app.get('owner_gender')), 10, 1)
    put(1, 5, '身份证号', 10, 1); put(1, 6, _s(app.get('owner_id_card')), 10, 1)

    put(2, 1, '家庭住址', 10, 1)
    put(2, 2, _s(app.get('approval_address')) or _s(app.get('owner_hukou')), 10, 0)
    put(3, 1, '申请理由', 10, 1)
    put(3, 2, _s(app.get('apply_reason')), 10, 0)

    put(4, 0, '拟批准\n宅基地\n及建房情况', 11, 1)
    put(4, 1, '宅基地面积', 9, 1); put_area(4, 2, app.get('approval_land_area'), 10, 1)
    put(4, 5, '房基占地\n面积', 9, 1); put_area(4, 6, app.get('approval_foundation_area'), 10, 1)
    put(5, 1, '地址', 10, 1); put(5, 2, _s(app.get('approval_address')) or _s(app.get('owner_hukou')), 10, 0)
    put(6, 1, '四至', 10, 1)
    put(6, 2, '东至：%s        南至：%s' % (_s(app.get('east_to')), _s(app.get('south_to'))), 9, 0)
    put(7, 2, '   西至：%s             北至：%s' % (_s(app.get('west_to')), _s(app.get('north_to'))), 9, 0)
    put(6, 6, _tick(BUILD_TYPES, app.get('approval_build_type') or app.get('build_type'), '建房类型：'), 9, 0)
    put(8, 1, '地类', 10, 1)
    put(8, 2, _tick(LAND_TYPES, app.get('approval_land_type') or app.get('land_type'), '', '    '), 9, 0)

    put(10, 1, '住房建筑面积', 10, 1); put_area(10, 3, app.get('approval_house_floor_area'), 10, 1)
    put(10, 4, '建筑层数', 10, 1); put(10, 5, _s(app.get('approval_floors')), 10, 1)
    put(10, 6, '建筑高度', 10, 1); put(10, 8, _s(app.get('approval_height')), 10, 1)

    labels = [
        ('natural', '乡镇承担自然\n资源职责的\n机构意见'),
        ('housing', '乡镇承担住房\n建设职责的\n机构意见'),
        ('agriculture', '乡镇承担农业\n农村职责的\n机构审查意见'),
        ('other', '其他机构部门\n审批意见'),
        ('government', '乡镇(人民)政府、\n街道办事处\n审批意见'),
    ]
    for index, (key, label) in enumerate(labels):
        row = 11 + index
        put(row, 0, label, 9, 1)
        # 意见格按空表原文：示例意见 + (盖章) + 空白负责人/年月日，落款贴右下角
        grid[row][1] = [
            _p(APPROVAL_HEADS.get(key, ''), 9, 1),
            Spacer(1, 4),
            _p(APPROVAL_SEAL, 9, 1),
            Spacer(1, 10),
            _p(APPROVAL_SIGN, 9, 2),
        ]

    put(16, 1, '1.其他机构部门审批意见由各地根据实际情况进行添加；\n'
               '2.宅基地涉及占用耕地的，宅基地面积最高不超过170平方米：宅基地不涉及占用耕地的，\n'
               '宅基地面积最高不超过200平方米。', 9, 0)

    spans = [
        ('SPAN', (0, 0), (8, 0)),
        ('SPAN', (0, 1), (0, 3)),
        ('SPAN', (6, 1), (8, 1)),
        ('SPAN', (2, 2), (8, 2)),
        ('SPAN', (2, 3), (8, 3)),
        ('SPAN', (0, 4), (0, 10)),
        ('SPAN', (2, 4), (4, 4)), ('SPAN', (6, 4), (8, 4)),
        ('SPAN', (2, 5), (8, 5)),
        ('SPAN', (1, 6), (1, 7)),
        ('SPAN', (2, 6), (5, 6)), ('SPAN', (2, 7), (5, 7)),
        ('SPAN', (6, 6), (8, 9)),
        ('SPAN', (1, 8), (1, 9)), ('SPAN', (2, 8), (5, 9)),
        ('SPAN', (1, 10), (2, 10)), ('SPAN', (6, 10), (7, 10)),
    ]
    for row in range(11, 16):
        spans.append(('SPAN', (1, row), (8, row)))
    spans.append(('SPAN', (1, 16), (8, 16)))

    heights = [26.0] + [25.0] * 10 + [75.0] * 5 + [50.0]

    reason = _s(app.get('apply_reason'))
    need = _need_height(reason, sum(col[2:]), 10)
    if need > heights[3]:
        heights[3] = need

    body_width = sum(col[1:])
    for index, (key, _label) in enumerate(labels):
        row = 11 + index
        head = APPROVAL_HEADS.get(key, '')
        need = _need_height(head, body_width, 9) + 4 + 13 + 10 + 13 + 4
        if need > heights[row]:
            heights[row] = need

    heights = _fit_heights(heights, limit, 14.0)
    table = Table(grid, colWidths=col, rowHeights=heights, repeatRows=0)
    table.setStyle(TableStyle(
        spans + [
            ('GRID', (0, 0), (-1, -1), 0.6, '#000000'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('VALIGN', (1, 11), (8, 15), 'BOTTOM'),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]
    ))
    return table


def export_app_pdf(app):
    """返回生成好的 pdf 绝对路径，调用方负责清理临时目录。"""
    if app is None:
        raise ValueError('申请记录不存在')
    _ensure_font()

    tmp_dir = tempfile.mkdtemp(prefix='hb_pdf_')
    out_name = '宅基地建房申请_%s_%s.pdf' % (_s(app.get('owner_name')) or '未命名', _s(app.get('app_no')) or '')
    out_path = os.path.join(tmp_dir, out_name)

    left = 0.86875 * 72
    right = 0.822222 * 72
    top = 0.279166 * 72
    bottom = 0.70 * 72
    width = A4[0] - left - right
    limit = A4[1] - top - bottom

    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=left,
        rightMargin=right,
        topMargin=top,
        bottomMargin=bottom,
        title='宅基地建房申请_%s' % _s(app.get('owner_name')),
        author='人口通',
    )
    story = [
        _build_apply(app, width, limit),
        PageBreak(),
        _build_approval(app, width, limit),
    ]
    doc.build(story)
    return out_path




