"""宅基地建房“一户一档”附页：承诺书、成员证明、一户一宅、相邻意见、会议记录、公示。

这些附页与申请表/审批表一起导出为一份 PDF，已有申请数据自动带入；
申请人签字、机构盖章、相邻权利人和会议/公示信息保持空白，打印后手填。
"""

import html
import re
from pathlib import Path

from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus.flowables import HRFlowable

from .export_app_pdf import (
    BUILD_TYPES,
    LAND_TYPES,
    _SignatureLine,
    _area_markup,
    _area_p,
    _ensure_font,
    _p,
    _pick,
    _raw_p,
    _s,
)

_NB = '\u00a0'
_BLANK = '＿'  # 全角下划线，打印后可直接手写

# 党政机关公文格式（GB/T 9704-2012）常用版式：
# 标题 2 号小标宋居中；正文 3 号仿宋，固定行距 28 磅，首行缩进 2 字。
_GW_TITLE_SIZE = 22
_GW_BODY_SIZE = 16
_GW_LEADING = 28
_GW_TOP_GAP = 85          # 现表框上边距约 20pt，补到约 37mm 版心上边距
_GW_BODY_INDENT = 16.85   # 左 28mm、右 26mm 版心的近似等距内缩（相对现表框）
_GW_TITLE_LEADING = 34

_GW_FONT_DIR = Path(__file__).resolve().parents[3] / 'house_build_templates'
_GW_FANGSONG = 'HBFangSong'
_GW_XIAOBIAOSONG = 'HBXiaoBiaoSong'
_gw_font_cache = None


def _gw_fonts():
    """公文正文用仿宋，标题用中宋（近似小标宋）；字体缺失时回退到原黑体。"""
    global _gw_font_cache
    if _gw_font_cache:
        return _gw_font_cache
    body = _ensure_font()
    title = _ensure_font()
    for name, filename in ((_GW_FANGSONG, 'simfang.ttf'),
                           (_GW_XIAOBIAOSONG, 'STZHONGS.TTF')):
        path = _GW_FONT_DIR / filename
        if path.exists():
            try:
                pdfmetrics.registerFont(TTFont(name, str(path)))
                if name == _GW_FANGSONG:
                    body = name
                else:
                    title = name
            except Exception:
                pass
    _gw_font_cache = (body, title)
    return _gw_font_cache



def _blank(value, width=6):
    text = _s(value)
    return text if text else _BLANK * width


def _gender_boxes(gender):
    value = _s(gender)
    if value == '男':
        return '■男%s%s□女' % (_NB, _NB)
    if value == '女':
        return '□男%s%s■女' % (_NB, _NB)
    return '□男%s%s□女' % (_NB, _NB)


def _gender_from_id(id_card):
    text = _s(id_card)
    try:
        if len(text) == 18:
            return '男' if int(text[16]) % 2 else '女'
        if len(text) == 15:
            return '男' if int(text[14]) % 2 else '女'
    except (TypeError, ValueError):
        pass
    return ''


def _group_base(app):
    """把“五八组/五八小组”归一成“五八”，后面统一补“组”字。"""
    text = _s(app.get('group_name'))
    for suffix in ('小组', '组'):
        if text.endswith(suffix):
            return text[:-len(suffix)]
    return text


def _neighbor_name(value):
    """四至里的“潘小勤土地/潘祥明竹林”只取权利人姓名，避免打印成“东边户潘小勤土地意见”。"""
    text = _s(value)
    core = text.rstrip('米㎡ ')
    if core.replace('.', '', 1).isdigit():
        return ''
    for suffix in ('土地', '竹林', '房屋', '房子', '林地', '菜地', '田地', '户'):
        if text.endswith(suffix) and len(text) > len(suffix):
            return text[:-len(suffix)]
    return text


def _member_count(app):
    members = app.get('members') or []
    owner_id = _s(app.get('owner_id_card'))
    if owner_id and any(_s(item.get('id_card')) == owner_id for item in members):
        return len(members)
    return 1 + len(members)


def _land_name(app):
    raw = _s(app.get('land_type')) or _s(app.get('approval_land_type'))
    return _pick(LAND_TYPES, raw) or raw


def _build_name(app):
    raw = _s(app.get('build_type')) or _s(app.get('approval_build_type'))
    return _pick(BUILD_TYPES, raw) or raw


COMMITMENT_REASONS = [
    (1, '分户新建住房'),
    (2, '按照规划迁址新建住房'),
    (3, '原址改、扩、翻建住房'),
    (4, '其他'),
]


