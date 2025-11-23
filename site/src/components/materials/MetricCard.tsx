/**
 * MetricCard - 指标卡片组件（MotherDuck 风格）
 * 用于展示关键指标如价格、速度、上下文窗口等
 */

interface MetricItem {
  provider?: string;
  label?: string;
  value: string | number;
  unit?: string;
  color: string;
  icon?: string;
  description?: string;
  note?: string;
}

interface MetricCardProps {
  title: string;
  items: MetricItem[];
  type?: 'bar' | 'number' | 'badge';
  showComparison?: boolean;
}

export default function MetricCard({
  title,
  items = [],
  type = 'number',
  showComparison = false,
}: MetricCardProps) {
  const getMaxValue = () => {
    if (type !== 'bar') return null;
    return Math.max(...items.map((item) => parseFloat(String(item.value)) || 0));
  };

  const getPercentage = (value: string | number) => {
    const max = getMaxValue();
    if (!max) return 0;
    return (parseFloat(String(value)) / max) * 100;
  };

  return (
    <div
      className="p-xl"
      style={{
        borderRadius: 0,
        backgroundColor: 'var(--md-white)',
        border: '1px solid var(--md-neutral-300)',
        boxShadow: 'var(--shadow-sm)',
      }}
    >
      <h4
        className="text-h3 font-semibold"
        style={{
          color: 'var(--md-neutral-900)',
          marginTop: 0,
          marginBottom: 'var(--space-lg)',
        }}
      >
        {title}
      </h4>

      {/* Bar Type */}
      {type === 'bar' && (
        <div>
          {items.map((item, idx) => (
            <div
              key={idx}
              style={{
                marginBottom: idx < items.length - 1 ? 'var(--space-lg)' : 0,
              }}
            >
              <div className="flex items-center justify-between" style={{ marginBottom: 'var(--space-sm)' }}>
                <div className="flex items-center gap-sm">
                  {item.icon && <span className="text-xl">{item.icon}</span>}
                  <span
                    className="text-body font-medium"
                    style={{ color: 'var(--md-neutral-900)' }}
                  >
                    {item.provider || item.label}
                  </span>
                </div>
                <span
                  className="text-body font-semibold"
                  style={{ color: item.color }}
                >
                  {item.description || item.value}
                  {item.unit && (
                    <span
                      className="text-small ml-1"
                      style={{ color: 'var(--md-neutral-700)' }}
                    >
                      {item.unit}
                    </span>
                  )}
                </span>
              </div>
              <div
                className="h-2 overflow-hidden"
                style={{ backgroundColor: 'var(--md-neutral-100)', borderRadius: 0 }}
              >
                <div
                  className="h-full transition-all duration-500"
                  style={{
                    borderRadius: 0,
                    width: `${getPercentage(item.value)}%`,
                    backgroundColor: item.color,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Number Type */}
      {type === 'number' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-md">
          {items.map((item, idx) => (
            <div
              key={idx}
              className="group relative overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-lg"
              style={{
                borderRadius: 0,
                backgroundColor: 'var(--md-white)',
                border: '2px solid var(--md-graphite)',
                padding: 'var(--space-5)',
              }}
            >
              {/* 左侧色块指示器 */}
              <div
                className="absolute left-0 top-0 bottom-0 w-1 transition-all duration-300 group-hover:w-2"
                style={{
                  backgroundColor: item.color,
                }}
              />

              {/* 内容区域 */}
              <div style={{ paddingLeft: 'var(--space-3)' }}>
                {/* 标签 */}
                <div
                  className="text-ui font-semibold mb-3"
                  style={{
                    color: 'var(--md-ink)',
                    lineHeight: '1.4',
                  }}
                >
                  {item.label || item.provider}
                </div>

                {/* 数值和单位 */}
                <div className="flex items-baseline gap-2">
                  <span
                    className="font-bold transition-colors duration-300"
                    style={{
                      fontSize: '2.5rem',
                      color: item.color,
                      lineHeight: '1',
                      fontFamily: 'var(--font-family-mono)',
                    }}
                  >
                    {item.value}
                  </span>
                  {item.unit && (
                    <span
                      className="text-h3 font-medium"
                      style={{
                        color: 'var(--md-slate)',
                      }}
                    >
                      {item.unit}
                    </span>
                  )}
                </div>

                {/* 备注 */}
                {item.note && (
                  <div
                    className="text-tiny mt-3"
                    style={{
                      color: 'var(--md-slate)',
                      lineHeight: '1.4',
                    }}
                  >
                    {item.note}
                  </div>
                )}
              </div>

              {/* Hover 效果背景 */}
              <div
                className="absolute inset-0 opacity-0 group-hover:opacity-5 transition-opacity duration-300 pointer-events-none"
                style={{
                  backgroundColor: item.color,
                }}
              />
            </div>
          ))}
        </div>
      )}

      {/* Badge Type */}
      {type === 'badge' && (
        <div className="flex flex-wrap gap-md">
          {items.map((item, idx) => (
            <div
              key={idx}
              className="flex items-center gap-sm p-md border-2 transition-all duration-200 hover:scale-105"
              style={{
                borderRadius: 0,
                borderColor: item.color,
                backgroundColor: `${item.color}10`,
              }}
            >
              {item.icon && <span className="text-xl">{item.icon}</span>}
              <div>
                <div
                  className="text-tiny"
                  style={{ color: 'var(--md-neutral-700)' }}
                >
                  {item.provider}
                </div>
                <div
                  className="text-body font-semibold"
                  style={{ color: item.color }}
                >
                  {item.value}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
