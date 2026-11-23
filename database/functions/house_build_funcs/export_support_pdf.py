"""宅基地建房“一户一档”附页：承诺书、成员证明、一户一宅、相邻意见、会议记录、公示。

这些附页与申请表/审批表一起导出为一份 PDF，已有申请数据自动带入；
申请人签字、机构盖章、相邻权利人和会议/公示信息保持空白，打印后手填。
"""

from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.platypus import PageBreak, Paragraph, Spacer, Table, TableStyle

from .export_app_pdf import (
    BUILD_TYPES,
    LAND_TYPES,
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


def _address(app):
    return _s(app.get('approval_address')) or _s(app.get('owner_hukou'))


def _header(label, title, size=17):
    return [
        _p(label, 9.5, 0, leading=14),
        Spacer(1, 10),
        _p(title, size, 1, leading=size * 1.55),
        Spacer(1, 18),
    ]


def _org_block(width, prefix='集体经济组织'):
    return [
        Spacer(1, 18),
        _p('%s%s（公章）' % (_BLANK * 8, prefix), 11, 2, leading=20),
        Spacer(1, 6),
        _p('年%s月%s日' % (_NB * 3, _NB * 3), 11, 2, leading=20),
    ]


def _sign_block(width, label):
    return [
        Spacer(1, 18),
        _p(label, 11, 2, leading=20),
        Spacer(1, 6),
        _p('年%s月%s日' % (_NB * 3, _NB * 3), 11, 2, leading=20),
    ]


def _commitment(app, width):
    group = _group_base(app)
    story = _header('材料2', '农村宅基地使用承诺书', 18)
    story += [
        _p(
            '因（1. 分户新建住房　2. 按照规划迁址新建住房　3. 原址改、扩、翻建住房　4. 其他）需要，\n'
            '本人申请在%s乡（镇、街道）%s村（社区）%s组用地建房，现郑重承诺：'
            % (_BLANK * 4, _BLANK * 4, _blank(group, 3)),
            11, leading=23,
        ),
        Spacer(1, 7),
        _p('本人为本集体经济组织成员，本人及家庭成员符合“一户一宅”申请条件，\n'
           '申请材料真实有效；', 11, leading=23, firstLineIndent=22),
        Spacer(1, 7),
        _p('宅基地和建房申请经批准后，我将严格按照批复位置和面积动工建设，\n'
           '在批准后%s月内建成并使用；' % (_BLANK * 3),
           11, leading=23, firstLineIndent=22),
        Spacer(1, 7),
        _p('新住房建设完成后，按照规定%s日内拆除旧房及其他地上建筑物，\n'
           '并无偿退出原有宅基地（或将原宅基地连带上物无偿交由本集体经济组织处置）。'
           % (_BLANK * 5),
           11, leading=23, firstLineIndent=22),
        Spacer(1, 7),
        _p('如有隐瞒或未履行承诺，本人愿承担一切经济和法律责任。', 11, leading=23, firstLineIndent=22),
    ]
    story += _sign_block(width, '承诺人：')
    return story


def _member_proof(app, width):
    group = _group_base(app)
    gender = _s(app.get('owner_gender')) or _gender_from_id(app.get('owner_id_card'))
    story = _header('材料5', '本集体经济组织成员证明（参考模板）', 16)
    story += [
        _p(
            '兹有%s乡（镇、街道）%s村（社区、组）%s组村民%s，性别：%s，'
            '身份证号：%s，□是　□否属于本集体经济组织成员，'
            '□是　□否享有本集体经济组织成员的权利并履行本集体经济组织成员的义务。'
            % (_BLANK * 3, _BLANK * 3, _blank(group, 3), _blank(app.get('owner_name'), 6),
               _gender_boxes(gender), _blank(app.get('owner_id_card'), 10)),
            11, leading=22, firstLineIndent=22,
        ),
        Spacer(1, 10),
        _p('情况属实，特此证明！', 11, leading=22, firstLineIndent=22),
    ]
    story += _org_block(width)
    return story


def _one_house_proof(app, width):
    group = _group_base(app)
    gender = _s(app.get('owner_gender')) or _gender_from_id(app.get('owner_id_card'))
    story = _header('材料6', '“一户一宅”证明（参考模板）', 16)
    story += [
        _p(
            '兹有%s乡（镇、街道）%s村（社区、组）%s组村民%s，性别：%s，'
            '身份证号：%s，经调查，该户符合“一户一宅”条件，无其他宅基地。'
            % (_BLANK * 3, _BLANK * 3, _blank(group, 3), _blank(app.get('owner_name'), 6),
               _gender_boxes(gender), _blank(app.get('owner_id_card'), 10)),
            11, leading=22, firstLineIndent=22,
        ),
        Spacer(1, 10),
        _p('情况属实，特此证明！', 11, leading=22, firstLineIndent=22),
    ]
    story += _org_block(width)
    return story


def _neighbor_section(index, direction, neighbor):
    return (
        '%d. %s年%s月%s日，通过□电话　□当面　□其他（填写具体方式）%s沟通方式'
        '征求了%s边户%s意见，其对该用地建房申请□有　□无异议，异议（如有）为%s。'
        % (index, _BLANK * 3, _BLANK * 2, _BLANK * 2, _BLANK * 5, direction,
           _blank(_neighbor_name(neighbor), 5), _BLANK * 6)
    )


def _neighbor_opinion(app, width):
    group = _group_base(app)
    story = _header('材料7', '征求相邻权利人意见情况（参考模板）', 15.5)
    story += [
        _p(
            '兹有申请人%s拟在%s乡（镇、街道）%s村（社区）%s组用地建房，\n'
            '建筑层数：%s层，长%s米，宽%s米，檐口高度%s米。\n'
            '所建房屋与相邻权利人保持适当间距，东%s米，南%s米，西%s米，北%s米。\n'
            '本集体经济组织已征求相邻权利人意见，有关情况如下。'
            % (_blank(app.get('owner_name'), 5), _BLANK * 4, _BLANK * 4, _blank(group, 3),
               _blank(app.get('floors'), 2), _BLANK * 3, _BLANK * 3,
               _blank(app.get('building_height'), 3), _BLANK * 2, _BLANK * 2, _BLANK * 2, _BLANK * 2),
            10.5, leading=20, firstLineIndent=21,
        ),
        Spacer(1, 7),
        _p(_neighbor_section(1, '东', app.get('east_to')), 10.5, leading=20, firstLineIndent=21),
        Spacer(1, 5),
        _p(_neighbor_section(2, '西', app.get('west_to')), 10.5, leading=20, firstLineIndent=21),
        Spacer(1, 5),
        _p(_neighbor_section(3, '北', app.get('north_to')), 10.5, leading=20, firstLineIndent=21),
        Spacer(1, 5),
        _p(_neighbor_section(4, '南', app.get('south_to')), 10.5, leading=20, firstLineIndent=21),
        Spacer(1, 8),
        _p('针对有关异议，本集体经济组织将在成员大会或者代表大会讨论形成意见。',
           10.5, leading=20, firstLineIndent=21),
    ]
    story += _org_block(width)
    return story


def _meeting_record(app, width):
    group = _group_base(app)
    area = _area_markup(app.get('apply_land_area'), 10.5)
    if not area:
        area = '%s m<super rise=2 size=6>2</super>' % (_BLANK * 4)
    reason = _s(app.get('apply_reason')).rstrip('。；;，,、 ')
    body = (
        '今天召开农村集体经济组织成员（代表）会议，审议本村村民（集体经济组织成员）%s的用地建房申请，'
        '申请事由：%s；申请面积%s。\n建房类型属于（原址翻建/改扩建/异址新建）%s，\n'
        '申请建房地块的四至界址：东至%s，西至%s，\n'
        '南至%s，北至%s。'
        % (escape(_blank(app.get('owner_name'), 5)), escape(_blank(reason, 6)),
           area, escape(_blank(_build_name(app), 3)), escape(_blank(app.get('east_to'), 3)),
           escape(_blank(app.get('west_to'), 3)), escape(_blank(app.get('south_to'), 3)),
           escape(_blank(app.get('north_to'), 3)))
    )
    story = _header('材料8', '农村集体经济组织成员（代表）会议记录（参考模板）', 15.5)
    story += [
        _p('时　　间：%s年%s月%s日' % (_BLANK * 3, _BLANK * 2, _BLANK * 2), 10.5, leading=20),
        _p('地　　点：%s' % (_BLANK * 18), 10.5, leading=20),
        _p('出席人员：（签字按手印）', 10.5, leading=20),
        Spacer(1, 4),
        _p('%s' % (_BLANK * 42), 10.5, leading=20),
        Spacer(1, 4),
        _p('主持人：%s　　记录人：%s' % (_BLANK * 8, _BLANK * 8), 10.5, leading=20),
        Spacer(1, 8),
        _raw_p(body, 10.5, leading=20, firstLineIndent=21),
        Spacer(1, 7),
        _raw_p(
            '会议研究了%s的建房申请，认为申请情况□是　□否属实，'
            '□是　□否符合条件及要求。'
            '相邻权利人□有　□无异议，异议（如有）□是　□否成立，'
            '□同意　□不同意通过，\n经张榜公示无异议后，报送上级审批。'
            % escape(_blank(app.get('owner_name'), 5)),
            10.5, leading=20, firstLineIndent=21,
        ),
    ]
    story += _org_block(width)
    return story


def _publicity_table(apps, width, pad_rows=0):
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
            _p(_s(_address(app)), 8.5, 1, leading=12),
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


def _publicity(apps, width, pad_rows=0):
    names = [_s(app.get('owner_name')) for app in apps]
    names_text = '、'.join(name for name in names if name) or (_BLANK * 5)
    story = _header('材料9', '农村集体经济组织成员（代表）大会审议情况公示（参考模板）', 15.5)
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
        _publicity_table(apps, width, pad_rows),
        Spacer(1, 10),
        _p('附：1. 农村集体经济组织成员（代表）会议记录；2. 征求相邻权利人意见情况。',
           10, leading=18),
    ]
    story += _org_block(width, '集体经济组织')
    return story