def _commitment_reason_no(app):
    """承诺书“因（1~4）”按申请理由/建房类型自动选一项。

    申请表没有独立的分户/迁址字段，因此优先看申请理由中的关键词；
    理由没有明确信息时再按建房类型兜底：原址翻建、改扩建归到第 3 项，
    异址新建归到第 2 项（按照规划迁址新建）。
    """
    reason = _s(app.get('apply_reason'))
    if '分户' in reason:
        return 1
    if '迁址' in reason or '异址' in reason:
        return 2
    if '原址' in reason or '翻建' in reason or '改扩建' in reason or '扩建' in reason:
        return 3
    if '其他' in reason:
        return 4
    name = _build_name(app)
    if name in ('原址翻建', '改扩建'):
        return 3
    if name == '异址新建':
        return 2
    return 0


def _commitment_reason_options(app):
    selected = _commitment_reason_no(app)
    return '　'.join(
        '%d.%s%s' % (no, '√' if no == selected else '', name)
        for no, name in COMMITMENT_REASONS
    )


def _commitment_reason_parts(app):
    selected = _commitment_reason_no(app)
    return [
        '%d.%s%s' % (no, '√' if no == selected else '', name)
        for no, name in COMMITMENT_REASONS
    ]


_ADMIN_TOWNSHIP_SUFFIXES = ('街道', '镇', '乡')
_ADMIN_VILLAGE_SUFFIXES = ('社区', '村')


def _address(app):
    return _s(app.get('approval_address')) or _s(app.get('owner_hukou'))


def _export_value(info, key):
    return _s((info or {}).get(key))


def _admin_core(text, suffixes):
    value = _s(text)
    for suffix in suffixes:
        if value.endswith(suffix) and len(value) > len(suffix):
            return value[:-len(suffix)]
    return value


def _admin_markup(value, generic, blank_width, suffixes):
    """乡/村抬头：填了就用填的；没填就打印横线，便于手写。"""
    raw = _s(value)
    if not raw:
        return _BLANK * blank_width + generic
    if any(raw.endswith(suffix) for suffix in suffixes):
        return escape(raw)
    return escape(raw) + generic


def _admin_plain(value, generic, suffixes):
    raw = _s(value)
    if not raw:
        return ''
    if any(raw.endswith(suffix) for suffix in suffixes):
        return escape(raw)
    return escape(raw) + generic


def _strip_admin_prefix(text):
    """从档案地址开头剥掉乡镇/村，避免和表头横线重复。"""
    value = _s(text)
    for suffixes in (_ADMIN_TOWNSHIP_SUFFIXES, _ADMIN_VILLAGE_SUFFIXES):
        for suffix in suffixes:
            match = re.match(r'^([\u4e00-\u9fa5]{1,10}?%s)' % re.escape(suffix), value)
            if match:
                value = value[match.end():]
                break
    return value.lstrip(' \t　、,，-—')


def _household_address(app, info=None):
    """承诺书、成员证明、一户一宅、相邻意见统一复用申请表的“家庭住址”。

    用户填了乡镇/村时，把档案地址里重复的乡镇/村前缀剥掉，只保留组/门牌等详细地址。
    """
    detail = _address(app)
    for value, suffixes in (
        (_export_value(info, 'township'), _ADMIN_TOWNSHIP_SUFFIXES),
        (_export_value(info, 'village'), _ADMIN_VILLAGE_SUFFIXES),
    ):
        core = _admin_core(value, suffixes)
        if core and detail.startswith(core):
            detail = detail[len(core):]
            for suffix in suffixes:
                if detail.startswith(suffix):
                    detail = detail[len(suffix):]
                    break
    return _strip_admin_prefix(detail)


def _full_address(app, info=None):
    """公示表“建房地址”用完整地址；未填乡/村时保持原档案地址。"""
    township = _export_value(info, 'township')
    village = _export_value(info, 'village')
    if not township and not village:
        return _address(app)
    detail = _household_address(app, info)
    return ''.join([
        _admin_plain(township, '乡（镇、街道）', _ADMIN_TOWNSHIP_SUFFIXES),
        _admin_plain(village, '村（社区）', _ADMIN_VILLAGE_SUFFIXES),
        detail,
    ]) or _address(app)


def _header(label, title, size=17, gap_after=18, top_gap=0, gongwen=False):
    spacer = [Spacer(1, top_gap)] if top_gap else []
    if gongwen:
        body_font, title_font = _gw_fonts()
        return spacer + [
            _gw_p(label, 10.5, 0, leading=15, font=body_font),
            Spacer(1, 10),
            _gw_p(title, _GW_TITLE_SIZE, 1, leading=_GW_TITLE_LEADING, font=title_font),
            Spacer(1, gap_after),
        ]
    return spacer + [
        _p(label, 9.5, 0, leading=14),
        Spacer(1, 10),
        _p(title, size, 1, leading=size * 1.55),
        Spacer(1, gap_after),
    ]


