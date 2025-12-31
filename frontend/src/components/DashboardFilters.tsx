import { Card, DatePicker, Select, Button, Space, Row, Col, Form } from 'antd';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';
import type { AnalyticsFilters } from '../types/analytics';

const { RangePicker } = DatePicker;

interface DashboardFiltersProps {
  onFilterChange: (filters: AnalyticsFilters) => void;
  loading?: boolean;
  equipmentModels?: string[];
}

export default function DashboardFilters({
  onFilterChange,
  loading = false,
  equipmentModels = [
    'All Models',
    'Conveyor-X1',
    'Package-Pro',
    'Sorter-2000',
  ],
}: DashboardFiltersProps) {
  const [form] = Form.useForm();

  const handleSubmit = (values: {
    dateRange?: [Dayjs, Dayjs];
    equipmentModel?: string;
  }) => {
    const filters: AnalyticsFilters = {
      startDate: values.dateRange?.[0]?.toISOString().split('T')[0] || '',
      endDate: values.dateRange?.[1]?.toISOString().split('T')[0] || '',
      equipmentModel:
        values.equipmentModel && values.equipmentModel !== 'All Models'
          ? values.equipmentModel
          : undefined,
    };

    onFilterChange(filters);
  };

  const handleReset = () => {
    form.resetFields();
    const defaultEndDate = dayjs();
    const defaultStartDate = dayjs().subtract(30, 'days');

    onFilterChange({
      startDate: defaultStartDate.toISOString().split('T')[0],
      endDate: defaultEndDate.toISOString().split('T')[0],
      equipmentModel: undefined,
    });
  };

  return (
    <Card title="Filters">
      <Form form={form} onFinish={handleSubmit} layout="vertical">
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={8}>
            <Form.Item
              label="Date Range"
              name="dateRange"
              initialValue={[dayjs().subtract(30, 'days'), dayjs()]}
            >
              <RangePicker
                style={{ width: '100%' }}
                format="YYYY-MM-DD"
                disabled={loading}
              />
            </Form.Item>
          </Col>

          <Col xs={24} sm={12} lg={8}>
            <Form.Item
              label="Equipment Model"
              name="equipmentModel"
              initialValue="All Models"
            >
              <Select
                style={{ width: '100%' }}
                disabled={loading}
                options={equipmentModels.map((model) => ({
                  label: model,
                  value: model,
                }))}
              />
            </Form.Item>
          </Col>

          <Col xs={24} sm={24} lg={8}>
            <Form.Item label="Actions">
              <Space>
                <Button
                  type="primary"
                  onClick={() => form.submit()}
                  loading={loading}
                  icon={<span>🔍</span>}
                >
                  Apply Filters
                </Button>
                <Button onClick={handleReset} disabled={loading}>
                  Reset
                </Button>
              </Space>
            </Form.Item>
          </Col>
        </Row>
      </Form>
    </Card>
  );
}
