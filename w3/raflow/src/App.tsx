import { OverlayWindow } from './components/OverlayWindow';
import { SettingsPanel } from './components/SettingsPanel';
import './styles/overlay.css';
import './styles/settings.css';

function App() {
  // 根据窗口 label 决定显示哪个组件
  const isOverlay = window.location.search.includes('overlay');

  if (isOverlay) {
    return <OverlayWindow />;
  }

  return <SettingsPanel />;
}

export default App;
