# -*- coding: utf-8 -*-
"""server 端身份证 / 电话校验回归测试（标准库 unittest，零外部依赖）。

运行方式（在 server 仓库根目录）：
    python -m unittest discover -s tests -v

口径基准就是本仓库的 utils/common/validate_id_card.py、validate_phone.py；
用例与 desktop 的 tests/test_validators.py、mobile 的 test/utils/validators_test.dart 保持一致，
三端任一口径漂移，这里就会红。

说明：这两个模块是纯函数（只依赖 re / datetime），这里按文件路径直接加载，
避免 import utils 包时连带引入数据库、Flask 等重量级依赖。
"""

import importlib.util
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _load(name, *parts):
    path = os.path.join(ROOT, *parts)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_validate_id_card = _load("srv_validate_id_card", "utils", "common", "validate_id_card.py").validate_id_card
_validate_phone = _load("srv_validate_phone", "utils", "common", "validate_phone.py").validate_phone

WEIGHTS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
CHECK_CODES = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']

PHONE_ERR = "电话号码格式无效，请输入11位手机号"


def make_id(prefix17):
    """补齐正确校验位，构造校验位一定合法的号码，用于单独测出生日期分支。"""
    total = sum(int(prefix17[i]) * WEIGHTS[i] for i in range(17))
    return prefix17 + CHECK_CODES[total % 11]


class TestValidateIdCard(unittest.TestCase):
    def assert_ok(self, value):
        self.assertEqual(_validate_id_card(value), (True, ""))

    def assert_bad(self, value, msg):
        ok, actual = _validate_id_card(value)
        self.assertFalse(ok, f"{value!r} 应被判为非法")
        self.assertEqual(actual, msg, f"{value!r} 的提示文案与基准不一致")

    def test_valid_18_digit(self):
        self.assert_ok(make_id('52032519900101123'))
        self.assert_ok('11010519491231002X')
        self.assert_ok(make_id('52032519920229123'))

    def test_15_digit_rejected(self):
        self.assert_bad('110105491231002', "身份证号必须为18位")
        self.assert_bad('520325900101123', "身份证号必须为18位")

    def test_wrong_check_digit(self):
        valid = make_id('52032519900101123')
        wrong = valid[:-1] + ('0' if valid[-1] != '0' else '1')
        self.assert_bad(wrong, "身份证号校验位错误")

    def test_birth_date_invalid_but_check_digit_ok(self):
        self.assert_bad(make_id('52032519901301123'), "身份证号出生月份无效")
        self.assert_bad(make_id('52032519900001123'), "身份证号出生月份无效")
        self.assert_bad(make_id('52032519900230123'), "身份证号出生日期无效")
        self.assert_bad(make_id('52032519900229123'), "身份证号出生日期无效")
        self.assert_bad(make_id('52032519900431123'), "身份证号出生日期无效")
        self.assert_bad(make_id('52032519900100123'), "身份证号出生日期无效")
        self.assert_bad(make_id('52032518000101123'), "身份证号出生年份无效")
        self.assert_bad(make_id('52032520990101123'), "身份证号出生年份无效")

    def test_empty_after_clean(self):
        self.assert_bad('', "身份证号不能为空")
        self.assert_bad(None, "身份证号不能为空")
        self.assert_bad('     ', "身份证号不能为空")
        self.assert_bad('\t\n ', "身份证号不能为空")

    def test_format_errors(self):
        self.assert_bad('52032519900101123A', "身份证号最后一位必须为数字或X")
        self.assert_bad('5203A5199001011234', "身份证号前17位必须为数字")
        self.assert_bad(make_id('52032519900101123')[:17], "身份证号必须为18位")
        self.assert_bad(make_id('52032519900101123') + '1', "身份证号必须为18位")

    def test_whitespace_tolerated(self):
        # 关键：中间带空格 / 制表符与 desktop、mobile 一致通过（此前 server 只 strip，会误拒）
        valid = '520325199001011235'
        self.assert_ok('  ' + valid + '  ')
        self.assert_ok('5203 2519 9001 0112 35')
        self.assert_ok(valid[:10] + '\t' + valid[10:])

    def test_lowercase_x_normalized(self):
        self.assert_ok('11010519491231002x')


class TestValidatePhone(unittest.TestCase):
    def test_empty_allowed(self):
        self.assertEqual(_validate_phone(''), (True, ""))
        self.assertEqual(_validate_phone(None), (True, ""))
        self.assertEqual(_validate_phone('   '), (True, ""))
        self.assertEqual(_validate_phone('\t\n'), (True, ""))

    def test_mobile_valid(self):
        for p in ('13800138000', '15012345678', '19912345678', '13456789012'):
            self.assertEqual(_validate_phone(p), (True, ""), p)

    def test_mobile_invalid(self):
        # 关键：12345678901 虽以 1 开头且 11 位，但第 2 位不是 3-9，必须拒
        #（此前 server 只判 "1 开头 + 11 位"，会放行假号段）
        for p in ('12345678901', '10012345678', '12800138000', '1380013800',
                  '138001380001', '123456789012', 'abcdefghijk', '02345678901'):
            self.assertEqual(_validate_phone(p), (False, PHONE_ERR), p)

    def test_landline_rejected(self):
        # 关键：座机不再放行（此前 server 还保留两种座机格式）
        for p in ('010-12345678', '0755-87654321', '08511234567', '0851-12345678',
                  '0851-1234567-1234'):
            self.assertEqual(_validate_phone(p), (False, PHONE_ERR), p)

    def test_whitespace_tolerated(self):
        self.assertEqual(_validate_phone(' 13800138000 '), (True, ""))
        self.assertEqual(_validate_phone('138 0013 8000'), (True, ""))
        self.assertEqual(_validate_phone('138\t0013\t8000'), (True, ""))

    def test_hyphon_tolerated(self):
        # 清洗阶段剔除 "-"，号码本身合法就放行
        self.assertEqual(_validate_phone('138-0013-8000'), (True, ""))


VECTOR_FILE = os.path.join(ROOT, "tests", "vectors", "validation_vectors.json")


class TestSharedVectors(unittest.TestCase):
    """三端共享向量 validation_vectors.json 的逐条比对。

    权威源在本仓库 tests/vectors/，由 sync_vectors.py 复制到 desktop/tests/vectors
    与 mobile/test/vectors，三份 sha256 必须一致。任一端口径漂移，三端各自这一组就会红。
    """

    @classmethod
    def setUpClass(cls):
        with open(VECTOR_FILE, encoding="utf-8") as f:
            cls.doc = json.load(f)

    def test_id_card_vectors(self):
        self.assertTrue(self.doc["id_card"], "身份证向量为空")
        for case in self.doc["id_card"]:
            with self.subTest(note=case["note"], value=case["input"]):
                self.assertEqual(
                    _validate_id_card(case["input"]),
                    (case["valid"], case["msg"]),
                    case["note"],
                )

    def test_phone_vectors(self):
        self.assertTrue(self.doc["phone"], "电话向量为空")
        for case in self.doc["phone"]:
            with self.subTest(note=case["note"], value=case["input"]):
                self.assertEqual(
                    _validate_phone(case["input"]),
                    (case["valid"], case["msg"]),
                    case["note"],
                )


if __name__ == '__main__':
    unittest.main()
