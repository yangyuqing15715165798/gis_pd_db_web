// 全局变量
let prpdChart = null;
let prpsChart = null;
let historyPrpdChart = null;
let historyPrpsChart = null;
let websocket = null;
let useDbm = false;
let showSineWave = true;
let sineAmplitude = 1.0;
let updateInterval = 1000; // 默认1秒更新一次
let maxCycles = 10; // 默认显示10个周期
let colorScheme = 'default';
let prpsMaxCycles = 50; // PRPS图固定显示最新的50个周期
let accumulatedData = []; // 存储累积的周期数据

// 颜色方案定义
const colorSchemes = {
    'default': ['#000000', '#FFFFFE', '#FFFF13', '#FF0000'],
    'blue-green-red': ['#0000FF', '#00FFFF', '#00FF00', '#FF0000'],
    'black-blue-purple': ['#000000', '#0000FF', '#800080', '#FF00FF'],
    'green-yellow-red': ['#006400', '#7FFF00', '#FFFF00', '#FF0000']
};

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化导航
    initNavigation();
    
    // 初始化图表
    initCharts();
    
    // 初始化WebSocket连接
    connectWebSocket();
    
    // 初始化控件事件
    initControlEvents();
    
    // 加载数据库统计信息
    loadDbStats();
    
    // 防止图表大小变化
    preventChartResize();
});

// 初始化导航
function initNavigation() {
    const navItems = document.querySelectorAll('nav ul li a');
    const sections = document.querySelectorAll('main section');
    
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            // 移除所有导航项的active类
            navItems.forEach(nav => nav.classList.remove('active'));
            
            // 为当前点击的导航项添加active类
            this.classList.add('active');
            
            // 隐藏所有section
            sections.forEach(section => {
                section.classList.remove('active-section');
                section.classList.add('section');
            });
            
            // 显示对应的section
            const targetId = this.id.replace('nav-', '') + '-section';
            document.getElementById(targetId).classList.remove('section');
            document.getElementById(targetId).classList.add('active-section');
        });
    });
}

// 初始化图表
function initCharts() {
    // 初始化PRPD图表
    const prpdCtx = document.getElementById('prpd-chart').getContext('2d');
    prpdChart = new Chart(prpdCtx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'PRPD数据',
                data: [],
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1,
                pointRadius: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2,  // 固定宽高比
            onResize: function(chart, size) {
                // 防止图表大小异常变化
                if (size.height > 600) {
                    size.height = 400;
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: '相位 (°)'
                    },
                    min: 0,
                    max: 360
                },
                y: {
                    title: {
                        display: true,
                        text: '幅值 (mV)'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'PRPD图'
                }
            }
        }
    });
    
    // 初始化PRPS图表 (使用Plotly.js)
    initPrpsChart();
    
    // 初始化历史数据PRPD图表
    const historyPrpdCtx = document.getElementById('history-prpd-chart').getContext('2d');
    historyPrpdChart = new Chart(historyPrpdCtx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: '历史PRPD数据',
                data: [],
                backgroundColor: 'rgba(255, 99, 132, 0.5)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1,
                pointRadius: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2,  // 固定宽高比
            onResize: function(chart, size) {
                // 防止图表大小异常变化
                if (size.height > 600) {
                    size.height = 400;
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: '相位 (°)'
                    },
                    min: 0,
                    max: 360
                },
                y: {
                    title: {
                        display: true,
                        text: '幅值 (mV)'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: '历史PRPD图'
                }
            }
        }
    });
}

