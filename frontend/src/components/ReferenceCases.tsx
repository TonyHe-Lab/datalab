import { useState } from 'react';
import { Card, List, Typography, Empty, Button, Tag } from 'antd';
import { FileTextOutlined, EyeOutlined } from '@ant-design/icons';
import type { ReferenceCase } from '../types/api';
import CaseDetailsModal from './CaseDetailsModal';

const { Title, Text, Paragraph } = Typography;

interface ReferenceCasesProps {
  cases: ReferenceCase[];
  loading?: boolean;
}

export default function ReferenceCases({ cases, loading }: ReferenceCasesProps) {
  const [selectedCase, setSelectedCase] = useState<ReferenceCase | null>(null);
  const [modalVisible, setModalVisible] = useState(false);

  const handleViewDetails = (caseItem: ReferenceCase) => {
    setSelectedCase(caseItem);
    setModalVisible(true);
  };

  const handleCloseModal = () => {
    setModalVisible(false);
  };

  if (loading) {
    return (
      <div>
        <Title level={4} style={{ marginBottom: '16px' }}>
          Reference Cases
        </Title>
        {[1, 2, 3].map((i) => (
          <Card key={i} loading={loading} style={{ marginBottom: '12px' }} />
        ))}
      </div>
    );
  }

  if (!cases || cases.length === 0) {
    return (
      <div>
        <Title level={4} style={{ marginBottom: '16px' }}>
          Reference Cases
        </Title>
        <Card>
          <Empty
            description="Enter a fault description to see similar historical cases"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        </Card>
      </div>
    );
  }

  return (
    <div>
      <Title level={4} style={{ marginBottom: '16px' }}>
        Reference Cases ({cases.length})
      </Title>

      <List
        dataSource={cases}
        renderItem={(caseItem) => (
          <Card
            key={caseItem.id}
            size="small"
            style={{ marginBottom: '12px', cursor: 'pointer' }}
            hoverable
            onClick={() => handleViewDetails(caseItem)}
          >
            <List.Item style={{ display: 'block', padding: 0 }}>
              <div style={{ marginBottom: '8px' }}>
                <Tag color="blue" icon={<FileTextOutlined />}>
                  {caseItem.id}
                </Tag>
                <Text type="secondary" style={{ marginLeft: '8px', fontSize: '12px' }}>
                  {caseItem.date}
                </Text>
              </div>
              <Paragraph
                ellipsis={{ rows: 2 }}
                style={{ marginBottom: 0, color: '#000000d9' }}
              >
                {caseItem.snippet}
              </Paragraph>
              <Button
                type="link"
                icon={<EyeOutlined />}
                style={{ marginTop: '8px', padding: 0 }}
                onClick={(e) => {
                  e.stopPropagation();
                  handleViewDetails(caseItem);
                }}
              >
                View Details
              </Button>
            </List.Item>
          </Card>
        )}
      />

      {selectedCase && (
        <CaseDetailsModal
          visible={modalVisible}
          caseData={selectedCase}
          onClose={handleCloseModal}
        />
      )}
    </div>
  );
}
