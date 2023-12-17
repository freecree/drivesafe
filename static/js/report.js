// Sample data (replace with your actual data)
const classData = {
  classes: ['Class A', 'Class B', 'Class C'],
  amounts: [10, 20, 15],
};

// Function to create the chart
function createChart() {
  const ctx = document.getElementById('myChart').getContext('2d');

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: chartData.map(item => item.description),
      datasets: [
        {
          label: 'Кількість відволікань',
          data: chartData.map(item => item.count / 20),
          backgroundColor: 'rgba(75, 192, 192, 0.2)', // Customize the chart colors
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

// Call the createChart function to generate the chart
createChart();