// 初始化PRPS图表
function initPrpsChart() {
    const prpsElement = document.getElementById('prps-chart');
    
    // 创建空的3D表面图
    const data = [{
        type: 'surface',
        x: [],  // 相位
        y: [],  // 周期
        z: [],  // 幅值
        colorscale: 'Jet',
        contours: {
            z: {
                show: true,
                usecolormap: true,
                highlightcolor: "#42f462",
                project: {z: true}
            }
        }
    }];
    
    const layout = {
        title: 'PRPS图',
        scene: {
            xaxis: {
                title: '相位 (°)',
                range: [0, 360]
            },
            yaxis: {
                title: '周期',
                range: [1, prpsMaxCycles]
            },
            zaxis: {title: '幅值 (mV)'},
            camera: {
                eye: {x: 1.5, y: 1.5, z: 1}
            },
            aspectratio: {x: 1.5, y: 1, z: 0.8}
        },
        margin: {
            l: 0,
            r: 0,
            b: 0,
            t: 30
        },
        autosize: true
    };
    
    const config = {
        responsive: true,
        displayModeBar: true, // 显示模式栏，方便用户操作3D图
        modeBarButtonsToRemove: ['toImage', 'sendDataToCloud'], // 移除不需要的按钮
        displaylogo: false // 不显示Plotly logo
    };
    
    Plotly.newPlot(prpsElement, data, layout, config);
    prpsChart = prpsElement;
    
    // 初始化历史PRPS图表
    const historyPrpsElement = document.getElementById('history-prps-chart');
    Plotly.newPlot(historyPrpsElement, data, layout, config);
    historyPrpsChart = historyPrpsElement;
}

// 连接WebSocket
function connectWebSocket() {
    // 关闭之前的WebSocket连接
    if (websocket !== null) {
        websocket.close();
    }
    
    // 创建新的WebSocket连接
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    websocket = new WebSocket(wsUrl);
    
    websocket.onopen = function(event) {
        console.log('WebSocket连接已建立');
        // 清空累积数据，准备接收新数据
        accumulatedData = [];
    };
    
    websocket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.success) {
            // 检查是否有数据
            if (data.data && data.data.length > 0) {
                console.log("收到WebSocket数据:", data.data.length, "条记录");
                
                // 将新数据添加到累积数据中
                accumulatedData = [...accumulatedData, ...data.data];
                
                // 保持最新的prpsMaxCycles个周期
                if (accumulatedData.length > prpsMaxCycles) {
                    accumulatedData = accumulatedData.slice(-prpsMaxCycles);
                }
                
                // 使用累积的数据更新图表
                updateCharts(accumulatedData);
                
                // 更新数据库统计信息
                loadDbStats();
            } else {
                console.log("收到WebSocket消息，但没有新数据");
            }
        } else {
            console.error("WebSocket数据错误:", data.error);
        }
    };
    
    websocket.onclose = function(event) {
        console.log('WebSocket连接已关闭');
        // 尝试重新连接
        setTimeout(function() {
            connectWebSocket();
        }, 3000);
    };
    
    websocket.onerror = function(error) {
        console.error('WebSocket错误:', error);
    };
}

// 更新图表数据
function updateCharts(data) {
    // 更新PRPD图表
    updatePrpdChart(data);
    
    // 更新PRPS图表
    updatePrpsChart(data);
}

// 更新PRPD图表
function updatePrpdChart(data) {
    // 处理数据
    const chartType = document.getElementById('chart-type').value;
    
    console.log("PRPD图表更新 - 接收到的周期数:", data.length);
    
    // 只使用PRPD需要的最新周期数
    let prpdData = data;
    if (data.length > maxCycles) {
        prpdData = data.slice(-maxCycles);
    }
    
    console.log("PRPD图表更新 - 使用的周期数:", prpdData.length, "最大周期数设置:", maxCycles);
    
    const allData = [];
    const xData = [];
    
    // 合并所有周期的数据用于绘图
    prpdData.forEach(cycle => {
        const cycleData = cycle.data;
        const phaseStep = 360 / cycleData.length;
        
        cycleData.forEach((value, index) => {
            const phase = index * phaseStep;
            xData.push(phase);
            allData.push(value);
        });
    });
    
    // 根据当前单位设置转换数据
    let displayData = allData;
    if (useDbm) {
        displayData = allData.map(value => convertToDbm(value));
    }
    
    // 准备图表数据
    const chartData = [];
    for (let i = 0; i < xData.length; i++) {
        chartData.push({
            x: xData[i],
            y: displayData[i]
        });
    }
    
    // 更新图表类型
    prpdChart.config.type = chartType === 'scatter' ? 'scatter' : 'line';
    
    // 更新图表数据
    prpdChart.data.datasets[0].data = chartData;
    
    // 更新图表标题
    prpdChart.options.plugins.title.text = `PRPD图 (最新${prpdData.length}个周期)`;
    
    // 更新Y轴标题
    prpdChart.options.scales.y.title.text = useDbm ? '幅值 (dBm)' : '幅值 (mV)';
    
    // 如果显示参考正弦波
    if (showSineWave) {
        // 添加参考正弦波
        addSineWave(prpdChart, displayData);
    } else {
        // 如果有正弦波数据集，则移除
        if (prpdChart.data.datasets.length > 1) {
            prpdChart.data.datasets.splice(1);
        }
    }
    
    // 更新图表
    prpdChart.update();
}

