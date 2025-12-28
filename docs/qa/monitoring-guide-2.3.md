# Story 2.3 监控部署指南

## 概述
本指南提供了 Story 2.3 (Azure OpenAI Integration & PII Scrubbing) 的监控系统部署指南。

## 监控架构

### 1. 指标收集层
```
应用代码 → Prometheus Monitor → Prometheus Server → Grafana
```

### 2. 监控指标

#### 成本监控指标
- `ai_cost_total` - 累计成本 (USD)
- `ai_cost_current` - 当前请求成本 (USD)

#### 使用量监控指标
- `ai_tokens_total` - 累计令牌使用量
- `ai_tokens_current` - 当前请求令牌数
- `ai_requests_total` - 累计请求数

#### 性能监控指标
- `ai_request_duration_seconds` - 请求延迟分布

#### 错误监控指标
- `ai_errors_total` - 错误计数
- `ai_rate_limit_hits_total` - 速率限制命中数

## 部署步骤

### 步骤 1: 安装依赖

```bash
# 安装 Prometheus 客户端
pip install prometheus-client

# 或者添加到 requirements.txt
echo "prometheus-client>=0.20.0" >> requirements.txt
```

### 步骤 2: 配置应用监控

在应用启动时添加监控端点：

```python
# 在 main.py 或应用入口点添加
from prometheus_client import start_http_server
from src.ai.prometheus_monitor import get_monitor

# 启动 Prometheus HTTP 服务器（端口 8000）
start_http_server(8000)

# 获取监控器实例
monitor = get_monitor()
print(f"Prometheus metrics available at http://localhost:8000")
```

### 步骤 3: 集成监控到现有代码

#### 在 Azure OpenAI 客户端中集成：

```python
# 在 openai_client.py 的适当位置添加
from src.ai.prometheus_monitor import (
    record_cost, record_tokens, record_request, 
    record_error, record_rate_limit
)

class AzureOpenAIClient:
    async def chat_completion(self, messages, **kwargs):
        start_time = time.time()
        try:
            response = await self._make_request(messages, **kwargs)
            duration = time.time() - start_time
            
            # 记录成功请求
            record_request("chat_completion", "success", duration)
            
            # 记录令牌使用
            if hasattr(response, 'usage'):
                record_tokens(response.usage.prompt_tokens, "prompt")
                record_tokens(response.usage.completion_tokens, "completion")
            
            return response
            
        except RateLimitError:
            record_rate_limit("chat_completion")
            record_request("chat_completion", "rate_limit", time.time() - start_time)
            raise
            
        except Exception as e:
            record_error(type(e).__name__, "chat_completion")
            record_request("chat_completion", "error", time.time() - start_time)
            raise
```

#### 在成本跟踪器中集成：

```python
# 在 cost_tracker.py 的 estimate 方法中添加
from src.ai.prometheus_monitor import record_cost

class CostTracker:
    def estimate(self, usage: Dict[str, int]) -> Dict[str, float]:
        # ... 现有计算逻辑 ...
        
        # 记录成本到 Prometheus
        record_cost(total, "batch_processing")
        
        return result
```

### 步骤 4: 部署 Prometheus 服务器

#### Docker 部署方式：

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    depends_on:
      - prometheus

volumes:
  prometheus_data:
  grafana_data:
```

#### Prometheus 配置文件：

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'ai-service'
    static_configs:
      - targets: ['host.docker.internal:8000']  # 应用监控端点
    metrics_path: '/metrics'
    scrape_interval: 10s
```

### 步骤 5: 配置 Grafana 仪表板

1. 访问 Grafana: http://localhost:3000
2. 登录 (admin/admin)
3. 添加 Prometheus 数据源
4. 导入预配置的仪表板

#### 预配置仪表板 JSON:

```json
{
  "dashboard": {
    "title": "AI Service Monitoring",
    "panels": [
      {
        "title": "Cost Overview",
        "targets": [{
          "expr": "sum(ai_cost_total)",
          "legendFormat": "Total Cost"
        }]
      },
      {
        "title": "Token Usage",
        "targets": [
          {"expr": "sum(ai_tokens_total{token_type='prompt'})", "legendFormat": "Prompt Tokens"},
          {"expr": "sum(ai_tokens_total{token_type='completion'})", "legendFormat": "Completion Tokens"}
        ]
      }
    ]
  }
}
```

### 步骤 6: 配置告警规则

#### Prometheus 告警规则：

```yaml
# alerts.yml
groups:
  - name: ai_service_alerts
    rules:
      - alert: HighAICost
        expr: rate(ai_cost_total[5m]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High AI service cost detected"
          description: "AI service cost rate is {{ $value }} USD per minute"
      
      - alert: RateLimitHit
        expr: rate(ai_rate_limit_hits_total[5m]) > 0
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Rate limit hit detected"
          description: "{{ $value }} rate limit hits in the last 5 minutes"
      
      - alert: HighErrorRate
        expr: rate(ai_errors_total[5m]) / rate(ai_requests_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }}%"
```

### 步骤 7: 测试监控系统

#### 测试脚本：

