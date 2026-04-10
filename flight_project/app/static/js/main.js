document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('flightSearchForm');
    const departureDateInput = document.getElementById('departure_date');
    const returnDateInput = document.getElementById('return_date');
    const typeSelect = document.getElementById('type');
    
    const today = new Date().toISOString().split('T')[0];
    departureDateInput.min = today;
    returnDateInput.min = today;
    
    function updateReturnDateVisibility() {
        const tripType = typeSelect.value;
        returnDateInput.parentElement.style.display = tripType === 'round_trip' ? 'block' : 'none';
        returnDateInput.required = tripType === 'round_trip';
    }
    
    typeSelect.addEventListener('change', updateReturnDateVisibility);
    updateReturnDateVisibility();

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const searchData = {
            origin: formData.get('origin'),
            destination: formData.get('destination'),
            departure_date: formData.get('departure_date'),
            return_date: formData.get('return_date') || null,
            passengers: parseInt(formData.get('passengers')),
            travel_class: formData.get('travel_class'),
            type: formData.get('type'),
            adults: parseInt(formData.get('passengers')),
            sort_by: formData.get('sort_by'),
            stops: formData.get('stops')
        };
        
        const resultsSection = document.getElementById('results');
        const resultsList = document.getElementById('resultsList');
        const priceChartSection = document.getElementById('priceChart');
        
        resultsList.innerHTML = '<div class="loading">搜索中...</div>';
        resultsSection.style.display = 'block';
        priceChartSection.style.display = 'none';
        
        try {
            const response = await fetch('/search', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(searchData)
            });
            
            const data = await response.json();
            
            if (data.flights && data.flights.length > 0) {
                resultsList.innerHTML = data.flights.map(flight => `
                    <div class="flight-card">
                        <div class="flight-info">
                            <div class="flight-route">
                                <span class="flight-number">${flight.flight_number}</span>
                                <span>${flight.airline_zh || flight.airline}</span>
                            </div>
                            <div class="stops-info">
                                ${flight.stops === 0 ? '直飞' : flight.stops + '次中转: ' + (flight.stops_airports || []).join(', ')}
                            </div>
                            <div class="flight-details">
                                <span>🕐 ${flight.departure_time} → ${flight.arrival_time}</span>
                                <span>⏱ ${flight.duration}小时</span>
                                <span>✈️ ${flight.aircraft}</span>
                            </div>
                        </div>
                        <div class="flight-price">
                            <div class="price-amount">
                                <span class="currency">€</span>${flight.price}
                            </div>
                            <div class="seats-info">剩余 ${flight.seats_available} 座</div>
                        </div>
                    </div>
                `).join('');
                
                loadPriceChart(searchData.departure_date);
            } else {
                resultsList.innerHTML = '<div class="error-message">未找到符合条件的航班</div>';
            }
        } catch (error) {
            resultsList.innerHTML = `<div class="error-message">搜索失败: ${error.message}</div>`;
        }
    });
    
    async function loadPriceChart(departureDate) {
        try {
            const response = await fetch(`/price-history?departure_date=${departureDate}`);
            const priceData = await response.json();
            
            const chartSection = document.getElementById('priceChart');
            chartSection.style.display = 'block';
            
            const ctx = document.getElementById('priceChartCanvas').getContext('2d');
            
            if (window.priceChartInstance) {
                window.priceChartInstance.destroy();
            }
            
            window.priceChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: priceData.map(d => d.date),
                    datasets: [{
                        label: '票价 (CNY)',
                        data: priceData.map(d => d.price),
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: true }
                    },
                    scales: {
                        y: { beginAtZero: false }
                    }
                }
            });
        } catch (error) {
            console.error('Price chart error:', error);
        }
    }
});
