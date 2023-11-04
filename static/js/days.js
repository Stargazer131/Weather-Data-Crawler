
function formatDate(date) {
    const day = date.getDate();
    const month = date.getMonth() + 1;
    const year = date.getFullYear();
    return `${day}.${month}.${year}`;
  }
  
  function updateCurrentDate() {
    const currentDate = new Date();
    const formattedDate = formatDate(currentDate);
    document.getElementById('current_date').textContent = formattedDate;
  }
  function formatNextDate(date) {
    const day = date.getDate()+1;
    const month = date.getMonth() + 1;
    const year = date.getFullYear();
    return `${day}.${month}.${year}`;
  }
  
  function updateNextDate() {
    const currentDate = new Date();
    const formattedDate = formatNextDate(currentDate);
    document.getElementById('next_date').textContent = formattedDate;
  }
  
  // Gọi hàm cập nhật ban đầu
  updateCurrentDate();
  updateNextDate();