def _org_block(width, prefix='集体经济组织', size=_GW_BODY_SIZE, gap=18):
    body_font, _ = _gw_fonts()
    return [
        Spacer(1, gap),
        _gw_p('%s%s（公章）' % (_BLANK * 8, prefix), size, 2,
              leading=_GW_LEADING, indent=_GW_BODY_INDENT, font=body_font),
        Spacer(1, 6),
        _gw_p('年%s月%s日' % (_NB * 3, _NB * 3), size, 2,
              leading=_GW_LEADING, indent=_GW_BODY_INDENT, font=body_font),
    ]


_OPEN_BRACKETS = '（《【「“‘'
_CLOSE_PUNCT = '，。；：、）》】」”’！？'
_FLOW_PHRASES = (
    '本集体经济组织成员', '本集体经济组织', '农村集体经济组织',
    '地上建筑物', '建筑物', '动工建设', '建成并使用', '申请条件', '申请情况',
    '原有宅基地', '无偿退出', '无偿交由', '交由', '用地建房', '建房申请', '郑重承诺',
    '保持适当间距', '适当间距', '形成意见', '道路', '异址新建', '原址翻建',
    '所建房屋',
    '分户新建住房', '按照规划迁址新建住房', '原址改、扩、翻建住房',
    '√原址改、扩、翻建住房', '本人申请在', '申请在',
    '有关情况如下', '讨论形成意见',
    '身份证号：', '申请事由', '申请面积', '建房类型', '用地建房',
    '建筑层数', '檐口高度', '相邻权利人', '成员大会', '代表大会',
    '填写具体方式', '沟通方式', '无异议', '异议为', '其他', '四至：', '记录如下',
)
_FLOW_TOKEN_RE = re.compile(
    '(?:' + '|'.join(re.escape(item) for item in sorted(_FLOW_PHRASES, key=len, reverse=True)) + r')|'
    r'（[^（）]{1,12}）|“[^”]{1,12}”|'
    r'[□■☑][\u4e00-\u9fa5]{1,3}|[□■☑][男女]|'
    r'(?:\d+\.)\s*(?:姓名：)[\u4e00-\u9fa5]{2,6}(?=[，。；、]|$|\s)|'
    r'(?:村民|户主|申请人|权利人|姓名：)[\u4e00-\u9fa5]{2,6}(?=[，。；、]|拟|$|\s)|'
    r'(?:东至|南至|西至|北至)[^，。；：]{2,14}(?=[，。；]|$)|'
    r'性别：[^\s，。；]*(?:\s*[□■☑][男女])?|'
    r'身份证号：[^\s，。；]*|'
    r'\d+(?:\.\d+)?\s*(?:平方米|m2|m²|㎡)|'
    r'\d+\.(?:√)?[^\s）＿，。；：]{0,12}|'
    r'[\u4e00-\u9fa5]{1,4}组|[\u4e00-\u9fa5]{1,4}(?:村|社区)|[\u4e00-\u9fa5]{1,4}(?:镇|乡|街道)|'
    r'[^\s（），。；：]{0,2}＿+[^\s（），。；：]{0,2}|'
    r'[A-Za-z0-9][A-Za-z0-9.．:：/+-]*|.',
    re.S,
)


def _gw_p(text, size=_GW_BODY_SIZE, align=0, leading=_GW_LEADING,
          first_line_indent=0, indent=0, font=None):
    """公文段落：仿宋正文、固定行距、首行缩进；标题另传中宋字体和居中。"""
    value = _s(text)
    font = font or _gw_fonts()[0]
    style = ParagraphStyle(
        'hb_gw_%s_%d_%d_%d' % (font, size, align, indent),
        fontName=font,
        fontSize=size,
        leading=leading,
        alignment=align,
        firstLineIndent=first_line_indent,
        leftIndent=indent,
        rightIndent=indent,
        wordWrap='LTR',
        splitLongWords=0,
    )
    return Paragraph(escape(value).replace('\n', '<br/>'), style)


def _pre_p(markup, size, align, leading, first_indent=0,
           first_line_indent=0, font=None):
    """已按字宽预排好的段落，禁止 ReportLab 再按 CJK 规则二次断行。"""
    font = font or _ensure_font()
    style = ParagraphStyle(
        'hb_pre_%s_%d_%d_%d_%d' % (font, size, align, first_indent, first_line_indent),
        fontName=font,
        fontSize=size,
        leading=leading,
        alignment=align,
        firstLineIndent=first_line_indent,
        leftIndent=first_indent,
        rightIndent=first_indent,
        wordWrap='LTR',
        splitLongWords=0,
    )
    return Paragraph(markup, style)