// 更新PRPS图表
function updatePrpsChart(data) {
    // 准备数据
    let numCycles = data.length;
    if (numCycles === 0) return;
    
    console.log("PRPS图表更新 - 接收到的周期数:", numCycles);
    
    // 只使用PRPS需要的最新周期数
    let prpsData = data;
    if (numCycles > prpsMaxCycles) {
        prpsData = data.slice(-prpsMaxCycles);
        numCycles = prpsMaxCycles;
    }
    
    console.log("PRPS图表更新 - 使用的周期数:", numCycles);
    
    // 找到所有周期中最大的数据点数
    let maxPoints = 0;
    prpsData.forEach(cycle => {
        maxPoints = Math.max(maxPoints, cycle.data.length);
    });
    
    // 创建规则网格
    const phase = Array.from({length: maxPoints}, (_, i) => i * (360 / maxPoints));
    const cycles = Array.from({length: numCycles}, (_, i) => i + 1);
    
    // 创建Z值矩阵
    const zData = Array(numCycles).fill().map(() => Array(maxPoints).fill(0));
    
    // 填充Z值矩阵
    prpsData.forEach((cycle, i) => {
        const cycleData = cycle.data;
        
        if (cycleData.length === maxPoints) {
            // 如果数据点数等于maxPoints，直接填充
            for (let j = 0; j < maxPoints; j++) {
                zData[i][j] = useDbm ? convertToDbm(cycleData[j]) : cycleData[j];
            }
        } else {
            // 如果数据点数不等于maxPoints，需要重采样
            const cyclePhases = Array.from({length: cycleData.length}, (_, i) => i * (360 / cycleData.length));
            
            for (let j = 0; j < maxPoints; j++) {
                // 使用线性插值
                const phaseValue = phase[j];
                let value = interpolateValue(cyclePhases, cycleData, phaseValue);
                zData[i][j] = useDbm ? convertToDbm(value) : value;
            }
        }
    });
    
    // 创建新的数据对象
    const plotData = [{
        type: 'surface',
        x: phase,
        y: cycles,
        z: zData,
        colorscale: getColorscale(colorScheme),
        showscale: true,
        contours: {
            z: {
                show: true,
                usecolormap: true,
                highlightcolor: "#42f462",
                project: {z: true}
            }
        }
    }];
    
    // 更新布局
    const layout = {
        title: `PRPS图 (最新${numCycles}个周期)`,
        scene: {
            xaxis: {
                title: '相位 (°)',
                range: [0, 360]
            },
            yaxis: {
                title: '周期',
                range: [1, prpsMaxCycles]
            },
            zaxis: {
                title: {
                    text: useDbm ? '幅值 (dBm)' : '幅值 (mV)'
                }
            },
            camera: {
                eye: {x: 1.5, y: 1.5, z: 1}
            },
            aspectratio: {x: 1.5, y: 1, z: 0.8}
        },
        margin: {
            l: 0,
            r: 0,
            b: 0,
            t: 30
        },
        autosize: true
    };
    
    // 完全重新绘制图表，而不是更新
    try {
        Plotly.react(prpsChart, plotData, layout);
        console.log("PRPS图表重绘成功");
    } catch (error) {
        console.error("更新PRPS图表时出错:", error);
    }
}

