import { Card, Statistic, Typography } from 'antd';
import {
  ThunderboltOutlined,
  AlertOutlined,
  InfoCircleOutlined,
  SyncOutlined,
} from '@ant-design/icons';
import type { ReactNode } from 'react';

const { Text } = Typography;

interface KPICardProps {
  title: string;
  value: number | string;
  icon: ReactNode;
  suffix?: string;
  precision?: number;
  loading?: boolean;
}

export function KPICard({
  title,
  value,
  icon,
  suffix = '',
  precision = 0,
  loading = false,
}: KPICardProps) {
  let displayValue: number | undefined;
  if (typeof value === 'number') {
    displayValue = value;
  }

  return (
    <Card
      hoverable
      loading={loading}
      styles={{ body: { paddingTop: '16px', paddingBottom: '16px' } }}
    >
      <Statistic
        title={
          <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {icon}
            <Text type="secondary">{title}</Text>
          </span>
        }
        value={displayValue}
        suffix={suffix}
        precision={precision}
        styles={{ content: { color: '#3f8600' } }}
      />
    </Card>
  );
}

interface DashboardKPIProps {
  summary?: {
    mtbf: number;
    total_failures: number;
    top_component: string;
    last_sync: string;
  };
  loading?: boolean;
}

export function DashboardKPI({
  summary,
  loading = false,
}: DashboardKPIProps) {
  if (!summary) {
    return (
      <>
        <KPICard
          title="MTBF"
          value={0}
          icon={<ThunderboltOutlined />}
          loading={loading}
        />
        <KPICard
          title="Total Failures"
          value={0}
          icon={<AlertOutlined />}
          loading={loading}
        />
        <KPICard
          title="Top Component"
          value="N/A"
          icon={<InfoCircleOutlined />}
          loading={loading}
        />
        <KPICard
          title="Last Sync"
          value="N/A"
          icon={<SyncOutlined />}
          loading={loading}
        />
      </>
    );
  }

  return (
    <>
      <KPICard
        title="MTBF"
        value={summary.mtbf}
        suffix="hrs"
        precision={1}
        icon={<ThunderboltOutlined />}
        loading={loading}
      />
      <KPICard
        title="Total Failures"
        value={summary.total_failures}
        icon={<AlertOutlined />}
        loading={loading}
      />
      <KPICard
        title="Top Component"
        value={summary.top_component}
        icon={<InfoCircleOutlined />}
        loading={loading}
      />
      <KPICard
        title="Last Sync"
        value={formatLastSync(summary.last_sync)}
        icon={<SyncOutlined />}
        loading={loading}
      />
    </>
  );
}

function formatLastSync(dateStr: string): string {
  if (!dateStr) return 'N/A';

  try {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) {
      return `${diffMins}m ago`;
    } else if (diffHours < 24) {
      return `${diffHours}h ago`;
    } else if (diffDays < 7) {
      return `${diffDays}d ago`;
    } else {
      return date.toLocaleDateString();
    }
  } catch {
    return 'N/A';
  }
}
