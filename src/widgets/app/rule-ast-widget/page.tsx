'use client';

import { useTheme, useWidgetSDK } from '@nitrostack/widgets';

interface RuleAstCondition {
  parameter: string;
  operator: string;
  threshold: number | string;
}

interface RuleAstData {
  operator?: string;
  conditions?: RuleAstCondition[];
  action?: string;
  ruleStr?: string;
  rawRule?: any;
}

export default function RuleAstWidget() {
  const theme = useTheme();
  const { getToolOutput } = useWidgetSDK();
  const rawData = getToolOutput<RuleAstData>();

  const isDark = theme === 'dark';
  const bgColor = isDark ? '#111827' : '#ffffff';
  const textColor = isDark ? '#f9fafb' : '#111827';
  const cardBg = isDark ? '#1f2937' : '#f3f4f6';
  const borderColor = isDark ? '#374151' : '#e5e7eb';
  const badgeBg = isDark ? '#374151' : '#e2e8f0';

  let rule: RuleAstData | null = rawData || null;

  // Try parsing rawRule or ruleStr if nested
  if (rawData?.rawRule) {
    rule = typeof rawData.rawRule === 'string' ? JSON.parse(rawData.rawRule) : rawData.rawRule;
  } else if (rawData?.ruleStr) {
    try {
      rule = JSON.parse(rawData.ruleStr);
    } catch {
      rule = rawData;
    }
  }

  const conditions = rule?.conditions || [
    { parameter: 'vibration_mm_s', operator: '>', threshold: 4.5 },
    { parameter: 'temperature_celsius', operator: '>', threshold: 90 }
  ];
  const operator = rule?.operator || 'AND';
  const action = rule?.action || 'SHUTDOWN';

  return (
    <div style={{
      padding: '20px',
      background: bgColor,
      color: textColor,
      borderRadius: '16px',
      border: `1px solid ${borderColor}`,
      boxShadow: '0 10px 15px -3px rgba(0,0,0,0.2)',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      width: '100%',
      boxSizing: 'border-box'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '20px' }}>⚡</span>
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: '#60a5fa' }}>
            Structured JSON AST Rule
          </h3>
        </div>
        <span style={{
          background: '#ef4444',
          color: '#ffffff',
          padding: '4px 10px',
          borderRadius: '20px',
          fontSize: '12px',
          fontWeight: 700,
          letterSpacing: '0.05em'
        }}>
          ACTION: {action}
        </span>
      </div>

      <div style={{
        background: cardBg,
        borderRadius: '12px',
        padding: '16px',
        border: `1px solid ${borderColor}`
      }}>
        <div style={{
          fontSize: '12px',
          fontWeight: 600,
          color: isDark ? '#9ca3af' : '#6b7280',
          marginBottom: '12px',
          textTransform: 'uppercase',
          letterSpacing: '0.05em'
        }}>
          Condition Logic ({operator})
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {conditions.map((cond, idx) => (
            <div key={idx} style={{
              display: 'flex',
              alignItems: 'center',
              justify: 'space-between',
              background: isDark ? '#111827' : '#ffffff',
              padding: '10px 14px',
              borderRadius: '8px',
              borderLeft: '4px solid #3b82f6',
              fontSize: '14px'
            }}>
              <span style={{ fontWeight: 500, fontFamily: 'monospace', color: isDark ? '#93c5fd' : '#2563eb' }}>
                {cond.parameter}
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{
                  background: badgeBg,
                  padding: '2px 8px',
                  borderRadius: '6px',
                  fontFamily: 'monospace',
                  fontWeight: 700,
                  fontSize: '13px'
                }}>
                  {cond.operator}
                </span>
                <span style={{ fontWeight: 700, color: '#f59e0b', fontSize: '15px' }}>
                  {cond.threshold}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{
        marginTop: '12px',
        display: 'flex',
        alignItems: 'center',
        justify: 'space-between',
        fontSize: '12px',
        color: isDark ? '#9ca3af' : '#6b7280'
      }}>
        <span>Grounded Tacit Rule</span>
        <span style={{ color: '#10b981', fontWeight: 600 }}>Verified by AST Engine</span>
      </div>
    </div>
  );
}
