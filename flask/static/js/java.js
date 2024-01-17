document.addEventListener('DOMContentLoaded', function () {
  var projectCountElement = document.getElementById('projectCount');
  var projectCount = projectCountElement ? projectCountElement.getAttribute('data-count') : 0;
  var barCtx = document.getElementById('barchart_values').getContext('2d');

  function updateBarChart(projectCount) {
   
    var domainValues = ['Finance', 'HealthCare', 'Education', 'Energy', 'Technology'];

    var data = {
      labels: domainValues,
      datasets: [{
        label: 'Number of project to this domain',
        data: [8, projectCount, 5, 10, 12],  
        backgroundColor: 'rgba(3, 173, 242, 0.7)',
        borderColor: 'rgba(0, 0, 255, 1)',
        borderWidth: 1,
        hoverBackgroundColor: 'rgba(255, 255, 255, 1)',
        hoverBorderColor: 'rgba(0, 0, 255, 1)',
      }]
    };

    var options = {
      indexAxis: 'y',
      responsive: false,
      scales: {
        x: {
          beginAtZero: true,
          max: Math.max(...data.datasets[0].data) + 5, 
        },
        y: {
          beginAtZero: true,
        }
      },
      plugins: {
        legend: {
          display: false
        }
      },
      layout: {
        padding: {
          left: 0,
          right: 10,
          top: 10,
          bottom: 10
        }
      },
      barThickness: 20
    };

    var myBarChart = new Chart(barCtx, {
      type: 'bar',
      data: data,
      options: options
    });

    var circles = document.querySelectorAll('.circle');
    
    var fixedNumbers = [1, projectCount, 20];

    circles.forEach(function (circle, index) {
      var numberText = document.createElement('div');
      numberText.classList.add('circle-number');
      numberText.textContent = fixedNumbers[index];
      circle.innerHTML = ''; 
      circle.appendChild(numberText);
    });
  }

  updateBarChart(projectCount);
});
