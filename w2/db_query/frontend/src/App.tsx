import { ConfigProvider, App as AntdApp, theme } from "antd";
import { Home } from "./pages/Home";
import "@refinedev/antd/dist/reset.css";

// MotherDuck-inspired theme
const motherDuckTheme = {
  algorithm: theme.defaultAlgorithm,
  token: {
    colorPrimary: '#6FC2FF',
    colorSuccess: '#16AA98',
    colorWarning: '#FFDE00',
    colorError: '#FF7169',
    colorInfo: '#6FC2FF',
    colorBgBase: '#F4EFEA',
    colorBgContainer: '#FFFFFF',
    colorBgLayout: '#F4EFEA',
    colorText: '#383838',
    colorTextSecondary: '#A1A1A1',
    colorBorder: '#000000',
    borderRadius: 2,
    fontSize: 15,
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    fontSizeHeading1: 32,
    fontSizeHeading2: 24,
    fontSizeHeading3: 18,
    lineHeight: 1.5,
    lineHeightHeading: 1.25,
  },
  components: {
    Button: {
      borderRadius: 2,
      controlHeight: 40,
      fontSize: 14,
      fontWeight: 700,
      primaryShadow: 'none',
    },
    Input: {
      borderRadius: 2,
      controlHeight: 40,
      fontSize: 15,
    },
    Card: {
      borderRadius: 2,
      boxShadow: 'none',
    },
    Table: {
      borderRadius: 2,
      fontSize: 15,
      headerBg: '#F8F8F7',
      headerColor: '#383838',
      rowHoverBg: '#EBF9FF',
    },
    Tree: {
      fontSize: 14,
    },
  },
};

function App() {
  return (
    <ConfigProvider theme={motherDuckTheme}>
      <AntdApp>
        <Home />
      </AntdApp>
    </ConfigProvider>
  );
}

export default App;
