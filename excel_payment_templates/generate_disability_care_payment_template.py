from ._write_template import _write_template
from ._constants import DISABILITY_CARE_PAYMENT_COLUMNS

_CARE_TITLE = "____年__月重度残疾人护理补贴发放花名册"
_CARE_DESC = ("填表说明：红色列为为必填项，蓝色为非必填项，可以为空，但是一旦填写则必须经过校验。"
              "身份证只能为18位，折号只能为大于18位的数，卡号为15到18位，区划地址必须与系统相同，"
              "代持代管(是，否)。")
# 第3行标签：列5 “一卡通”包含折、卡；列10 单位:元
_CARE_LABEL_ROW = {5: '"一卡通"包含折、卡', 10: "单位:元"}


def generate_disability_care_payment_template(path):
    _write_template(
        path, "资金花名册", DISABILITY_CARE_PAYMENT_COLUMNS,
        title_text=_CARE_TITLE, desc_text=_CARE_DESC, label_row=_CARE_LABEL_ROW,
    )
