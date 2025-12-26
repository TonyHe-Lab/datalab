我们将基于 PRD 和架构文档，为 **AI 驱动的医疗工单分析系统** 创建一份详细的 **前端开发规格说明书 (Frontend Specification)**。

这份文档将直接指导 **Epic 4** 的开发，详细定义页面布局、组件结构、状态管理以及与后端 API 的交互方式。鉴于单人开发的约束，我们将最大限度利用 **Ant Design** 的现成组件模式。

---

执行指令: create-doc  
目标文件: docs/frontend-spec.md  
引用源: docs/prd.md, docs/architecture.md

# ---

**医疗工单智能分析系统前端规格说明书 (Frontend Specification)**

| Attribute        | Details                                      |
| :--------------- | :------------------------------------------- |
| **Project Name** | AI-Driven Medical Work Order Analysis System |
| **Version**      | 1.0                                          |
| **Status**       | **Approved**                                 |
| **Author**       | UX Designer Agent                            |
| **Tech Stack**   | React 18, Ant Design 5.x, Recharts, Axios    |

## **1. 设计概览 (Design Overview)**

### **1.1 设计哲学**

- **工具化 (Utilitarian)**: 界面应像 IDE 或专业仪表盘一样紧凑。避免不必要的留白，最大化信息密度。
- **一致性 (Consistency)**: 严格遵循 Ant Design 默认设计语言，仅在必要时进行最小化定制（如品牌色）。
- **响应式**: 优先适配桌面端 (1920x1080 & 1440x900)，但需通过 Flexbox/Grid 保证在笔记本屏幕上的可用性。

### **1.2 核心布局 (App Layout)**

采用 Ant Design <ProLayout> 或标准 <Layout> 结构：

- **Sidebar (Sider)**: 全局导航。
  - Logo area: "Medical AI Ops"
  - Menu Items:
    - Diagnostic Workbench (Icon: MedicineBoxOutlined)
    - Analytics Dashboard (Icon: BarChartOutlined)
    - Settings (Icon: SettingOutlined)
- **Header**: 显示当前页面标题、当前用户（模拟）、连接状态指示器（WSL <-> Host DB）。
- **Content Area**: 带有 Padding 的主操作区，白色背景卡片式设计。

## **2. 路由与页面结构 (Routing & Pages)**

| Route      | Component     | Description                                      |
| :--------- | :------------ | :----------------------------------------------- |
| /          | WorkbenchPage | 默认首页。智能诊断工作台，包含 Chat 和参考案例。 |
| /dashboard | DashboardPage | 统计分析看板，包含 MTBF 和 Pareto 图表。         |
| /settings  | SettingsPage  | 系统配置（如 API Key 填写，ETL 状态查看）。      |

## **3. 详细视图规格 (Detailed View Specs)**

### **3.1 智能诊断工作台 (Diagnostic Workbench)**

**布局**: 两栏布局 (Split View)。

- **Left Pane (Chat & Diagnosis)**: 占宽 60%。
- **Right Pane (Evidence & References)**: 占宽 40%。

#### **A. 左侧：交互区**

- **组件结构**:
  1. **Input Area (Top)**:
     - <Input.TextArea>: 允许输入多行故障描述。
     - <Button type="primary">: "Analyze / Diagnose".
  2. **Result Card (Bottom)**:
     - <Card title="AI Diagnosis">:
     - **Content**: 使用 <Markdown> 渲染器显示 AI 返回的 summary 和 resolution_steps。
     - **Tags**: 在顶部显示提取的元数据 <Tag color="red">{fault_code}</Tag>, <Tag color="blue">{component}</Tag>.

#### **B. 右侧：佐证区**

- **组件结构**:
  - <List> (Ant Design List): 渲染 "Reference Cases"。
  - **Item Layout**:
    - **Title**: 工单 ID + 日期 (e.g., "WO-2023001 | 2023-10-27")
    - **Description**: 原始问题摘要 (截断显示)。
    - **Action**: "View Details" 按钮，点击弹窗 (<Modal>) 显示完整工单 JSON。

### **3.2 趋势监控仪表盘 (Analytics Dashboard)**

**布局**: 栅格布局 (Grid Layout)。

#### **A. 顶部筛选栏 (Filter Bar)**

- <Space> 容器:
  - <DatePicker.RangePicker>: 选择分析时间段。
  - <Select>: 选择设备型号 (Device Model)。
  - <Button>: "Refresh Data".

#### **B. 核心指标卡 (KPI Cards)**

- Row 1 (4 Cards):
  - **Avg MTBF**: 显示小时数 (e.g., "450 Hours") + 环比箭头。
  - **Total Failures**: 总故障数。
  - **Top Fault Component**: 当前最高频故障部件。
  - **Data Freshness**: 上次 ETL 同步时间。

#### **C. 图表区 (Charts)**

- **Row 2 (Main Chart)**: <Card title="Reliability Trend (MTBF)">
  - Content: **Recharts** <LineChart>.
  - X 轴: 时间 (周/月)。
  - Y 轴: MTBF (小时)。
  - Line: 带有数据点的平滑曲线。
- **Row 3 (Secondary Charts)**:
  - Left: <Card title="Top 10 Failing Components">
    - Content: **Recharts** <BarChart> (Horizontal layout).
  - Right: <Card title="Fault Type Distribution">
    - Content: **Recharts** <PieChart>.

## **4. 状态管理与数据流 (State Management)**

由于应用逻辑主要围绕“远程数据获取”，推荐使用 **React Query (TanStack Query)** + **Axios**。

### **4.1 Server State (React Query)**

- useDiagnosis(query): Mutation。POST /api/chat。触发时 isLoading 设为 true，禁用提交按钮。
- useDashboardMetrics(filters): Query。GET /api/dashboard。自动缓存，切换页面不重新加载。
- useReferenceCases(id): Query。GET /api/cases/{id}。

### **4.2 Client State (Local/Context)**

- 使用 React Context 或简单 useState 管理全局配置（如 Theme Mode, Current User）。
- 不需要复杂的 Redux/Zustand，保持简单。

## **5. 组件与样式规范 (Component & Styling)**

### **5.1 颜色系统 (Ant Design Token)**

- **Primary Color**: #1890ff (Tech Blue) - 用于操作按钮、高亮。
- **Error Color**: #ff4d4f - 用于高危故障、报错。
- **Success Color**: #52c41a - 用于系统正常、修复成功。
- **Background**: #f0f2f5 (Layout BG), #ffffff (Card BG).

### **5.2 字体排印**

- **Monospace**: 用于显示 Error Code, Log Snippets, JSON。
- **System UI**: 用于常规文本。

## **6. API 集成层 (Service Layer)**

在 /src/services 下封装 API 调用：

TypeScript

// services/api.ts  
const api = axios.create({ baseURL: '/api' });

export const diagnoseIssue = async (text: string) => {  
 return api.post('/chat', { query: text });  
};

export const fetchDashboardStats = async (range: [Date, Date]) => {  
 return api.get('/dashboard', { params: { start: range[0], end: range[1] } });  
};

## **7. 异常处理 (Error Handling)**

- **API 错误**: 使用 Ant Design <message.error()> 全局提示网络错误。
- **空状态**: 当看板无数据时，使用 <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} />。
- **Loading**: 诊断过程中，Chat 区域显示 <Skeleton active /> 骨架屏。

---