def _flow_p(text, size, leading, width, first_indent=28,
            first_line_indent=0, font=None, align=0):
    """按实际字宽排满一行再换行，避免手动断行留下大片空白。

    ReportLab 的 CJK 自动换行会把逗号、右括号放到下一行行首；这里先按字宽
    预排，并把标点粘回上一行，保证正文右侧基本齐平、标题仍在页面正中。
    公文正文由 `first_line_indent` 控制首行缩进 2 字，续行回到版心左边缘。
    """
    value = html.unescape(_s(text)).replace('\n', '')
    font = font or _ensure_font()
    if not value:
        return _pre_p('', size, align, leading, first_indent,
                      first_line_indent, font)
    safe_width = max(40.0, width - 16.0)
    units = _FLOW_TOKEN_RE.findall(value)
    lines = []
    current = []
    current_width = 0.0
    rest_available = safe_width - 2 * first_indent
    available = rest_available - first_line_indent
    first_line = True
    for unit in units:
        unit_width = pdfmetrics.stringWidth(unit, font, size)
        if current and current_width + unit_width > available:
            if unit[0] in _CLOSE_PUNCT:
                # 标点不能出现在行首：宁可让本行略超一点，也粘在上一行。
                current.append(unit)
                current_width += unit_width
                lines.append(''.join(current))
                current = []
                current_width = 0.0
                first_line = False
                available = rest_available
                continue
            carry = ''
            if current[-1] and current[-1][-1] in _OPEN_BRACKETS:
                carry = current[-1][-1]
                current[-1] = current[-1][:-1]
                current_width -= pdfmetrics.stringWidth(carry, font, size)
            elif current[-1] in ('：', ':') and len(current) >= 2:
                # 标签不能孤零零留在行尾，把“标签：”整体带到下一行。
                carry = current[-2] + current[-1]
                del current[-2:]
                current_width -= pdfmetrics.stringWidth(carry, font, size)
            elif current[-1].endswith(('：', ':')) and len(current[-1]) > 1:
                carry = current[-1]
                current.pop()
                current_width -= pdfmetrics.stringWidth(carry, font, size)
            lines.append(''.join(current)) if current else None
            current = [carry] if carry else []
            current_width = pdfmetrics.stringWidth(carry, font, size) if carry else 0.0
            first_line = False
            available = rest_available
        current.append(unit)
        current_width += unit_width
    if current:
        lines.append(''.join(current))

    # 后处理：右括号/逗号等仍落到行首时，粘回上一行；左括号留在行尾时移到下一行。
    for index in range(1, len(lines)):
        while lines[index] and lines[index][0] in _CLOSE_PUNCT:
            lines[index - 1] += lines[index][0]
            lines[index] = lines[index][1:]
    for index in range(len(lines) - 1):
        while lines[index] and lines[index][-1] in _OPEN_BRACKETS:
            char = lines[index][-1]
            lines[index] = lines[index][:-1]
            lines[index + 1] = char + lines[index + 1]

    # 行尾只剩“标签：”时，把标签带到下一行，和取值放在一起。
    for index in range(len(lines) - 1):
        line = lines[index]
        if line.endswith(('：', ':')):
            cut = max(line.rfind(char) for char in '；;，,、 ')
            label = line[cut + 1:]
            if cut >= 0 and len(label) > 1 and len(label) < 18:
                lines[index] = line[:cut + 1]
                lines[index + 1] = label + lines[index + 1]

    markup = '<br/>'.join(escape(line) for line in lines)
    return _pre_p(markup, size, align, leading, first_indent,
                  first_line_indent, font)


def _sign_block(width, label):
    return [
        Spacer(1, 18),
        _p(label, 11, 2, leading=20),
        Spacer(1, 6),
        _p('年%s月%s日' % (_NB * 3, _NB * 3), 11, 2, leading=20),
    ]