// 添加参考正弦波
function addSineWave(chart, data) {
    // 计算正弦波的振幅和偏移量
    let sineAmp, sineOffset;
    
    if (data.length > 0) {
        const maxData = Math.max(...data);
        const minData = Math.min(...data);
        const dataRange = maxData - minData;
        
        // 计算正弦波的振幅，使其与数据的振幅范围相适应
        sineAmp = sineAmplitude * dataRange / 4;
        // 计算正弦波的偏移量，使其居中显示
        sineOffset = (maxData + minData) / 2;
    } else {
        sineAmp = sineAmplitude;
        sineOffset = 0;
    }
    
    // 生成正弦波数据
    const sineData = [];
    for (let i = 0; i <= 360; i++) {
        const radians = i * Math.PI / 180;
        const value = sineAmp * Math.sin(radians) + sineOffset;
        sineData.push({
            x: i,
            y: value
        });
    }
    
    // 如果已经有正弦波数据集，则更新
    if (chart.data.datasets.length > 1) {
        chart.data.datasets[1].data = sineData;
    } else {
        // 否则添加新的数据集
        chart.data.datasets.push({
            label: '参考正弦波',
            data: sineData,
            type: 'line',
            backgroundColor: 'rgba(255, 99, 132, 0.5)',
            borderColor: 'rgba(255, 99, 132, 1)',
            borderWidth: 2,
            pointRadius: 0,
            fill: false
        });
    }
}

// 初始化控件事件
function initControlEvents() {
    // 图表类型切换
    document.getElementById('chart-type').addEventListener('change', function() {
        const chartType = this.value;
        if (chartType === 'scatter') {
            prpdChart.config.type = 'scatter';
        } else {
            prpdChart.config.type = 'line';
        }
        prpdChart.update();
    });
    
    // 参考正弦波显示切换
    document.getElementById('show-sine').addEventListener('change', function() {
        showSineWave = this.checked;
        // 触发图表更新
        fetchLatestData();
    });
    
    // 正弦波振幅调整
    document.getElementById('sine-amplitude').addEventListener('input', function() {
        sineAmplitude = parseFloat(this.value);
        document.getElementById('sine-amplitude-value').textContent = sineAmplitude.toFixed(1);
        // 触发图表更新
        fetchLatestData();
    });
    
    // 单位切换
    document.getElementById('unit-toggle').addEventListener('click', function() {
        useDbm = !useDbm;
        this.textContent = useDbm ? '单位: dBm' : '单位: mV';
        // 触发图表更新
        fetchLatestData();
    });
    
    // 历史数据查询类型切换
    document.getElementById('query-type').addEventListener('change', function() {
        const queryType = this.value;
        const latestCountGroup = document.getElementById('latest-count-group');
        const timeRangeGroups = document.querySelectorAll('.time-range-group');
        
        if (queryType === 'latest') {
            latestCountGroup.style.display = 'block';
            timeRangeGroups.forEach(group => group.style.display = 'none');
        } else {
            latestCountGroup.style.display = 'none';
            timeRangeGroups.forEach(group => group.style.display = 'block');
        }
    });
    
    // 历史数据查询按钮
    document.getElementById('query-btn').addEventListener('click', function() {
        queryHistoricalData();
    });
    
    // 历史图表类型切换
    document.getElementById('history-chart-type').addEventListener('change', function() {
        const chartType = this.value;
        const historyPrpdChartElement = document.getElementById('history-prpd-chart');
        const historyPrpsChartElement = document.getElementById('history-prps-chart');
        
        if (chartType === 'prps') {
            historyPrpdChartElement.style.display = 'none';
            historyPrpsChartElement.style.display = 'block';
        } else {
            historyPrpdChartElement.style.display = 'block';
            historyPrpsChartElement.style.display = 'none';
            
            // 更新PRPD图表类型
            if (chartType === 'prpd-scatter') {
                historyPrpdChart.config.type = 'scatter';
            } else {
                historyPrpdChart.config.type = 'line';
            }
            historyPrpdChart.update();
        }
    });
    
    // 保存设置按钮
    document.getElementById('save-settings').addEventListener('click', function() {
        saveSettings();
    });
    
    // 设置初始值
    document.getElementById('update-interval').value = updateInterval / 1000;
    document.getElementById('max-cycles').value = maxCycles;
    document.getElementById('color-scheme').value = colorScheme;
}

