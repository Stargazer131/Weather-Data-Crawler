//hiện thị time thực
function updateRealTime() {
  const currentTime = new Date();
  const options = { hour: '2-digit', minute: '2-digit', second: '2-digit' };
  const formattedTime = currentTime.toLocaleTimeString('vi-VN', options);
  document.getElementById('real_time').textContent = formattedTime;
}

// Cập nhật thời gian mỗi giây
setInterval(updateRealTime, 1000);

// Gọi hàm cập nhật ban đầu
updateRealTime();

//   hiện thị ngày
function updateCurrentDate() {
  const currentDate = new Date();
  const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
  const formattedDate = currentDate.toLocaleDateString('vi-VN', options);
  document.getElementById('current_date').textContent = formattedDate;
}

// Gọi hàm cập nhật ban đầu
updateCurrentDate();