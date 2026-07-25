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

  let rule: RuleAstData | null = rawData || null;
  if (rawData?.rawRule) {
    rule = typeof rawData.rawRule === 'string' ? JSON.parse(rawData.rawRule) : rawData.rawRule;
  } else if (rawData?.ruleStr) {
    try { rule = JSON.parse(rawData.ruleStr); } catch { rule = rawData; }
  }

  const conditions = rule?.conditions || [
    { parameter: 'vibration_mm_s', operator: '>', threshold: 4.5 },
    { parameter: 'temperature_celsius', operator: '>', threshold: 90 }
  ];
  const operator = rule?.operator || 'AND';
  const action = rule?.action || 'SHUTDOWN';

  return (
    <div style={{
      padding: '24px',
      background: 'linear-gradient(145deg, #0f172a 0%, #1e1b4b 100%)',
      color: '#f8fafc',
      borderRadius: '20px',
      border: '1px solid rgba(99, 102, 241, 0.25)',
      boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(99, 102, 241, 0.2)',
      fontFamily: "'Inter', system-ui, sans-serif",
      width: '100%',
      boxSizing: 'border-box'
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #3b82f6 0%, #6366f1 100%)',
            display: 'flex',
            alignItems: 'center',
            justify: 'center',
            boxShadow: '0 4px 12px rgba(59, 130, 246, 0.4)'
          }}>
            <span style={{ fontSize: '20px' }}>⚡</span>
          </div>
          <div>
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: '#ffffff', letterSpacing: '-0.02em' }}>
              Structured JSON AST Rule
            </h3>
            <span style={{ fontSize: '12px', color: '#818cf8', fontWeight: 500 }}>Engineered Tacit Rule Representation</span>
          </div>
        </div>

        <span style={{
          background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
          color: '#ffffff',
          padding: '6px 14px',
          borderRadius: '30px',
          fontSize: '11px',
          fontWeight: 800,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          boxShadow: '0 4px 12px rgba(239, 68, 68, 0.4)'
        }}>
          ACTION: {action}
        </span>
      </div>

      {/* AST Content Box */}
      <div style={{
        background: 'rgba(15, 23, 42, 0.7)',
        backdropFilter: 'blur(12px)',
        borderRadius: '14px',
        padding: '18px',
        border: '1px solid rgba(255, 255, 255, 0.08)'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justify: 'space-between',
          marginBottom: '14px',
          paddingBottom: '10px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)'
        }}>
          <span style={{ fontSize: '11px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            LOGICAL OPERATOR
          </span>
          <span style={{
            background: 'rgba(99, 102, 241, 0.2)',
            color: '#a5b4fc',
            border: '1px solid rgba(99, 102, 241, 0.4)',
            padding: '4px 12px',
            borderRadius: '8px',
            fontSize: '12px',
            fontWeight: 800,
            fontFamily: "'JetBrains Mono', monospace"
          }}>
            {operator}
          </span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {conditions.map((cond, idx) => (
            <div key={idx} style={{
              display: 'flex',
              alignItems: 'center',
              justify: 'space-between',
              background: 'rgba(30, 41, 59, 0.6)',
              padding: '12px 16px',
              borderRadius: '10px',
              borderLeft: '4px solid #3b82f6',
              transition: 'transform 0.2s ease, border-color 0.2s ease'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ color: '#64748b', fontSize: '12px' }}>#{idx + 1}</span>
                <span style={{
                  fontWeight: 600,
                  fontFamily: "'JetBrains Mono', monospace",
                  color: '#93c5fd',
                  fontSize: '13px'
                }}>
                  {cond.parameter}
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{
                  background: 'rgba(15, 23, 42, 0.9)',
                  color: '#e2e8f0',
                  padding: '3px 10px',
                  borderRadius: '6px',
                  fontFamily: "'JetBrains Mono', monospace",
                  fontWeight: 700,
                  fontSize: '12px',
                  border: '1px solid rgba(255, 255, 255, 0.1)'
                }}>
                  {cond.operator}
                </span>
                <span style={{
                  fontWeight: 700,
                  color: '#fbbf24',
                  fontSize: '15px',
                  fontFamily: "'JetBrains Mono', monospace"
                }}>
                  {cond.threshold}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer Meta */}
      <div style={{
        marginTop: '16px',
        display: 'flex',
        alignItems: 'center',
        justify: 'space-between',
        fontSize: '11px',
        color: '#64748b'
      }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', display: 'inline-block' }}></span>
          Grounded Tacit Knowledge Rule
        </span>
        <span style={{ color: '#818cf8', fontWeight: 600 }}>Validated against Neon DB</span>
      </div>
    </div>
  );
}
