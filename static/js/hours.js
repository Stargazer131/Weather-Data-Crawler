
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

function updateCurrentHour() {
  // Tạo một đối tượng Date để lấy thời gian hiện tại
  var now = new Date();
  // Thêm 1 giờ (3600000 milliseconds) vào thời gian hiện tại
  var oneHourLater = new Date(now.getTime() + 3600000);
  // Lấy giờ và phút của thời gian mới
  var hour = oneHourLater.getHours();
  var minute = "00";
  // Đảm bảo rằng giờ luôn được hiển thị dưới dạng hai chữ số
  if (hour < 10) {
    hour = "0" + hour;
  }
  // Tạo chuỗi kết quả theo định dạng "hour:00"
  var formattedTime = hour + ":" + minute;
  // Hiển thị thời gian mới
  document.getElementById('next_hour').textContent = formattedTime;

}

// Gọi hàm cập nhật ban đầu
updateCurrentDate();
updateCurrentHour();