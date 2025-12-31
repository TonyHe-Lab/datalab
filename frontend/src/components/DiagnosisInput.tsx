import { useState } from 'react';
import { Button, Card, Form, Input, Typography, Space } from 'antd';
import { SendOutlined } from '@ant-design/icons';

const { TextArea } = Input;
const { Title } = Typography;

interface DiagnosisInputProps {
  onDiagnose: (query: string) => void;
}

export default function DiagnosisInput({ onDiagnose }: DiagnosisInputProps) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (values: { description: string }) => {
    if (!values.description.trim()) return;

    setLoading(true);
    try {
      await onDiagnose(values.description);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to diagnose';
      form.setFields([{ name: 'description', errors: [errorMessage] }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card style={{ marginBottom: '24px' }}>
      <Title level={4} style={{ marginBottom: '16px' }}>
        Enter Fault Description
      </Title>
      <Form form={form} layout="vertical" onFinish={handleSubmit}>
        <Form.Item
          name="description"
          rules={[
            { required: true, message: 'Please enter a fault description' },
            { min: 10, message: 'Description must be at least 10 characters' },
          ]}
        >
          <TextArea
            rows={6}
            placeholder="Describe the fault you're experiencing... (e.g., 'The conveyor belt at station 3 is making unusual noises and stops intermittently')"
            maxLength={500}
            showCount
            disabled={loading}
          />
        </Form.Item>
        <Form.Item>
          <Space>
            <Button
              type="primary"
              htmlType="submit"
              icon={<SendOutlined />}
              loading={loading}
              size="large"
            >
              Diagnose
            </Button>
            <Button
              onClick={() => {
                form.resetFields();
              }}
              disabled={loading}
            >
              Clear
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  );
}
