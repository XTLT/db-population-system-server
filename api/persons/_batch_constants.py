# 批量操作限制
MAX_BATCH_DELETE_COUNT = 100  # 单次最大删除数量
MAX_BATCH_UPDATE_COUNT = 200  # 单次最大更新数量

# 允许批量更新的字段白名单
BATCH_UPDATE_ALLOWED_FIELDS = {
    'relation', 'phone', 'address', 'remark', 
    'disability', 'dis_level', 'dibao', 'tekun', 'tekun_type', 'jisheng',
    'social_card1', 'land_area',
    'local_welfare_forest_area', 'national_welfare_forest_area', 'commercial_forest_area'
}
