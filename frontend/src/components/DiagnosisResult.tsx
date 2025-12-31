import { Card, Typography, Tag, Collapse, Empty, Skeleton } from 'antd';
import ReactMarkdown from 'react-markdown';
import type { DiagnosisResponse } from '../types/api';

const { Title, Text, Paragraph } = Typography;

interface DiagnosisResultProps {
  diagnosis: DiagnosisResponse | null;
}

export default function DiagnosisResult({ diagnosis }: DiagnosisResultProps) {
  if (!diagnosis) {
    return (
      <Card>
        <Empty
          description="Enter a fault description and click Diagnose to get AI-powered diagnostic suggestions"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    );
  }

  const items = [
    ...(diagnosis.resolution_steps?.map((step, index) => ({
      key: index,
      label: `Step ${index + 1}`,
      children: <Paragraph>{step}</Paragraph>,
    })) || []),
  ];

  return (
    <div>
      <Card style={{ marginBottom: '16px' }}>
        <Title level={4} style={{ marginBottom: '16px' }}>
          AI Diagnosis
        </Title>

        <div style={{ marginBottom: '16px' }}>
          <Text strong>Fault Code:</Text>{' '}
          {diagnosis.fault_code ? (
            <Tag color="red">{diagnosis.fault_code}</Tag>
          ) : (
            <Text type="secondary">N/A</Text>
          )}
        </div>

        <div style={{ marginBottom: '16px' }}>
          <Text strong>Component:</Text>{' '}
          {diagnosis.component ? (
            <Tag color="blue">{diagnosis.component}</Tag>
          ) : (
            <Text type="secondary">N/A</Text>
          )}
        </div>

        {diagnosis.summary && (
          <div style={{ marginBottom: '16px' }}>
            <Text strong>Summary:</Text>
            <Paragraph style={{ marginBottom: 0 }}>
              {diagnosis.summary}
            </Paragraph>
          </div>
        )}

        <div>
          <Text strong>Detailed Analysis:</Text>
          <ReactMarkdown
            components={{
              p: ({ children }) => <Paragraph style={{ marginBottom: '8px' }}>{children}</Paragraph>,
              ul: ({ children }) => <ul style={{ marginBottom: '8px' }}>{children}</ul>,
              ol: ({ children }) => <ol style={{ marginBottom: '8px' }}>{children}</ol>,
              li: ({ children }) => <li>{children}</li>,
              code: ({ children }) => (
                <code
                  style={{
                    background: '#f5f5f5',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    fontSize: '0.9em',
                  }}
                >
                  {children}
                </code>
              ),
              strong: ({ children }) => <strong>{children}</strong>,
            }}
          >
            {diagnosis.answer}
          </ReactMarkdown>
        </div>
      </Card>

      {items.length > 0 && (
        <Card title="Resolution Steps">
          <Collapse items={items} defaultActiveKey={[]} />
        </Card>
      )}
    </div>
  );
}

export function DiagnosisResultSkeleton() {
  return (
    <Card>
      <Skeleton active paragraph={{ rows: 6 }} />
    </Card>
  );
}
