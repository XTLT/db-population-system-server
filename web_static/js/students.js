










document.getElementById('eduEditForm').onsubmit = function(e) {
    e.preventDefault();
    const personId = document.getElementById('eduPersonId').value;
    const data = {
        school_name: document.getElementById('eduSchool').value.trim(),
        grade: document.getElementById('eduGrade').value,
        class_name: document.getElementById('eduClass').value.trim(),
        guardian: document.getElementById('eduGuardian').value.trim(),
        guardian_phone: document.getElementById('eduGuardianPhone').value.trim(),
        is_left_behind: document.getElementById('eduLeftBehind').value,
        student_status: document.getElementById('eduStatus').value,
        enrollment_date: document.getElementById('eduEnrollDate').value
    };

    fetch(`/api/person/${personId}/education`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(result => {
        if (result.success) {
            closeEduEdit();
            searchStudents();
        } else {
            alert(result.error || '保存失败');
        }
    })
    .catch(err => alert('保存失败：' + err.message));
};