def _meeting_record_shared(apps, width):
    """多户共用一张会议记录：只列户名和户数，逐户明细见同批公示表。"""
    if len(apps) == 1:
        return _meeting_record(apps[0], width)

    names = [_s(app.get('owner_name')) for app in apps]
    names_text = '、'.join(name for name in names if name) or (_BLANK * 6)
    size = 10.5 if len(apps) <= 6 else 9.5
    body = (
        '今天召开农村集体经济组织成员（代表）会议，审议本村村民（集体经济组织成员）'
        '%s 共 %d 户的用地建房申请，各户申请事由、申请面积、建房类型及四至界址详见本次公示。'
        % (names_text, len(apps))
    )
    conclusion = (
        '会议对上述 %d 户的用地建房申请逐一进行了研究，认为申请情况□是　□否属实，'
        '□是　□否符合条件及要求。相邻权利人□有　□无异议，异议（如有）□是　□否成立，'
        '□同意　□不同意通过，公示无异议后报上级审批。' % len(apps)
    )
    story = _header('材料8', '农村集体经济组织成员（代表）会议记录（参考模板）', 15.5)
    story += [
        _p('时　　间：%s年%s月%s日' % (_BLANK * 3, _BLANK * 2, _BLANK * 2), size, leading=20),
        _p('地　　点：%s' % (_BLANK * 18), size, leading=20),
        _p('出席人员：（签字按手印）', size, leading=20),
        Spacer(1, 4),
        _p('%s' % (_BLANK * 42), size, leading=20),
        Spacer(1, 4),
        _p('主持人：%s　　记录人：%s' % (_BLANK * 8, _BLANK * 8), size, leading=20),
        Spacer(1, 8),
        _p(body, size, leading=20, firstLineIndent=21),
        Spacer(1, 7),
        _p(conclusion, size, leading=20, firstLineIndent=21),
    ]
    story += _org_block(width)
    return story


def build_household_support_story(app, width):
    """一户一表的前 4 张附页：承诺书、成员证明、一户一宅证明、相邻意见。"""
    forms = [
        _commitment(app, width),
        _member_proof(app, width),
        _one_house_proof(app, width),
        _neighbor_opinion(app, width),
    ]
    story = []
    for index, form in enumerate(forms):
        if index:
            story.append(PageBreak())
        story.extend(form)
    return story


def build_shared_support_story(apps, width):
    """多户共用附页：会议记录 1 张、公示 1 张（户数多时表格自动续页）。"""
    story = _meeting_record_shared(apps, width)
    story.append(PageBreak())
    story.extend(_publicity(apps, width, pad_rows=0))
    return story


def build_support_story(app, width):
    """返回 6 张附页（每张独立一页），由 export_app_pdf 追加在审批表之后。"""
    forms = [
        _commitment(app, width),
        _member_proof(app, width),
        _one_house_proof(app, width),
        _neighbor_opinion(app, width),
        _meeting_record(app, width),
        _publicity([app], width, pad_rows=2),
    ]
    story = []
    for index, form in enumerate(forms):
        if index:
            story.append(PageBreak())
        story.extend(form)
    return story
