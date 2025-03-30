
  function replaceWithTextBox(assessmentType) {
    document.querySelector(`#remark-form-${assessmentType} button`).style.display = 'none';
    document.querySelector(`#remark-textbox-${assessmentType}`).style.display = 'block';
  }
