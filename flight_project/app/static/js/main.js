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
                resultsList.innerHTML = data.flights.map(flight => {
                    const outboundSegments = (flight.outbound_flights || []).map(seg => {
                        const hours = Math.floor(seg.duration / 60);
                        const mins = seg.duration % 60;
                        return `
                        <div class="flight-segment outbound">
                            <div class="segment-header">
                                <span class="segment-label">去程</span>
                                <img src="${seg.airline_logo || ''}" alt="${seg.airline}" class="segment-airline-logo" onerror="this.style.display='none'">
                                <span>${seg.airline}</span>
                                <span class="segment-flight-num">${seg.flight_number}</span>
                            </div>
                            <div class="segment-details">
                                <div class="segment-time">
                                    <span>${seg.departure_time}</span>
                                    <span class="seg-arrow">→</span>
                                    <span>${seg.arrival_time}</span>
                                </div>
                                <div class="segment-airport">
                                    <span>${seg.departure_airport}</span>
                                    <span>${seg.arrival_airport}</span>
                                </div>
                                <div class="segment-duration">${hours}h ${mins}min</div>
                            </div>
                        </div>
                        `;
                    }).join('');
                    
                    const returnSegments = (flight.return_flights || []).map(seg => {
                        const hours = Math.floor(seg.duration / 60);
                        const mins = seg.duration % 60;
                        return `
                        <div class="flight-segment return">
                            <div class="segment-header">
                                <span class="segment-label">返程</span>
                                <img src="${seg.airline_logo || ''}" alt="${seg.airline}" class="segment-airline-logo" onerror="this.style.display='none'">
                                <span>${seg.airline}</span>
                                <span class="segment-flight-num">${seg.flight_number}</span>
                            </div>
                            <div class="segment-details">
                                <div class="segment-time">
                                    <span>${seg.departure_time}</span>
                                    <span class="seg-arrow">→</span>
                                    <span>${seg.arrival_time}</span>
                                </div>
                                <div class="segment-airport">
                                    <span>${seg.departure_airport}</span>
                                    <span>${seg.arrival_airport}</span>
                                </div>
                                <div class="segment-duration">${hours}h ${mins}min</div>
                            </div>
                        </div>
                        `;
                    }).join('');
                    
                    const outboundDuration = flight.total_duration || 0;
                    const returnDuration = flight.return_duration || 0;
                    const totalDuration = outboundDuration + returnDuration;
                    
                    return `
                    <div class="flight-card">
                        <div class="flight-header">
                            <div class="flight-price">
                                <span class="price-amount">
                                    <span class="currency">€</span>${flight.price}
                                </span>
                                <span class="flight-type-tag">${flight.type || ''}</span>
                            </div>
                        </div>
                        <div class="flight-segments">
                            ${outboundSegments}
                            ${returnSegments ? returnSegments : ''}
                        </div>
                        <div class="flight-summary">
                            <span>⏱ 总计: ${Math.floor(totalDuration / 60)}h ${totalDuration % 60}min</span>
                            <span>🛫 去程: ${flight.outbound_stops === 0 ? '直飞' : `${flight.outbound_stops}次中转`}</span>
                            ${flight.return_flights ? `<span>🛬 返程: ${flight.return_stops === 0 ? '直飞' : `${flight.return_stops}次中转`}</span>` : ''}
                        </div>
                        ${flight.extensions && flight.extensions.length > 0 ? `
                        <div class="flight-extensions">
                            ${flight.extensions.slice(0, 2).map(ext => `<span class="extension-tag">${ext}</span>`).join('')}
                        </div>
                        ` : ''}
                    </div>
                `}).join('');
                
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
            
            if (!priceData || priceData.length === 0) {
                chartSection.innerHTML = '<div class="error-message">No historical data found</div>';
                return;
            }
            
            const prices = priceData.map(d => d.price);
            const avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length;
            
            const pointColors = priceData.map(d => {
                if (d.price < avgPrice * 0.9) return '#28a745';
                if (d.price > avgPrice * 1.1) return '#dc3545';
                return '#667eea';
            });
            
            const pointRadius = priceData.map(d => {
                if (d.price < avgPrice * 0.9 || d.price > avgPrice * 1.1) return 8;
                return 4;
            });
            
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
                        tension: 0.4,
                        pointBackgroundColor: pointColors,
                        pointBorderColor: pointColors,
                        pointRadius: pointRadius
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: true },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const d = priceData[context.dataIndex];
                                    let label = `票价: ${d.price} CNY`;
                                    if (d.min_price && d.max_price) {
                                        label += ` (最低: ${d.min_price}, 最高: ${d.max_price})`;
                                    }
                                    if (d.price < avgPrice * 0.9) label += ' - 低价';
                                    if (d.price > avgPrice * 1.1) label += ' - 高价';
                                    return label;
                                }
                            }
                        },
                        title: {
                            display: true,
                            text: ['■ 绿色: 低价 (低于均价10%)', '■ 红色: 高价 (高于均价10%)', '■ 蓝色: 正常价格']
                        }
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
