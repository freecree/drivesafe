function groupDistractions(allDrivers) {
  const map = new Map();
  map.set('1', {descr: 'Користування телефоном', count: 0})
  map.set('2', {descr: 'Користування радіо', count: 0})
  map.set('3', {descr: 'Споживання напоїв', count: 0})
  map.set('4', {descr: 'Відволікання на речі позаду', count: 0})

  allDistractions.forEach(distraction => {
    const key = distraction.distracted_class;
    map.set(key, {...map.get(key), count: map.get(key).count+1})
  })
  return map;
}

function createChart() {
  const ctx = document.getElementById('myChart').getContext('2d');

  const chartData = groupDistractions(allDistractions);
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: Array.from(chartData).filter(item=>item[1].count > 0).map(item => item[1].descr),
      datasets: [
        {
          label: 'Кількість відволікань',
          data: Array.from(chartData).filter(item=>item[1].count > 0).map(item => item[1].count / drivingTimeMin),
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          borderColor: 'rgba(75, 192, 192, 1)',
          borderWidth: 1,
        },
      ],
    },
    responsive: false,  // Disable automatic resizing
    maintainAspectRatio: false, // Disable aspect ratio maintenance
    options: {
      scales: {
        y: {
          beginAtZero: true,
        },
      },
    },
  });
}

createChart();
