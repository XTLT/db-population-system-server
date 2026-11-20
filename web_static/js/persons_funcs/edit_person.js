function editPerson() {
    if (!currentPersonId) return;

    apiRequest('GET', `/api/person/${currentPersonId}`)
        .then(data => {
            const p = data.person || data;
            currentPersonUpdatedAt = p.updated_at || '';
            document.getElementById('editId').value = p.id;
            document.getElementById('editIdCard').value = p.id_card;
            document.getElementById('editName').value = p.name;
            document.getElementById('editHuHao').value = p.hu_hao || '';
            document.getElementById('editRelation').value = p.relation || '';
            // 存量关系不在标准下拉选项时动态并入，避免编辑时丢失原值
            const relSel = document.getElementById('editRelation');
            let relFound = false;
            for (const opt of relSel.options) {
                if (opt.value === (p.relation || '')) { relFound = true; break; }
            }
            if (!relFound && p.relation) {
                relSel.add(new Option(p.relation, p.relation));
            }
            relSel.value = p.relation || '';
            document.getElementById('editIsDead').value = p.is_dead || '';
            document.getElementById('editPhone').value = (p.phone && p.phone !== '无') ? p.phone : '';
            document.getElementById('editAddress').value = (p.address && p.address !== '无') ? p.address : '';
            document.getElementById('editLandArea').value = p.land_area || '';
            currentPersonLandArea = p.land_area || '';
            document.getElementById('editLocalWelfareForest').value = p.local_welfare_forest_area || '';
            currentPersonLocalWelfareForest = p.local_welfare_forest_area || '';
            document.getElementById('editNationalWelfareForest').value = p.national_welfare_forest_area || '';
            currentPersonNationalWelfareForest = p.national_welfare_forest_area || '';
            document.getElementById('editCommercialForest').value = p.commercial_forest_area || '';
            currentPersonCommercialForest = p.commercial_forest_area || '';
            document.getElementById('editSocial1').value = (p.social_card1 && p.social_card1 !== '无') ? p.social_card1 : '';
            document.getElementById('editSocial2').value = (p.social_card2 && p.social_card2 !== '无') ? p.social_card2 + (p.social_card2_source ? `（${p.social_card2_source}）` : '') : '';
            document.getElementById('editSocial3').value = (p.social_card3 && p.social_card3 !== '无') ? p.social_card3 + (p.social_card3_source ? `（${p.social_card3_source}）` : '') : '';
            // 社保卡号2/3 仅由补贴导入自动回填，编辑框只读展示卡号+来源
            document.getElementById('editSocial2').readOnly = true;
            document.getElementById('editSocial3').readOnly = true;
            document.getElementById('editRemark').value = (p.remark && p.remark !== '无') ? p.remark : '';

            // 社会保障
            document.getElementById('editPoorType').value = (p.poor_type && p.poor_type !== '无') ? p.poor_type : '';

            const disValue = (p.disability && p.disability !== '无') ? p.disability : '';
            document.getElementById('editDisability').value = disValue;
            toggleDisabilityDetail();
            if (disValue === '是') {
                document.getElementById('editDisabilityType').value = (p.disability_type && p.disability_type !== '无') ? p.disability_type : '';
                document.getElementById('editDisLevel').value = (p.dis_level && p.dis_level !== '无') ? p.dis_level : '';
            }

            document.getElementById('editDibao').value = (p.dibao && p.dibao !== '无') ? p.dibao : '';
            document.getElementById('editJisheng').value = (p.jisheng && p.jisheng !== '无') ? p.jisheng : '';

            const tekunValue = (p.tekun && p.tekun !== '无') ? p.tekun : '';
            document.getElementById('editTekun').value = tekunValue;
            toggleTekunDetail();
            if (tekunValue === '是') {
                document.getElementById('editTekunType').value = (p.tekun_type && p.tekun_type !== '无') ? p.tekun_type : '';
            }

            // 就读信息
            document.getElementById('editEduSchool').value = p.education?.school_name || '';
            document.getElementById('editEduClass').value = p.education?.class_name || '';
            document.getElementById('editEduGuardian').value = p.education?.guardian || '';
            document.getElementById('editEduGuardianPhone').value = p.education?.guardian_phone || '';
            document.getElementById('editEduLeftBehind').value = p.education?.is_left_behind || '';
            document.getElementById('editEduStatus').value = p.education?.student_status || '';
            document.getElementById('editEduEnrollDate').value = p.education?.enrollment_date || '';
            document.getElementById('editEduGradDate').value = p.education?.graduation_date || '';
            document.getElementById('editEduGrade').value = p.education?.grade || '';

            // 添加年级变化监听，自动计算入学和毕业日期
            const gradeSelect = document.getElementById('editEduGrade');
            gradeSelect.onchange = function() {
                calculateEnrollmentAndGraduation();
            };

            document.getElementById('editModal').style.display = 'flex';
        });
}