// 保存设置
function saveSettings() {
    // 保存旧设置用于比较
    const oldMaxCycles = maxCycles;
    const oldUpdateInterval = updateInterval;
    const oldColorScheme = colorScheme;
    
    // 更新设置
    updateInterval = parseInt(document.getElementById('update-interval').value) * 1000;
    maxCycles = parseInt(document.getElementById('max-cycles').value);
    colorScheme = document.getElementById('color-scheme').value;
    
    console.log("设置已更新 - 最大周期数:", maxCycles, "更新间隔:", updateInterval, "颜色方案:", colorScheme);
    
    // 检查是否需要重新连接WebSocket
    const needReconnect = oldUpdateInterval !== updateInterval;
    
    if (needReconnect && websocket !== null) {
        console.log("更新间隔已更改，重新连接WebSocket");
        websocket.close();
        setTimeout(function() {
            connectWebSocket();
        }, 500);
    } else {
        // 如果不需要重新连接，但设置已更改，立即获取最新数据以应用新设置
        if (oldMaxCycles !== maxCycles || oldColorScheme !== colorScheme) {
            console.log("设置已更改，刷新数据");
            fetchLatestData();
        }
    }
    
    alert('设置已保存');
}

// 加载数据库统计信息
function loadDbStats() {
    fetch('/api/db_stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('cycle-count').textContent = data.data.cycle_count;
                document.getElementById('raw-count').textContent = data.data.raw_count;
                document.getElementById('latest-time').textContent = data.data.latest_cycle || '无数据';
                
                // 如果有时间范围查询，设置默认值
                if (data.data.earliest_cycle && data.data.latest_cycle) {
                    document.getElementById('start-time').value = formatDateTimeForInput(data.data.earliest_cycle);
                    document.getElementById('end-time').value = formatDateTimeForInput(data.data.latest_cycle);
                }
            } else {
                console.error('加载数据库统计信息失败:', data.error);
            }
        })
        .catch(error => {
            console.error('请求数据库统计信息出错:', error);
        });
}

// 查询历史数据
function queryHistoricalData() {
    const queryType = document.getElementById('query-type').value;
    let url;
    
    if (queryType === 'latest') {
        const count = document.getElementById('latest-count').value;
        url = `/api/latest_cycle_data?count=${count}`;
    } else {
        const startTime = document.getElementById('start-time').value;
        const endTime = document.getElementById('end-time').value;
        
        if (!startTime || !endTime) {
            alert('请选择开始时间和结束时间');
            return;
        }
        
        // 将HTML datetime-local格式转换为数据库格式
        const formattedStartTime = formatDateTimeForDb(startTime);
        const formattedEndTime = formatDateTimeForDb(endTime);
        
        url = `/api/cycle_data_by_time?start_time=${encodeURIComponent(formattedStartTime)}&end_time=${encodeURIComponent(formattedEndTime)}`;
    }
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateHistoryCharts(data.data);
            } else {
                console.error('查询历史数据失败:', data.error);
                alert('查询历史数据失败: ' + data.error);
            }
        })
        .catch(error => {
            console.error('请求历史数据出错:', error);
            alert('请求历史数据出错: ' + error);
        });
}

// 更新历史图表
function updateHistoryCharts(data) {
    const chartType = document.getElementById('history-chart-type').value;
    
    if (chartType === 'prps') {
        updateHistoryPrpsChart(data);
    } else {
        updateHistoryPrpdChart(data, chartType === 'prpd-scatter' ? 'scatter' : 'line');
    }
}