def _commitment(app, width, signature_path=None, info=None):
    body_font, _ = _gw_fonts()
    address = _household_address(app, info)
    township = _admin_markup(
        _export_value(info, 'township'), '乡（镇、街道）', 4, _ADMIN_TOWNSHIP_SUFFIXES,
    )
    village = _admin_markup(
        _export_value(info, 'village'), '村（社区）', 4, _ADMIN_VILLAGE_SUFFIXES,
    )
    story = _header('材料2', '农村宅基地使用承诺书', gap_after=28,
                    top_gap=_GW_TOP_GAP, gongwen=True)
    reasons = _commitment_reason_parts(app)
    story += [
        _flow_p(
            '因（%s　%s　%s　%s）需要，'
            '本人申请在%s%s%s用地建房，现郑重承诺：'
            % (reasons[0], reasons[1], reasons[2], reasons[3],
               township, village, _blank(address, 5)),
            _GW_BODY_SIZE, _GW_LEADING, width,
            first_indent=_GW_BODY_INDENT, first_line_indent=_GW_BODY_SIZE * 2,
            font=body_font,
        ),
        _flow_p('本人为本集体经济组织成员，本人及家庭成员符合“一户一宅”申请条件，'
                '申请材料真实有效；', _GW_BODY_SIZE, _GW_LEADING, width,
                first_indent=_GW_BODY_INDENT, first_line_indent=_GW_BODY_SIZE * 2,
                font=body_font),
        _flow_p('宅基地和建房申请经批准后，我将严格按照批复位置和面积动工建设，'
                '在批准后%s月内建成并使用；' % (_BLANK * 3),
                _GW_BODY_SIZE, _GW_LEADING, width,
                first_indent=_GW_BODY_INDENT, first_line_indent=_GW_BODY_SIZE * 2,
                font=body_font),
        _flow_p('新住房建设完成后，按照规定%s日内拆除旧房及其他地上建筑物，'
                '并无偿退出原有宅基地（或将原宅基地连带上物无偿交由'
                '本集体经济组织处置）。'
                % (_BLANK * 5),
                _GW_BODY_SIZE, _GW_LEADING, width,
                first_indent=_GW_BODY_INDENT, first_line_indent=_GW_BODY_SIZE * 2,
                font=body_font),
        _flow_p('如有隐瞒或未履行承诺，愿承担一切经济和法律责任。',
                _GW_BODY_SIZE, _GW_LEADING, width,
                first_indent=_GW_BODY_INDENT, first_line_indent=_GW_BODY_SIZE * 2,
                font=body_font),
    ]
    # 承诺人落款整体左移，给手写签名留出右侧空间；签名图直接套用申请表手签。
    story += [
        Spacer(1, 60),
        _SignatureLine('承诺人：', signature_path, '', size=_GW_BODY_SIZE,
                       image_height=38, start_ratio=0.70, font=body_font),
        Spacer(1, 8),
        _gw_p('年%s月%s日' % (_NB * 3, _NB * 3), _GW_BODY_SIZE, 2,
              leading=_GW_LEADING, indent=_GW_BODY_INDENT, font=body_font),
    ]
    return story


def _member_proof(app, width, info=None):
    body_font, _ = _gw_fonts()
    address = _household_address(app, info)
    township = _admin_markup(
        _export_value(info, 'township'), '乡（镇、街道）', 3, _ADMIN_TOWNSHIP_SUFFIXES,
    )
    village = _admin_markup(
        _export_value(info, 'village'), '村（社区、组）', 3, _ADMIN_VILLAGE_SUFFIXES,
    )
    gender = _s(app.get('owner_gender')) or _gender_from_id(app.get('owner_id_card'))
    story = _header('材料5', '本集体经济组织成员证明', gap_after=28,
                    top_gap=_GW_TOP_GAP, gongwen=True)
    story += [
        _flow_p(
            '兹有%s%s%s村民%s，性别：%s，身份证号：%s。'
            % (township, village, _blank(address, 5), _blank(app.get('owner_name'), 6),
               _gender_boxes(gender), _blank(app.get('owner_id_card'), 10)),
            _GW_BODY_SIZE, _GW_LEADING, width,
            first_indent=_GW_BODY_INDENT, first_line_indent=_GW_BODY_SIZE * 2,
            font=body_font,
        ),
        _flow_p('□是　□否属于本集体经济组织成员，□是　□否享有'
                '成员权利并履行成员义务。',
                _GW_BODY_SIZE, _GW_LEADING, width,
                first_indent=_GW_BODY_INDENT, first_line_indent=_GW_BODY_SIZE * 2,
                font=body_font),
        _flow_p('情况属实，特此证明！', _GW_BODY_SIZE, _GW_LEADING, width,
                first_indent=_GW_BODY_INDENT, first_line_indent=_GW_BODY_SIZE * 2,
                font=body_font),
    ]
    story += _org_block(width, size=_GW_BODY_SIZE, gap=120)
    return story


