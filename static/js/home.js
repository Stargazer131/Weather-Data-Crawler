//var value = document.querySelector('.value')
//var predict_weather = document.querySelector('.predict_weather')
//var temperature_feel = document.querySelector('.temperature_feel')
//var wind = document.querySelector('.wind')
//var rain = document.querySelector('.rain')
//var humidity = document.querySelector('.humidity')
//var pressure = document.querySelector('.pressure')
//var luminosity = document.querySelector('.luminosity')
//
//async function thaydoi() {
//  // var value = document.querySelector('.predict_weather')
//  // if (value) {
//  //     value.textContent = "nắng"
//  // }
//  let apiUrl = `https://api.openweathermap.org/data/2.5/weather?q=Hanoi&appid=9534cf23258721d78220e22b0dcb4860`
//
//  let data = await fetch(apiUrl).then(res => res.json())
//  console.log(data);
//
//  if (data.cod == 200) {
//    let temp = (data.main.temp - 273) - (data.main.temp - 273) % 1
//    value.innerText = temp
//    predict_weather.innerText = data.weather[0].main
//    let temp_feel = (data.main.feels_like - 273) - (data.main.feels_like - 273) % 1
//    temperature_feel.innerText = temp_feel
//    wind.innerText = data.wind.speed + " km/h"
//    rain.innerText = "(Mưa)" + " 10%"
//    humidity.innerText = data.main.humidity + " %"
//    pressure.innerText = data.main.pressure + " mbar"
//    luminosity.innerText = "1234" + " %"
//
//  } else {
//    content.classList.add('hide')
//  }
//}

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
thaydoi();