```python
# test_monitoring_integration.py
import time
from src.ai.prometheus_monitor import (
    record_cost, record_tokens, record_request,
    record_error, record_rate_limit
)

def test_monitoring_integration():
    """测试监控系统集成"""
    
    print("Testing monitoring integration...")
    
    # 模拟一些监控事件
    record_cost(5.0, "test_operation")
    record_tokens(1000, "prompt")
    record_tokens(500, "completion")
    record_request("test", "success", 1.5)
    record_error("test_error", "test")
    record_rate_limit("test")
    
    print("Monitoring events recorded successfully")
    
    # 验证指标端点
    import requests
    try:
        response = requests.get("http://localhost:8000/metrics", timeout=5)
        if response.status_code == 200:
            print("Prometheus metrics endpoint is accessible")
            # 检查是否包含我们的指标
            if "ai_cost_total" in response.text:
                print("✓ AI cost metrics found")
            if "ai_requests_total" in response.text:
                print("✓ AI request metrics found")
        else:
            print(f"✗ Metrics endpoint returned {response.status_code}")
    except Exception as e:
        print(f"✗ Could not access metrics endpoint: {e}")

if __name__ == "__main__":
    test_monitoring_integration()
```

## 替代方案

### 如果 Prometheus 不可用：

#### 方案 1: 日志监控
```python
# 使用结构化日志和日志聚合
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "cost": getattr(record, 'cost', None),
            "tokens": getattr(record, 'tokens', None),
            "operation": getattr(record, 'operation', None),
        }
        return json.dumps(log_record)

# 配置日志
logger = logging.getLogger("ai_service")
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

# 记录成本
logger.info("AI operation completed", extra={
    "cost": 5.0,
    "tokens": 1500,
    "operation": "chat_completion"
})
```

#### 方案 2: 简单阈值监控
```python
# simple_monitor.py
import time
from collections import deque
from threading import Thread

class SimpleMonitor:
    def __init__(self, alert_threshold=100.0):
        self.cost_total = 0
        self.alert_threshold = alert_threshold
        self.recent_costs = deque(maxlen=100)  # 最近100次成本
        self._alert_thread = None
        
    def record_cost(self, cost, operation):
        self.cost_total += cost
        self.recent_costs.append((time.time(), cost, operation))
        
        # 检查阈值
        if self.cost_total > self.alert_threshold:
            self._send_alert(f"Total cost {self.cost_total} exceeds threshold {self.alert_threshold}")
    
    def _send_alert(self, message):
        print(f"ALERT: {message}")
        # 可以集成到邮件、Slack、Webhook等
    
    def start_background_monitor(self):
        """启动后台监控线程"""
        self._alert_thread = Thread(target=self._monitor_loop, daemon=True)
        self._alert_thread.start()
    
    def _monitor_loop(self):
        while True:
            time.sleep(60)  # 每分钟检查一次
            # 检查最近成本趋势
            recent_total = sum(cost for _, cost, _ in self.recent_costs)
            if recent_total > self.alert_threshold * 0.1:  # 最近成本超过阈值的10%
                self._send_alert(f"High recent cost: {recent_total}")
```

## 验证检查清单

### 部署前检查
- [ ] Prometheus 客户端已安装
- [ ] 监控代码已集成到关键路径
- [ ] 测试监控事件记录
- [ ] 验证指标端点可访问

### 部署后检查
- [ ] Prometheus 服务器正在运行
- [ ] 指标正在被收集
- [ ] Grafana 仪表板配置正确
- [ ] 告警规则已配置
- [ ] 告警通知渠道已测试

### 生产验证
- [ ] 监控系统处理真实流量
- [ ] 成本计算准确
- [ ] 错误检测有效
- [ ] 性能影响可接受

## 故障排除

### 常见问题

1. **指标不可见**
   - 检查应用是否在运行
   - 验证端口 8000 是否可访问
   - 检查 Prometheus 配置中的目标地址

2. **成本计算不准确**
   - 验证令牌计数逻辑
   - 检查定价配置
   - 确认汇率转换（如果适用）

3. **性能影响**
   - 监控监控系统本身的资源使用
   - 考虑批量记录指标
   - 使用异步记录方式

### 监控系统健康检查

```bash
# 检查应用监控端点
curl http://localhost:8000/metrics | grep ai_

# 检查 Prometheus 目标状态
curl http://localhost:9090/api/v1/targets

# 检查 Grafana 数据源
curl -u admin:admin http://localhost:3000/api/datasources
```

## 维护和扩展

### 定期维护任务
- 监控磁盘使用（Prometheus 数据保留）
- 更新 Grafana 仪表板
- 审查和调整告警阈值
- 备份监控配置

### 扩展建议
1. **添加业务指标**：用户数、请求类型分布
2. **集成 APM**：分布式追踪（Jaeger, Zipkin）
3. **添加 SLA 监控**：可用性、响应时间 SLA
4. **成本优化建议**：基于使用模式的建议

## 联系和支持

- **监控系统文档**: 本指南
- **代码位置**: `src/ai/prometheus_monitor.py`
- **测试位置**: `tests/ai/test_prometheus_monitor.py`
- **配置示例**: `docs/qa/monitoring-guide-2.3.md`

---
*最后更新: 2025-12-28*
*版本: 1.0*