def _one_house_proof(app, width, info=None):
    body_font, _ = _gw_fonts()
    address = _household_address(app, info)
    township = _admin_markup(
        _export_value(info, 'township'), '乡（镇、街道）', 3, _ADMIN_TOWNSHIP_SUFFIXES,
    )
    village = _admin_markup(
        _export_value(info, 'village'), '村（社区、组）', 3, _ADMIN_VILLAGE_SUFFIXES,
    )
    gender = _s(app.get('owner_gender')) or _gender_from_id(app.get('owner_id_card'))
    story = _header('材料6', '“一户一宅”证明', gap_after=28,
                    top_gap=_GW_TOP_GAP, gongwen=True)
    story += [
        _flow_p(
            '兹有%s%s%s村民%s，性别：%s，身份证号：%s。'
            % (township, village, _blank(address, 5), _blank(app.get('owner_name'), 6),
               _gender_boxes(gender), _blank(app.get('owner_id_card'), 10)),
            _GW_BODY_SIZE, _GW_LEADING, width,
            first_indent=_GW_BODY_INDENT, first_line_indent=_GW_BODY_SIZE * 2,
            font=body_font,
        ),
        _flow_p('经调查，该户符合“一户一宅”条件，无其他宅基地。',
                _GW_BODY_SIZE, _GW_LEADING, width,
                first_indent=_GW_BODY_INDENT, first_line_indent=_GW_BODY_SIZE * 2,
                font=body_font),
        _flow_p('情况属实，特此证明！', _GW_BODY_SIZE, _GW_LEADING, width,
                first_indent=_GW_BODY_INDENT, first_line_indent=_GW_BODY_SIZE * 2,
                font=body_font),
    ]
    story += _org_block(width, size=_GW_BODY_SIZE, gap=120)
    return story


def _neighbor_section(index, direction, neighbor):
    return (
        '%d. %s年%s月%s日，通过□电话　□当面　□其他%s方式征求%s边户%s意见，'
        '其对该用地建房申请□有　□无异议，异议为%s。'
        % (index, _BLANK * 3, _BLANK * 2, _BLANK * 2, _BLANK * 5, direction,
           _blank(_neighbor_name(neighbor), 5), _BLANK * 6)
    )


def _neighbor_opinion(app, width, info=None):
    body_font, _ = _gw_fonts()
    address = _household_address(app, info)
    township = _admin_markup(
        _export_value(info, 'township'), '乡（镇、街道）', 4, _ADMIN_TOWNSHIP_SUFFIXES,
    )
    village = _admin_markup(
        _export_value(info, 'village'), '村（社区）', 4, _ADMIN_VILLAGE_SUFFIXES,
    )
    story = _header('材料7', '征求相邻权利人意见情况', gap_after=28,
                    top_gap=_GW_TOP_GAP, gongwen=True)
    body_kw = dict(
        first_indent=_GW_BODY_INDENT,
        first_line_indent=_GW_BODY_SIZE * 2,
        font=body_font,
    )
    lead = 27
    story += [
        _flow_p(
            '兹有申请人%s拟在%s%s%s用地建房，'
            '建筑层数：%s层，长%s米，宽%s米，檐口高度%s米。'
            '与相邻权利人保持适当间距，'
            '东%s米，南%s米，西%s米，北%s米。'
            '已征求意见，情况如下。'
            % (_blank(app.get('owner_name'), 5), township, village, _blank(address, 5),
               _blank(app.get('floors'), 2), _BLANK * 3, _BLANK * 3,
               _blank(app.get('building_height'), 3), _BLANK * 2, _BLANK * 2, _BLANK * 2, _BLANK * 2),
            _GW_BODY_SIZE, lead, width, **body_kw
        ),
        _flow_p(_neighbor_section(1, '东', app.get('east_to')),
                _GW_BODY_SIZE, lead, width, **body_kw),
        _flow_p(_neighbor_section(2, '西', app.get('west_to')),
                _GW_BODY_SIZE, lead, width, **body_kw),
        _flow_p(_neighbor_section(3, '北', app.get('north_to')),
                _GW_BODY_SIZE, lead, width, **body_kw),
        _flow_p(_neighbor_section(4, '南', app.get('south_to')),
                _GW_BODY_SIZE, lead, width, **body_kw),
        _flow_p('有异议的，提交成员大会或代表大会讨论形成意见。',
                _GW_BODY_SIZE, lead, width, **body_kw),
    ]
    story += _org_block(width, size=_GW_BODY_SIZE, gap=22)
    return story


def _meeting_value(meeting_info, key, blank_width):
    value = _s((meeting_info or {}).get(key))
    return value or (_BLANK * blank_width)


def _meeting_household_entry(index, app, size):
    """会议记录逐户条目：申请事由、申请面积、建房类型、四至界址。"""
    reason = _s(app.get('apply_reason')).rstrip('。；;，,、 ')
    area_value = _s(app.get('apply_land_area'))
    if area_value.endswith('.0'):
        area_value = area_value[:-2]
    area_value = re.sub(r'\s*(?:平方米|平米|m2|m²|㎡)\s*$', '', area_value,
                        flags=re.IGNORECASE).strip()
    area = '%s平方米' % (area_value or (_BLANK * 4))
    boundary = ('四至：东至%s，南至%s，西至%s，北至%s。'
                % (_blank(app.get('east_to'), 4),
                   _blank(app.get('south_to'), 4),
                   _blank(app.get('west_to'), 4),
                   _blank(app.get('north_to'), 4)))
    return (
        '%d. 姓名：%s；申请事由：%s；申请面积：%s；建房类型：%s；%s'
        % (index, _blank(app.get('owner_name'), 6),
           _blank(reason, 8), area, _blank(_build_name(app), 4),
           boundary)
    )