// 更新历史PRPD图表
function updateHistoryPrpdChart(data, type) {
    // 处理数据
    console.log("历史PRPD图表更新 - 接收到的周期数:", data.length);
    
    // 只使用PRPD需要的最新周期数
    let prpdData = data;
    if (data.length > maxCycles) {
        prpdData = data.slice(-maxCycles);
    }
    
    console.log("历史PRPD图表更新 - 使用的周期数:", prpdData.length, "最大周期数设置:", maxCycles);
    
    const allData = [];
    const xData = [];
    
    // 合并所有周期的数据用于绘图
    prpdData.forEach(cycle => {
        const cycleData = cycle.data;
        const phaseStep = 360 / cycleData.length;
        
        cycleData.forEach((value, index) => {
            const phase = index * phaseStep;
            xData.push(phase);
            allData.push(value);
        });
    });
    
    // 根据当前单位设置转换数据
    let displayData = allData;
    if (useDbm) {
        displayData = allData.map(value => convertToDbm(value));
    }
    
    // 准备图表数据
    const chartData = [];
    for (let i = 0; i < xData.length; i++) {
        chartData.push({
            x: xData[i],
            y: displayData[i]
        });
    }
    
    // 更新图表类型
    historyPrpdChart.config.type = type;
    
    // 更新图表数据
    historyPrpdChart.data.datasets[0].data = chartData;
    
    // 更新图表标题
    historyPrpdChart.options.plugins.title.text = `历史PRPD图 (${prpdData.length}个周期)`;
    
    // 更新Y轴标题
    historyPrpdChart.options.scales.y.title.text = useDbm ? '幅值 (dBm)' : '幅值 (mV)';
    
    // 更新图表
    historyPrpdChart.update();
}

// 更新历史PRPS图表
function updateHistoryPrpsChart(data) {
    // 准备数据
    let numCycles = data.length;
    if (numCycles === 0) return;
    
    console.log("历史PRPS图表更新 - 接收到的周期数:", numCycles);
    
    // 只使用PRPS需要的最新周期数
    let prpsData = data;
    if (numCycles > prpsMaxCycles) {
        prpsData = data.slice(-prpsMaxCycles);
        numCycles = prpsMaxCycles;
    }
    
    console.log("历史PRPS图表更新 - 使用的周期数:", numCycles);
    
    // 找到所有周期中最大的数据点数
    let maxPoints = 0;
    prpsData.forEach(cycle => {
        maxPoints = Math.max(maxPoints, cycle.data.length);
    });
    
    // 创建规则网格
    const phase = Array.from({length: maxPoints}, (_, i) => i * (360 / maxPoints));
    const cycles = Array.from({length: numCycles}, (_, i) => i + 1);
    
    // 创建Z值矩阵
    const zData = Array(numCycles).fill().map(() => Array(maxPoints).fill(0));
    
    // 填充Z值矩阵
    prpsData.forEach((cycle, i) => {
        const cycleData = cycle.data;
        
        if (cycleData.length === maxPoints) {
            // 如果数据点数等于maxPoints，直接填充
            for (let j = 0; j < maxPoints; j++) {
                zData[i][j] = useDbm ? convertToDbm(cycleData[j]) : cycleData[j];
            }
        } else {
            // 如果数据点数不等于maxPoints，需要重采样
            const cyclePhases = Array.from({length: cycleData.length}, (_, i) => i * (360 / cycleData.length));
            
            for (let j = 0; j < maxPoints; j++) {
                // 使用线性插值
                const phaseValue = phase[j];
                let value = interpolateValue(cyclePhases, cycleData, phaseValue);
                zData[i][j] = useDbm ? convertToDbm(value) : value;
            }
        }
    });
    
    // 创建新的数据对象
    const plotData = [{
        type: 'surface',
        x: phase,
        y: cycles,
        z: zData,
        colorscale: getColorscale(colorScheme),
        showscale: true,
        contours: {
            z: {
                show: true,
                usecolormap: true,
                highlightcolor: "#42f462",
                project: {z: true}
            }
        }
    }];
    
    // 更新布局
    const layout = {
        title: `历史PRPS图 (${numCycles}个周期)`,
        scene: {
            xaxis: {
                title: '相位 (°)',
                range: [0, 360]
            },
            yaxis: {
                title: '周期',
                range: [1, prpsMaxCycles]
            },
            zaxis: {
                title: {
                    text: useDbm ? '幅值 (dBm)' : '幅值 (mV)'
                }
            },
            camera: {
                eye: {x: 1.5, y: 1.5, z: 1}
            },
            aspectratio: {x: 1.5, y: 1, z: 0.8}
        },
        margin: {
            l: 0,
            r: 0,
            b: 0,
            t: 30
        },
        autosize: true
    };
    
    // 完全重新绘制图表，而不是更新
    try {
        Plotly.react(historyPrpsChart, plotData, layout);
        console.log("历史PRPS图表重绘成功");
    } catch (error) {
        console.error("更新历史PRPS图表时出错:", error);
    }
}

