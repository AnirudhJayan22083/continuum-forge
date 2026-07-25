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

  return (
    <div style={{
      padding: '24px',
      background: 'linear-gradient(145deg, #180505 0%, #2a0a0a 100%)',
      color: '#fef2f2',
      borderRadius: '20px',
      border: '1px solid rgba(239, 68, 68, 0.4)',
      boxShadow: '0 20px 30px -10px rgba(220, 38, 38, 0.4)',
      fontFamily: "'Inter', system-ui, sans-serif",
      width: '100%',
      boxSizing: 'border-box'
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #ef4444 0%, #991b1b 100%)',
            display: 'flex',
            alignItems: 'center',
            justify: 'center',
            boxShadow: '0 4px 14px rgba(239, 68, 68, 0.5)'
          }}>
            <span style={{ fontSize: '22px' }}>🚨</span>
          </div>
          <div>
            <h3 style={{ margin: 0, fontSize: '17px', fontWeight: 800, color: '#fca5a5', letterSpacing: '-0.02em' }}>
              CRITICAL OPERATIONAL GUIDANCE
            </h3>
            <span style={{ fontSize: '12px', color: '#f87171', fontWeight: 500 }}>Immediate Senior Mentor Protocol</span>
          </div>
        </div>

        <span style={{
          background: 'rgba(239, 68, 68, 0.2)',
          color: '#fca5a5',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          fontSize: '11px',
          fontWeight: 700,
          padding: '4px 12px',
          borderRadius: '20px',
          textTransform: 'uppercase',
          letterSpacing: '0.05em'
        }}>
          VERBOSITY: {data?.verbosity || 'short'}
        </span>
      </div>

      {/* Telemetry Breach Box */}
      <div style={{
        background: 'rgba(15, 23, 42, 0.7)',
        backdropFilter: 'blur(10px)',
        borderRadius: '14px',
        padding: '16px',
        marginBottom: '18px',
        borderLeft: '4px solid #ef4444',
        border: '1px solid rgba(239, 68, 68, 0.2)'
      }}>
        <div style={{ fontSize: '11px', fontWeight: 800, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '6px' }}>
          ⚠️ DETECTED TELEMETRY BREACH
        </div>
        <div style={{ fontSize: '13px', lineHeight: '1.5', fontFamily: "'JetBrains Mono', monospace", color: '#fca5a5' }}>
          {data?.scenario || 'Vibration: 5.0 mm/s (EXCEEDS 4.5) | Temp: 95°C (EXCEEDS 90°C)'}
        </div>
      </div>

      {/* Immediate Action Checklist */}
      <div style={{
        background: 'linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%)',
        borderRadius: '14px',
        padding: '18px',
        marginBottom: '16px',
        boxShadow: '0 8px 16px rgba(127, 29, 29, 0.4)',
        border: '1px solid rgba(254, 202, 202, 0.2)'
      }}>
        <div style={{ fontSize: '12px', fontWeight: 800, letterSpacing: '0.08em', color: '#ffffff', marginBottom: '10px' }}>
          ACTION CHECKLIST (EXECUTE IMMEDIATELY)
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ background: '#ef4444', color: '#fff', borderRadius: '50%', width: '20px', height: '20px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 800 }}>1</span>
            <strong>ACTIVATE EMERGENCY SHUTDOWN PUMP-B IMMEDIATELY</strong>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ background: '#ef4444', color: '#fff', borderRadius: '50%', width: '20px', height: '20px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 800 }}>2</span>
            <span>Notify Shift Lead & Maintenance Supervisor</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ background: '#ef4444', color: '#fff', borderRadius: '50%', width: '20px', height: '20px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 800 }}>3</span>
            <span>Do NOT restart before physical bearing inspection</span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justify: 'space-between',
        fontSize: '11px',
        color: '#f87171'
      }}>
        <span style={{ fontWeight: 600 }}>Senior Mentor Persona</span>
        <span style={{ color: '#34d399', fontWeight: 700 }}>Preventive Safety Rule Active</span>
      </div>
    </div>
  );
}
