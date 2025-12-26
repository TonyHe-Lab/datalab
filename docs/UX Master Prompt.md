**“Master Prompt” (主提示词)**

你可以将这个提示词直接发送给 **Cursor (Composer)**、**v0.dev** 或 **GitHub Copilot**，以便通过一次交互生成高质量的 React 项目骨架和核心 UI 组件。

此提示词经过优化，包含上下文、技术栈约束和具体的组件要求。

### ---

**🎨 UI Master Prompt (Copy & Paste code below)**

Markdown

# Role

You are a Senior Frontend Engineer and UX Specialist expert in React and Ant Design.

# Goal

Scaffold a complete Frontend application for the "AI-Driven Medical Work Order Analysis System".  
The app must be a Single Page Application (SPA) using React 18 + Vite, styled with Ant Design 5.x.

# Technical Constraints

- \***\*Framework\*\***: React 18 (Vite) + TypeScript.
- \***\*UI Library\*\***: Ant Design (latest version). Use <ConfigProvider> for theming.
- \***\*Charts\*\***: Recharts (ResponsiveContainer).
- \***\*Icons\*\***: @ant-design/icons.
- \***\*State/Network\*\***: Axios (mocked for now).
- \***\*Layout\*\***: Ant Design ProLayout or standard Layout (Sider + Header + Content).
- \***\*Environment\*\***: The app will run in a Monorepo structure (assume /frontend folder).

# Theme & Styling

- Primary Color: #1890ff (Tech Blue).
- Layout Background: #f0f2f5.
- Component Background: #ffffff.
- Density: Compact (High information density for engineers).

# Core Pages to Implement

## 1. App Layout (Shell)

- Sidebar Navigation:
- "Diagnostic Workbench" (Icon: MedicineBoxOutlined) -> Path: /
- "Analytics Dashboard" (Icon: BarChartOutlined) -> Path: /dashboard
- "Settings" (Icon: SettingOutlined) -> Path: /settings
- Header:
- Title: "Medical AI Ops"
- Right side: Connection Status Indicator (Green dot: "Host DB Connected").

## 2. Page: Diagnostic Workbench (Path: /)

- \***\*Layout\*\***: Split view (Left 60%, Right 40%).
- \***\*Left Pane (Interaction)\*\***:
- Top: <Input.TextArea> for entering fault description + "Diagnose" <Button>.
- Bottom: Diagnosis Result <Card>. Use ReactMarkdown to render the "Summary" and "Resolution Steps". Display tags for "Fault Code" and "Component".
- \***\*Right Pane (Evidence)\*\***:
- Title: "Reference Cases".
- Component: <List> showing mock historical cases (ID, Date, Snippet).
- Action: "View" button opens a Modal with full JSON details.

## 3. Page: Analytics Dashboard (Path: /dashboard)

- \***\*Layout\*\***: Grid (Row/Col).
- \***\*Top Bar\*\***: <DatePicker.RangePicker> and <Select> for Device Model.
- \***\*KPI Cards (Row 1)\*\***: 4 Cards (MTBF, Total Failures, Top Component, Last Sync).
- \***\*Main Chart (Row 2)\*\***: "Reliability Trend" (LineChart showing MTBF over time).
- \***\*Secondary Charts (Row 3)\*\***:
- "Top Failing Components" (BarChart, horizontal).
- "Fault Distribution" (PieChart).

# Deliverables

1. Setup the Vite project structure.
2. Create the `Layout` component.
3. Create `Workbench` and `Dashboard` page components.
4. Create a `mockData.ts` file with realistic medical device data to populate the UI (e.g., "X-Ray Tube Overheat", "CT Gantry Noise").
5. Implement the routing using `react-router-dom`.

Please generate the code step-by-step. Start with the project structure and dependencies.

### ---

**💡 如何使用此提示词**

1. **Cursor 用户**: 打开 Ctrl+I (Composer)，粘贴上述内容。它会为你创建文件并写入代码。
2. **v0.dev 用户**: 粘贴内容，它将生成可交互的 UI 原型。
3. **手动开发**: 将此作为你的 README.md 或开发任务清单，逐项完成。

