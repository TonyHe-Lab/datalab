import { Modal, Descriptions, Typography, Tag, Empty } from 'antd';
import type { ReferenceCase } from '../types/api';

const { Paragraph, Text } = Typography;

interface CaseDetailsModalProps {
  visible: boolean;
  caseData: ReferenceCase;
  onClose: () => void;
}

export default function CaseDetailsModal({
  visible,
  caseData,
  onClose,
}: CaseDetailsModalProps) {
  return (
    <Modal
      title={`Work Order Details: ${caseData.id}`}
      open={visible}
      onCancel={onClose}
      footer={null}
      width={700}
    >
      {caseData.details ? (
        <Descriptions bordered column={1} size="small">
          <Descriptions.Item label="Work Order ID">
            <Text code>{caseData.details.work_order_id}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="Device Model">
            {caseData.details.device_model}
          </Descriptions.Item>
          <Descriptions.Item label="Date">
            {caseData.details.date}
          </Descriptions.Item>
          <Descriptions.Item label="Status">
            <Tag
              color={
                caseData.details.status === 'Resolved'
                  ? 'green'
                  : caseData.details.status === 'Pending'
                  ? 'orange'
                  : 'red'
              }
            >
              {caseData.details.status}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Fault Code">
            <Tag color="red">{caseData.details.fault_code}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Component">
            <Tag color="blue">{caseData.details.component}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Fault Description">
            <Paragraph style={{ marginBottom: 0 }}>
              {caseData.details.fault_description}
            </Paragraph>
          </Descriptions.Item>
          {caseData.details.resolution && (
            <Descriptions.Item label="Resolution">
              <Paragraph style={{ marginBottom: 0 }}>
                {caseData.details.resolution}
              </Paragraph>
            </Descriptions.Item>
          )}
        </Descriptions>
      ) : (
        <Empty description="Detailed information not available" />
      )}
    </Modal>
  );
}
