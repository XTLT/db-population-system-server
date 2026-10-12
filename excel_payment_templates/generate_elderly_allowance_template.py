from ._write_template import _write_template
from ._constants import ELDERLY_ALLOWANCE_COLUMNS

_ELDERLY_TITLE = "____年__月高龄补贴发放花名册"
_ELDERLY_DESC = ("填表说明：红色列为为必填项，蓝色为非必填项，可以为空，但是一旦填写则必须经过校验。"
                 "身份证只能为18位，折号只能为大于18位的数，卡号为15到18位，区划地址必须与系统相同。")
# 第3行标签：列2 享受人姓名 / 列3 享受人身份证 / 列6 “一卡通”包含折、卡 / 列11 打款人姓名 / 列12 打款人身份证
_ELDERLY_LABEL_ROW = {
    2: "享受人姓名", 3: "享受人身份证", 6: '"一卡通"包含折、卡',
    11: "打款人姓名", 12: "打款人身份证",
}


def generate_elderly_allowance_template(path):
    _write_template(
        path, "发放资金花名册", ELDERLY_ALLOWANCE_COLUMNS,
        title_text=_ELDERLY_TITLE, desc_text=_ELDERLY_DESC, label_row=_ELDERLY_LABEL_ROW,
    )
