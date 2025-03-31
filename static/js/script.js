
function openRemarkForm(assessmentType) {
  const form = document.getElementById(`remark-form-${assessmentType}`);
  if (form) {
    form.style.display = 'block';
  }
}

function closeRemarkForm(assessmentType) {
  const form = document.getElementById(`remark-form-${assessmentType}`);
  if (form) {
    form.style.display = 'none';
  }
}