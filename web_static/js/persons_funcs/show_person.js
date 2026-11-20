function showPerson(personId) {
    currentPersonId = personId;
    document.getElementById('personDetail').style.display = 'block';

    apiRequest('GET', `/api/person/${personId}`)
        .then(data => {
            const p = data.person || data;
            currentPersonUpdatedAt = p.updated_at || '';
            let html = `
                <div class="detail-item"><label>姓名</label><span>${p.name}</span></div>
                <div class="detail-item"><label>身份证号</label><span>${p.id_card}</span></div>
                <div class="detail-item"><label>户号</label><span>${p.hu_hao}</span></div>
                <div class="detail-item"><label>与户主关系</label><span>${p.relation}</span></div>
                <div class="detail-item"><label>年龄</label><span>${p.age}</span></div>
                <div class="detail-item"><label>电话</label><span>${p.phone === '无' ? '' : p.phone}</span></div>
                <div class="detail-item"><label>状态</label><span>${p.is_dead === '是' ? '已故' : (p.is_migrated === '是' ? '已迁出' : '正常')}</span></div>
                <div class="detail-item"><label>地址</label><span>${p.address || ''}</span></div>
                <div class="detail-item"><label>社保卡号1</label><span>${p.social_card1 === '无' ? '' : p.social_card1}</span></div>
                <div class="detail-item"><label>社保卡号2</label><span>${(p.social_card2 && p.social_card2 !== '无') ? p.social_card2 + (p.social_card2_source ? `（${p.social_card2_source}）` : '') : ''}</span></div>
                <div class="detail-item"><label>社保卡号3</label><span>${(p.social_card3 && p.social_card3 !== '无') ? p.social_card3 + (p.social_card3_source ? `（${p.social_card3_source}）` : '') : ''}</span></div>
                <div class="detail-item"><label>脱贫户</label><span>${p.poor_type === '无' ? '' : p.poor_type}</span></div>
                <div class="detail-item"><label>备注</label><span>${p.remark === '无' ? '' : p.remark}</span></div>
                <div class="detail-item"><label>残疾</label><span>${p.disability === '无' ? '' : p.disability}</span></div>
                ${p.disability === '是' ? `<div class="detail-item"><label>残疾类型</label><span>${p.disability_type === '无' ? '' : (p.disability_type || '')}</span></div><div class="detail-item"><label>残疾等级</label><span>${p.dis_level === '无' ? '' : (p.dis_level || '')}</span></div>` : ''}
                <div class="detail-item"><label>低保</label><span>${p.dibao === '无' ? '' : p.dibao}</span></div>
                <div class="detail-item"><label>计生家庭</label><span>${p.jisheng === '无' ? '' : p.jisheng}</span></div>
                <div class="detail-item"><label>特困供养</label><span>${p.tekun === '无' ? '' : (p.tekun || '')}</span></div>
                ${p.tekun === '是' ? `<div class="detail-item"><label>供养类型</label><span>${p.tekun_type === '无' ? '' : (p.tekun_type || '')}</span></div>` : ''}
                <div class="detail-item"><label>土地面积</label><span>${p.land_area || ''}</span></div>
                ${p.land_area_change_reason ? `<div class="detail-item"><label>土地变更原因</label><span>${p.land_area_change_reason}</span></div><div class="detail-item"><label>土地变更时间</label><span>${p.land_area_change_time}</span></div>` : ''}
                <div class="detail-item"><label>地方公益林</label><span>${p.local_welfare_forest_area || ''}</span></div>
                ${p.local_welfare_forest_change_reason ? `<div class="detail-item"><label>地方公益林变更原因</label><span>${p.local_welfare_forest_change_reason}</span></div><div class="detail-item"><label>地方公益林变更时间</label><span>${p.local_welfare_forest_change_time}</span></div>` : ''}
                <div class="detail-item"><label>国家公益林</label><span>${p.national_welfare_forest_area || ''}</span></div>
                ${p.national_welfare_forest_change_reason ? `<div class="detail-item"><label>国家公益林变更原因</label><span>${p.national_welfare_forest_change_reason}</span></div><div class="detail-item"><label>国家公益林变更时间</label><span>${p.national_welfare_forest_change_time}</span></div>` : ''}
                <div class="detail-item"><label>非国有天然商品林</label><span>${p.commercial_forest_area || ''}</span></div>
                ${p.commercial_forest_change_reason ? `<div class="detail-item"><label>非国有天然商品林变更原因</label><span>${p.commercial_forest_change_reason}</span></div><div class="detail-item"><label>非国有天然商品林变更时间</label><span>${p.commercial_forest_change_time}</span></div>` : ''}
            `;

            if (p.education) {
                html += `
                    <div class="detail-item" style="grid-column: span 2;"><label>就读信息</label></div>
                    <div class="detail-item"><label>学校</label><span>${p.education.school_name}</span></div>
                    <div class="detail-item"><label>年级</label><span>${p.education.grade}</span></div>
                    <div class="detail-item"><label>班级</label><span>${p.education.class_name}</span></div>
                    <div class="detail-item"><label>监护人</label><span>${p.education.guardian}</span></div>
                    <div class="detail-item"><label>监护人电话</label><span>${p.education.guardian_phone}</span></div>
                    <div class="detail-item"><label>留守儿童</label><span>${p.education.is_left_behind}</span></div>
                    <div class="detail-item"><label>学生状态</label><span>${p.education.student_status}</span></div>
                `;
            }

            document.getElementById('detailContent').innerHTML = html;
        });
}