def _meeting_story(apps, width, meeting_info=None):
    body_font, _ = _gw_fonts()
    apps = [app for app in (apps or []) if app]
    if not apps:
        raise ValueError('会议记录至少需要一条建房申请')
    names = [_s(app.get('owner_name')) for app in apps]
    names_text = '、'.join(name for name in names if name) or (_BLANK * 6)
    count = len(apps)
    # 单户按 3 号仿宋；多户时逐级缩小字号以保证一张会议记录能容纳全部户数。
    if count == 1:
        size = _GW_BODY_SIZE
        leading = _GW_LEADING
    elif count <= 3:
        size = 13.5
        leading = 24
    elif count <= 6:
        size = 12
        leading = 21
    elif count <= 20:
        size = 10.5
        leading = 18.5
    else:
        size = 9.5
        leading = 17
    first_line = size * 2

    if count == 1:
        intro = (
            '今天召开农村集体经济组织成员（代表）会议，'
            '审议本村村民（集体经济组织成员）%s的用地建房申请。'
            '现将申请事由、申请面积、建房类型及四至记录如下：'
            % names_text
        )
    else:
        intro = (
            '今天召开农村集体经济组织成员（代表）会议，'
            '审议本村村民（集体经济组织成员）共 %d 户的用地建房申请。'
            '现将各户申请事由、申请面积、建房类型及四至逐一记录如下：'
            % count
        )

    conclusion = (
        '会议研究了%s的建房申请，认为申请情况□是　□否属实，'
        '□是　□否符合条件及要求。'
        '相邻权利人□有　□无异议，异议（如有）□是　□否成立，'
        '□同意　□不同意通过，经张榜公示无异议后，报送上级审批。' % escape(names_text)
        if count == 1 else
        '会议对上述 %d 户的用地建房申请逐一进行了研究，'
        '认为申请情况□是　□否属实，□是　□否符合条件及要求。'
        '相邻权利人□有　□无异议，异议（如有）□是　□否成立，'
        '□同意　□不同意通过，公示无异议后报上级审批。' % count
    )

    meeting_date = _meeting_value(meeting_info, 'date', 0)
    if meeting_date:
        date_line = '时　　间：%s' % meeting_date
    else:
        date_line = '时　　间：%s年%s月%s日' % (_BLANK * 3, _BLANK * 2, _BLANK * 2)

    story = _header('材料8', '农村集体经济组织成员（代表）会议记录',
                    gap_after=28, top_gap=_GW_TOP_GAP, gongwen=True)
    story += [
        _gw_p(date_line, size, 0, leading=leading, indent=_GW_BODY_INDENT,
              font=body_font),
        _gw_p('地　　点：%s' % _meeting_value(meeting_info, 'place', 18),
              size, 0, leading=leading, indent=_GW_BODY_INDENT, font=body_font),
        _gw_p('出席人员：（签字按手印）', size, 0, leading=leading,
              indent=_GW_BODY_INDENT, font=body_font),
        Spacer(1, 4),
        HRFlowable(width=width - 2 * _GW_BODY_INDENT, thickness=0.7,
                   color=colors.black, hAlign='CENTER',
                   spaceBefore=2, spaceAfter=6),
        Spacer(1, 4),
        _gw_p('主持人：%s　　记录人：%s'
              % (_meeting_value(meeting_info, 'host', 8),
                 _meeting_value(meeting_info, 'recorder', 8)),
              size, 0, leading=leading, indent=_GW_BODY_INDENT, font=body_font),
        Spacer(1, 6),
        _flow_p(intro, size, leading, width,
                first_indent=_GW_BODY_INDENT, first_line_indent=first_line,
                font=body_font),
    ]
    entry_width = width - 42 if size < 16 else width
    for index, app in enumerate(apps, 1):
        story.append(KeepTogether([
            _flow_p(
                _meeting_household_entry(index, app, size),
                size, leading, entry_width,
                first_indent=_GW_BODY_INDENT, first_line_indent=first_line,
                font=body_font,
            ),
        ]))
    story += [
        Spacer(1, 2),
        _flow_p(conclusion, size, leading, width,
                first_indent=_GW_BODY_INDENT, first_line_indent=first_line,
                font=body_font),
    ]
    story += _org_block(width, size=size, gap=38)
    return story


