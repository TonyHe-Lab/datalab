import { useState } from 'react';
import { Row, Col, Typography } from 'antd';
import { useQuery } from '@tanstack/react-query';
import DiagnosisInput from '../components/DiagnosisInput';
import DiagnosisResult from '../components/DiagnosisResult';
import ReferenceCases from '../components/ReferenceCases';
import { chatService, searchService } from '../services/chat';
import type { DiagnosisResponse } from '../types/api';

const { Title } = Typography;

export default function WorkbenchPage() {
  const [faultDescription, setFaultDescription] = useState('');
  const [diagnosis, setDiagnosis] = useState<DiagnosisResponse | null>(null);

  const { data: referenceCases = [], isLoading: isLoadingReferences } = useQuery({
    queryKey: ['search', faultDescription],
    queryFn: () => searchService.searchSimilarCases(faultDescription),
    enabled: faultDescription.length > 0,
  });

  const handleDiagnose = async (query: string) => {
    try {
      setFaultDescription(query);
      const result = await chatService.diagnose({ query });
      setDiagnosis(result);
    } catch (error) {
      console.error('Diagnosis failed:', error);
      throw error;
    }
  };

  return (
    <div style={{ padding: '24px', minHeight: '100vh', background: '#f0f2f5' }}>
      <Title level={2} style={{ marginBottom: '24px' }}>
        Diagnostic Workbench
      </Title>
      <div style={{ background: '#fff', minHeight: '600px', borderRadius: '8px', padding: '24px' }}>
        <Row gutter={24}>
          <Col span={14}>
            <DiagnosisInput onDiagnose={handleDiagnose} />
            <DiagnosisResult diagnosis={diagnosis} />
          </Col>
          <Col span={10}>
            <div style={{ background: '#fafafa', padding: '24px', borderRadius: '8px', height: '100%' }}>
              <ReferenceCases cases={referenceCases} loading={isLoadingReferences} />
            </div>
          </Col>
        </Row>
      </div>
    </div>
  );
}