// 获取最新数据
function fetchLatestData() {
    // 请求足够的数据以满足PRPD和PRPS图表的需求
    const requestCount = Math.max(maxCycles, prpsMaxCycles);
    console.log(`请求最新数据 - 请求数量: ${requestCount} (PRPD: ${maxCycles}, PRPS: ${prpsMaxCycles})`);
    
    fetch(`/api/latest_cycle_data?count=${requestCount}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateCharts(data.data);
            } else {
                console.error('获取最新数据失败:', data.error);
            }
        })
        .catch(error => {
            console.error('请求最新数据出错:', error);
        });
}

// 工具函数：毫伏转dBm
function convertToDbm(value) {
    return value * 54.545 - 81.818;
}

// 工具函数：dBm转毫伏
function convertToMv(value) {
    return (value + 81.818) / 54.545;
}

// 工具函数：线性插值
function interpolateValue(x, y, x0) {
    // 找到x0在x数组中的位置
    let i = 0;
    while (i < x.length && x[i] < x0) {
        i++;
    }
    
    if (i === 0) {
        return y[0];
    }
    
    if (i === x.length) {
        return y[x.length - 1];
    }
    
    // 线性插值
    const x1 = x[i - 1];
    const x2 = x[i];
    const y1 = y[i - 1];
    const y2 = y[i];
    
    return y1 + (y2 - y1) * (x0 - x1) / (x2 - x1);
}

// 工具函数：获取颜色方案
function getColorscale(scheme) {
    const colors = colorSchemes[scheme] || colorSchemes['default'];
    return colors.map((color, i) => [i / (colors.length - 1), color]);
}

// 工具函数：格式化日期时间用于input元素
function formatDateTimeForInput(dateTimeString) {
    const date = new Date(dateTimeString);
    return date.toISOString().slice(0, 16);
}

// 工具函数：格式化日期时间用于数据库查询
function formatDateTimeForDb(inputDateTimeString) {
    const date = new Date(inputDateTimeString);
    return date.toISOString().replace('T', ' ').slice(0, 19);
}

// 防止图表大小变化的事件处理
function preventChartResize() {
    // 获取所有图表容器
    const chartWrappers = document.querySelectorAll('.chart-wrapper');
    
    // 为每个容器添加鼠标事件处理
    chartWrappers.forEach(wrapper => {
        wrapper.addEventListener('mouseenter', function(e) {
            // 记录当前高度
            if (!this.dataset.originalHeight) {
                this.dataset.originalHeight = this.style.height;
            }
        });
        
        wrapper.addEventListener('mouseleave', function(e) {
            // 恢复原始高度
            if (this.dataset.originalHeight) {
                this.style.height = this.dataset.originalHeight;
            }
        });
    });
    
    // 防止鼠标滚轮事件导致图表大小变化
    document.addEventListener('wheel', function(e) {
        const target = e.target;
        if (target.closest('.chart-wrapper') || target.closest('canvas') || target.closest('.js-plotly-plot')) {
            // 如果滚轮事件发生在图表区域，阻止默认行为
            if (e.ctrlKey) {
                e.preventDefault();
            }
        }
    }, { passive: false });
} 