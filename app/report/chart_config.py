import json


def pie_chart(container_id: str, title: str, data: list[dict]) -> str:
    """生成ECharts饼图配置。data格式: [{"name": "xxx", "value": 30}, ...]"""
    option = {
        "title": {"text": title, "left": "center", "textStyle": {"fontFamily": "'Source Serif Pro', 'Noto Serif SC', serif", "fontSize": 16, "color": "#2A2A2A"}},
        "tooltip": {"trigger": "item", "formatter": "{b}: {d}%"},
        "color": ["#2C3E2D", "#4A6B4E", "#7A9B6E", "#C9A961", "#E8A87C", "#8B7355"],
        "series": [{
            "type": "pie", "radius": ["40%", "70%"], "center": ["50%", "55%"],
            "itemStyle": {"borderRadius": 6, "borderColor": "#FAF7F2", "borderWidth": 2},
            "label": {"formatter": "{b}\n{d}%", "fontSize": 12},
            "data": data
        }]
    }
    return _chart_html(container_id, option)


def line_chart(container_id: str, title: str, x_data: list, series_list: list[dict]) -> str:
    """折线图。series_list: [{"name": "xxx", "data": [...]}]"""
    series = []
    colors = ["#2C3E2D", "#C9A961", "#D97757", "#7A9B6E", "#2A3B4D"]
    for i, s in enumerate(series_list):
        series.append({
            "name": s["name"], "type": "line", "data": s["data"],
            "smooth": True, "lineStyle": {"width": 2},
            "itemStyle": {"color": colors[i % len(colors)]}
        })
    option = {
        "title": {"text": title, "left": "center", "textStyle": {"fontFamily": "'Source Serif Pro', 'Noto Serif SC', serif", "fontSize": 16, "color": "#2A2A2A"}},
        "tooltip": {"trigger": "axis"},
        "legend": {"bottom": 0, "textStyle": {"fontSize": 11}},
        "grid": {"left": "8%", "right": "5%", "top": "18%", "bottom": "15%"},
        "xAxis": {"type": "category", "data": x_data, "axisLabel": {"fontSize": 11}},
        "yAxis": {"type": "value", "axisLabel": {"fontSize": 11}},
        "series": series
    }
    return _chart_html(container_id, option)


def kline_chart(container_id: str, title: str, dates: list, kline_data: list,
                volumes: list, events: list[dict] | None = None) -> str:
    """K线图。kline_data: [[open, close, low, high], ...]"""
    mark_points = []
    if events:
        for e in events:
            mark_points.append({"coord": [e["date"], e["price"]], "value": e["label"],
                                "itemStyle": {"color": "#C9A961"}})

    option = {
        "title": {"text": title, "left": "center", "textStyle": {"fontFamily": "'Source Serif Pro', 'Noto Serif SC', serif", "fontSize": 16, "color": "#2A2A2A"}},
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
        "grid": [
            {"left": "8%", "right": "5%", "top": "15%", "height": "55%"},
            {"left": "8%", "right": "5%", "top": "75%", "height": "15%"}
        ],
        "xAxis": [
            {"type": "category", "data": dates, "gridIndex": 0, "axisLabel": {"fontSize": 10}},
            {"type": "category", "data": dates, "gridIndex": 1, "axisLabel": {"show": False}}
        ],
        "yAxis": [
            {"type": "value", "gridIndex": 0, "scale": True},
            {"type": "value", "gridIndex": 1, "scale": True, "axisLabel": {"show": False}, "splitLine": {"show": False}}
        ],
        "series": [
            {
                "type": "candlestick", "data": kline_data, "xAxisIndex": 0, "yAxisIndex": 0,
                "itemStyle": {"color": "#D97757", "color0": "#7A9B6E", "borderColor": "#D97757", "borderColor0": "#7A9B6E"},
                "markPoint": {"data": mark_points, "symbol": "pin", "symbolSize": 40, "label": {"fontSize": 9}} if mark_points else {}
            },
            {
                "type": "bar", "data": volumes, "xAxisIndex": 1, "yAxisIndex": 1,
                "itemStyle": {"color": "#C9A961", "opacity": 0.5}
            }
        ]
    }
    return _chart_html(container_id, option, height="450px")


def gauge_chart(container_id: str, title: str, current: float, min_val: float,
                max_val: float, label: str = "") -> str:
    """标尺/仪表图，用于DCF估值和估值分位展示。"""
    pct = (current - min_val) / (max_val - min_val) * 100 if max_val != min_val else 50
    pct = max(0, min(100, pct))
    option = {
        "title": {"text": title, "left": "center", "textStyle": {"fontFamily": "'Source Serif Pro', 'Noto Serif SC', serif", "fontSize": 14, "color": "#2A2A2A"}},
        "series": [{
            "type": "gauge", "startAngle": 180, "endAngle": 0,
            "min": min_val, "max": max_val,
            "pointer": {"show": True, "length": "60%", "width": 4, "itemStyle": {"color": "#C9A961"}},
            "axisLine": {"lineStyle": {"width": 20, "color": [[0.3, "#7A9B6E"], [0.7, "#E8A87C"], [1, "#D97757"]]}},
            "axisTick": {"show": False},
            "splitLine": {"show": False},
            "axisLabel": {"fontSize": 11, "distance": 25},
            "detail": {"formatter": f"{{value}}\n{label}", "fontSize": 16, "offsetCenter": [0, "40%"], "color": "#2A2A2A"},
            "data": [{"value": round(current, 2)}]
        }]
    }
    return _chart_html(container_id, option, height="280px")


def _chart_html(container_id: str, option: dict, height: str = "350px") -> str:
    return f'''<div id="{container_id}" style="width:100%;height:{height};margin:20px 0;"></div>
<script>
(function(){{var c=echarts.init(document.getElementById('{container_id}'),null,{{renderer:'canvas'}});c.setOption({json.dumps(option, ensure_ascii=False)});window.addEventListener('resize',function(){{c.resize()}});}})();
</script>'''
