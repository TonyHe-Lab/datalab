import { Card, Typography } from 'antd'

const { Title } = Typography

export function Chat() {
  return (
    <div>
      <Title level={2}>AI Chat Assistant</Title>
      <Card>
        <p>Chat interface will be implemented with RAG backend integration</p>
      </Card>
    </div>
  )
}
