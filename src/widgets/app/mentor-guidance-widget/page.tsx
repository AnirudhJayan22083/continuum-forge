'use client';

import { useTheme, useWidgetSDK } from '@nitrostack/widgets';

interface MentorGuidanceData {
  scenario?: string;
  instruction?: string;
  verbosity?: 'short' | 'detailed';
}

export default function MentorGuidanceWidget() {
  const theme = useTheme();
  const { getToolOutput } = useWidgetSDK();
  const data = getToolOutput<MentorGuidanceData>();

  const isDark = theme === 'dark';
  const bgColor = isDark ? '#18181b' : '#ffffff';
  const textColor = isDark ? '#f4f4f5' : '#18181b';
  const cardBg = isDark ? '#27272a' : '#f4f4f5';
  const borderColor = isDark ? '#3f3f46' : '#e4e4e7';

  const isCritical = true;

  return (
    <div style={{
      padding: '20px',
      background: bgColor,
      color: textColor,
      borderRadius: '16px',
      border: `2px solid ${isCritical ? '#dc2626' : borderColor}`,
      boxShadow: '0 10px 25px -5px rgba(220, 38, 38, 0.25)',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      width: '100%',
      boxSizing: 'border-box'
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justify: 'space-between',
        marginBottom: '14px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '22px' }}>🚨</span>
          <h3 style={{ margin: 0, fontSize: '17px', fontWeight: 700, color: '#ef4444' }}>
            CRITICAL OPERATIONAL GUIDANCE
          </h3>
        </div>
        <span style={{
          background: isDark ? '#3f3f46' : '#e4e4e7',
          color: isDark ? '#a1a1aa' : '#71717a',
          fontSize: '11px',
          fontWeight: 600,
          padding: '3px 8px',
          borderRadius: '12px',
          textTransform: 'uppercase'
        }}>
          Verbosity: {data?.verbosity || 'short'}
        </span>
      </div>

      <div style={{
        background: cardBg,
        borderRadius: '12px',
        padding: '14px',
        marginBottom: '16px',
        borderLeft: '4px solid #ef4444'
      }}>
        <div style={{ fontSize: '12px', fontWeight: 600, color: '#f59e0b', marginBottom: '6px' }}>
          CURRENT TELEMETRY BREACH
        </div>
        <div style={{ fontSize: '13px', lineHeight: 1.5, opacity: 0.9 }}>
          {data?.scenario || 'Vibration: 5.0 mm/s (> 4.5 mm/s) | Temp: 95°C (> 90°C)'}
        </div>
      </div>

      <div style={{
        background: '#7f1d1d',
        color: '#fef2f2',
        borderRadius: '12px',
        padding: '16px',
        marginBottom: '14px'
      }}>
        <div style={{ fontSize: '13px', fontWeight: 700, marginBottom: '8px', letterSpacing: '0.05em' }}>
          IMMEDIATE ACTION REQUIRED
        </div>
        <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', lineHeight: 1.6 }}>
          <li><strong>SHUTDOWN PUMP-B IMMEDIATELY</strong> — Hit physical emergency stop</li>
          <li>Notify Shift Lead & Maintenance Supervisor immediately</li>
          <li>Do NOT attempt restart before full inspection</li>
        </ul>
      </div>

      <div style={{
        display: 'flex',
        alignItems: 'center',
        justify: 'space-between',
        fontSize: '11px',
        color: isDark ? '#a1a1aa' : '#71717a'
      }}>
        <span>Senior Mentor Persona</span>
        <span style={{ color: '#10b981', fontWeight: 600 }}>Safety Rule Triggered</span>
      </div>
    </div>
  );
}