def _meeting_record(app, width, meeting_info=None):
    return _meeting_story([app], width, meeting_info)


def _publicity_table(apps, width, pad_rows=0, info=None):
    header = [
        _p(text, 8.5, 1, leading=12)
        for text in ('姓名', '在册人口', '占地面积', '地类', '建房地址', '建筑面积', '建筑层数', '性质')
    ]
    rows = [header]
    for app in apps:
        rows.append([
            _p(_s(app.get('owner_name')), 8.5, 1, leading=12),
            _p(str(_member_count(app)), 8.5, 1, leading=12),
            _area_p(app.get('apply_land_area'), 8.5, 1) or '',
            _p(_s(_land_name(app)), 8.5, 1, leading=12),
            _p(_full_address(app, info), 8.5, 1, leading=12),
            _area_p(app.get('building_area'), 8.5, 1) or '',
            _p(_s(app.get('floors')), 8.5, 1, leading=12),
            _p(_s(_build_name(app)), 8.5, 1, leading=12),
        ])
    for _ in range(pad_rows):
        rows.append(['', '', '', '', '', '', '', ''])

    ratios = (0.10, 0.09, 0.12, 0.16, 0.21, 0.12, 0.10, 0.10)
    widths = [width * r for r in ratios]
    heights = [30] + [34] * (len(rows) - 1)
    table = Table(rows, colWidths=widths, rowHeights=heights, repeatRows=1, splitByRow=1)
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.6, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F2F2F2')),
        ('FONTSIZE', (0, 0), (-1, 0), 8.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    return table


def _publicity(apps, width, pad_rows=0, info=None):
    names = [_s(app.get('owner_name')) for app in apps]
    names_text = '、'.join(name for name in names if name) or (_BLANK * 5)
    story = _header('材料9', '农村集体经济组织成员（代表）大会审议情况公示', 15.5)
    story += [
        _p(
            '经农村集体经济组织成员（代表）大会审议决定，拟同意上报%s等 %d 户的用地建房申请。'
            '为方便群众监督，对建房户情况进行张榜公示，公示期满无异议或异议理由不成立的，报上级审批。'
            % (names_text, len(apps)),
            10.5, leading=20, firstLineIndent=21,
        ),
        Spacer(1, 6),
        _p('一、公示时间（不少于5日）%s年%s月%s日至%s年%s月%s日止。'
           % (_BLANK * 3, _BLANK * 2, _BLANK * 2, _BLANK * 3, _BLANK * 2, _BLANK * 2),
           10.5, leading=20),
        _p('二、反馈方式　　联系电话：%s' % (_BLANK * 12), 10.5, leading=20),
        _p('三、公示内容', 10.5, leading=20),
        Spacer(1, 4),
        _publicity_table(apps, width, pad_rows, info=info),
        Spacer(1, 10),
        _p('附：1. 农村集体经济组织成员（代表）会议记录；2. 征求相邻权利人意见情况。',
           10, leading=18),
    ]
    story += _org_block(width, '集体经济组织')
    return story


def _meeting_record_shared(apps, width, meeting_info=None):
    """多户共用会议记录：逐户写明申请事由、面积、建房类型、四至。"""
    return _meeting_story(apps, width, meeting_info)


def build_household_support_story(app, width, signature_path=None, info=None):
    """一户一表的前 4 张附页：承诺书、成员证明、一户一宅证明、相邻意见。"""
    forms = [
        _commitment(app, width, signature_path, info),
        _member_proof(app, width, info),
        _one_house_proof(app, width, info),
        _neighbor_opinion(app, width, info),
    ]
    story = []
    for index, form in enumerate(forms):
        if index:
            story.append(PageBreak())
        story.extend(form)
    return story


def build_shared_support_story(apps, width, meeting_info=None):
    """多户共用附页：会议记录 1 张、公示 1 张（户数多时表格自动续页）。"""
    story = _meeting_record_shared(apps, width, meeting_info)
    story.append(PageBreak())
    story.extend(_publicity(apps, width, pad_rows=0, info=meeting_info))
    return story


def build_support_story(app, width, signature_path=None, meeting_info=None):
    """返回 6 张附页（每张独立一页），由 export_app_pdf 追加在审批表之后。"""
    forms = [
        _commitment(app, width, signature_path, meeting_info),
        _member_proof(app, width, meeting_info),
        _one_house_proof(app, width, meeting_info),
        _neighbor_opinion(app, width, meeting_info),
        _meeting_record(app, width, meeting_info),
        _publicity([app], width, pad_rows=2, info=meeting_info),
    ]
    story = []
    for index, form in enumerate(forms):
        if index:
            story.append(PageBreak())
        story.extend(form)
    return story

