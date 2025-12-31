import type { ThemeConfig } from 'antd';

export const ThemeProvider: ThemeConfig = {
  token: {
    colorPrimary: '#1890ff',
    colorBgBase: '#ffffff',
    borderRadius: 6,
    fontSize: 14,
  },
  components: {
    Button: {
      borderRadius: 6,
    },
    Layout: {
      headerBg: '#001529',
      siderBg: '#001529',
    },
  },
};
