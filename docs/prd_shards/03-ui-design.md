```markdown
## 3. UI Design Goals

### 3.1 UX Vision

- **工程师导向**: 界面采用高密度信息展示，风格简洁专业 (Ant Design)。
- **分离视图**: 明确区分“诊断工作台 (一线维修)”和“管理仪表盘 (宏观分析)”。

### 3.2 Core Screens

1. **智能诊断工作台 (Diagnostic Workbench)**
   - 提供类似 Chat 的自然语言输入框。
   - 左侧/底部展示 AI 生成的建议 (Markdown 渲染)。
   - 右侧展示 "Reference Cases" (佐证)，列出相似的历史工单详情。
2. **趋势监控仪表盘 (Analytics Dashboard)**
   - **MTBF 趋势图**: 使用折线图展示设备可靠性变化。
   - **故障 Pareto 图**: 使用条形图展示高频故障原因。
   - 支持按“时间范围”和“设备型号”筛选。

### 3.3 Technology Stack (Frontend)

- **Framework**: React (Vite) Single Page Application.
- **Component Library**: **Ant Design** (for efficiency).
- **Charting Library**: **Recharts** (for visualization).

```
