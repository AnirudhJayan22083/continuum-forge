'use client';

import { useState } from 'react';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  widgets?: Array<{
    title: string;
    type: 'ast' | 'database' | 'mentor';
    data?: any;
  }>;
}

export default function ContinuumDashboard() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      sender: 'assistant',
      text: '👋 Welcome to **Continuum Forge** — Tacit Knowledge Capture & Transfer Engine.\n\nI can help you codify expert rules of thumb, validate them against your Neon PostgreSQL database, and provide instant coaching to junior operators.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [inputPrompt, setInputPrompt] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const runScenario = (promptText: string) => {
    setInputPrompt(promptText);
    handleSend(promptText);
  };

  const handleSend = (overrideText?: string) => {
    const textToSend = overrideText || inputPrompt;
    if (!textToSend.trim() || isProcessing) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputPrompt('');
    setIsProcessing(true);

    // Simulate real-time MCP Master Orchestrator Pipeline execution with Widgets
    setTimeout(() => {
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: '🚨 **MASTER ORCHESTRATOR PIPELINE - PUMP B CRITICAL ALERT**\n\n' +
          '✅ **Codification & Rule Generation**: Expert rule codified into Structured JSON AST.\n' +
          '📊 **Database Validation**: Checked 20 historical readings on `MACHINE-B`. No prior incidents exceeded both thresholds simultaneously.\n\n' +
          '🚨 **IMMEDIATE ACTION FOR JUNIOR TECH**:\n' +
          '• **ACTIVATE EMERGENCY SHUTDOWN** — Kill power to Pump B immediately.\n' +
          '• **NOTIFY SHIFT LEAD** — Report incident.\n' +
          '• **LOG READINGS** — Vibration: 5.0 mm/s, Temp: 95°C.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        widgets: [
          {
            title: 'Structured JSON AST Rule',
            type: 'ast',
            data: {
              operator: 'AND',
              conditions: [
                { parameter: 'vibration_mm_s', operator: '>', threshold: 4.5 },
                { parameter: 'temperature_celsius', operator: '>', threshold: 90 }
              ],
              action: 'SHUTDOWN'
            }
          },
          {
            title: 'Critical Operational Guidance',
            type: 'mentor',
            data: {
              scenario: 'Vibration: 5.0 mm/s (EXCEEDS 4.5) | Temp: 95°C (EXCEEDS 90)',
              verbosity: 'short'
            }
          }
        ]
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setIsProcessing(false);
    }, 1200);
  };

  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      width: '100vw',
      background: '#090d16',
      color: '#f3f4f6',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      overflow: 'hidden'
    }}>
      {/* LEFT SIDEBAR: Pipeline & System Navigation */}
      <div style={{
        width: '280px',
        background: '#111827',
        borderRight: '1px solid #1f2937',
        display: 'flex',
        flexDirection: 'column',
        padding: '20px',
        boxSizing: 'border-box'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
            display: 'flex',
            alignItems: 'center',
            justify: 'center',
            fontWeight: 800,
            fontSize: '18px'
          }}>
            ⚡
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: '#ffffff' }}>CONTINUUM FORGE</h1>
            <span style={{ fontSize: '11px', color: '#10b981', fontWeight: 600 }}>● NitroStack MCP Active</span>
          </div>
        </div>

        <div style={{ fontSize: '11px', fontWeight: 700, color: '#6b7280', textTransform: 'uppercase', marginBottom: '12px' }}>
          7-Step Knowledge Pipeline
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '24px' }}>
          {[
            { step: '1', title: 'Grounding Interview', active: true },
            { step: '2', title: 'Codification (JSON AST)', active: true },
            { step: '3', title: 'Parameter Extraction', active: true },
            { step: '4', title: 'Database Validation', active: true },
            { step: '5', title: 'Explainability Engine', active: true },
            { step: '6', title: 'Rule Codification', active: true },
            { step: '7', title: 'Mentor Coaching', active: true }
          ].map((item) => (
            <div key={item.step} style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              padding: '8px 12px',
              borderRadius: '8px',
              background: item.active ? 'rgba(59, 130, 246, 0.1)' : 'transparent',
              border: item.active ? '1px solid rgba(59, 130, 246, 0.2)' : 'none',
              fontSize: '13px'
            }}>
              <span style={{
                width: '20px',
                height: '20px',
                borderRadius: '50%',
                background: '#3b82f6',
                color: '#fff',
                fontSize: '11px',
                display: 'flex',
                alignItems: 'center',
                justify: 'center',
                fontWeight: 700
              }}>{item.step}</span>
              <span style={{ color: '#e5e7eb' }}>{item.title}</span>
            </div>
          ))}
        </div>

        <div style={{ marginTop: 'auto', paddingTop: '16px', borderTop: '1px solid #1f2937' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#6b7280', textTransform: 'uppercase', marginBottom: '8px' }}>
            Observability Telemetry
          </div>
          <a
            href="https://jp.cloud.langfuse.com"
            target="_blank"
            rel="noreferrer"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              color: '#60a5fa',
              textDecoration: 'none',
              fontSize: '13px',
              fontWeight: 500,
              padding: '8px 12px',
              background: '#1f2937',
              borderRadius: '8px'
            }}
          >
            📊 View Langfuse Traces ↗
          </a>
        </div>
      </div>

      {/* CENTER AREA: Chat Interface with Inline Widgets */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        background: '#0b1120',
        position: 'relative'
      }}>
        {/* Top Header */}
        <div style={{
          height: '60px',
          borderBottom: '1px solid #1f2937',
          display: 'flex',
          alignItems: 'center',
          justify: 'space-between',
          padding: '0 24px',
          background: '#090d16'
        }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '15px', fontWeight: 600 }}>Master Orchestrator Assistant</h2>
            <span style={{ fontSize: '12px', color: '#9ca3af' }}>Pump-B Motor Burnout Real-Time Telemetry & Rule Engine</span>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => runScenario("Run master orchestrator for Pump B burnout: Vibration > 4.5 mm/s, Temp > 90C. Current: 5.0 mm/s and 95C.")}
              style={{
                background: '#dc2626',
                color: '#fff',
                border: 'none',
                padding: '6px 14px',
                borderRadius: '8px',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              🚨 Trigger Pump B Scenario
            </button>
          </div>
        </div>

        {/* Message Log */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px'
        }}>
          {messages.map((msg) => (
            <div
              key={msg.id}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '85%',
                alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start'
              }}
            >
              <div style={{
                fontSize: '11px',
                color: '#6b7280',
                marginBottom: '4px',
                padding: '0 4px'
              }}>
                {msg.sender === 'user' ? 'Junior Tech / Operator' : 'Master Orchestrator AI'} • {msg.timestamp}
              </div>

              <div style={{
                background: msg.sender === 'user' ? '#2563eb' : '#1e293b',
                color: '#ffffff',
                padding: '14px 18px',
                borderRadius: '16px',
                borderTopRightRadius: msg.sender === 'user' ? '4px' : '16px',
                borderTopLeftRadius: msg.sender === 'assistant' ? '4px' : '16px',
                fontSize: '14px',
                lineHeight: '1.6',
                whiteSpace: 'pre-wrap',
                boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)'
              }}>
                {msg.text}
              </div>

              {/* Inline Rendered MCP Widgets */}
              {msg.widgets && (
                <div style={{
                  marginTop: '12px',
                  width: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px'
                }}>
                  {msg.widgets.map((w, idx) => (
                    <div key={idx} style={{
                      background: '#0f172a',
                      borderRadius: '16px',
                      padding: '16px',
                      border: '1px solid #334155'
                    }}>
                      {w.type === 'ast' && (
                        <div>
                          <div style={{ fontSize: '13px', fontWeight: 700, color: '#60a5fa', marginBottom: '8px' }}>
                            ⚡ Structured JSON AST Rule
                          </div>
                          <div style={{ background: '#1e293b', padding: '12px', borderRadius: '8px', fontFamily: 'monospace', fontSize: '12px' }}>
                            <div><strong>Operator:</strong> {w.data.operator}</div>
                            <div><strong>Action:</strong> <span style={{ color: '#ef4444' }}>{w.data.action}</span></div>
                            <div style={{ marginTop: '6px' }}><strong>Conditions:</strong></div>
                            {w.data.conditions.map((c: any, i: number) => (
                              <div key={i} style={{ paddingLeft: '12px', color: '#fbbf24' }}>
                                • {c.parameter} {c.operator} {c.threshold}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {w.type === 'mentor' && (
                        <div>
                          <div style={{ fontSize: '13px', fontWeight: 700, color: '#ef4444', marginBottom: '8px' }}>
                            🚨 Emergency Guidance Card
                          </div>
                          <div style={{ background: '#7f1d1d', padding: '12px', borderRadius: '8px', fontSize: '12px', color: '#fef2f2' }}>
                            <div><strong>STATUS:</strong> {w.data.scenario}</div>
                            <div style={{ marginTop: '6px', fontWeight: 700 }}>ACTION: EMERGENCY SHUTDOWN PUMP B IMMEDIATELY</div>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}

          {isProcessing && (
            <div style={{ color: '#60a5fa', fontSize: '13px', fontStyle: 'italic' }}>
              ⚡ Master Orchestrator executing 7-step pipeline...
            </div>
          )}
        </div>

        {/* Input Bar */}
        <div style={{
          padding: '16px 24px',
          borderTop: '1px solid #1f2937',
          background: '#090d16',
          display: 'flex',
          gap: '12px'
        }}>
          <input
            type="text"
            value={inputPrompt}
            onChange={(e) => setInputPrompt(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Type your scenario or ask Master Orchestrator..."
            style={{
              flex: 1,
              background: '#1f2937',
              border: '1px solid #374151',
              borderRadius: '10px',
              padding: '12px 16px',
              color: '#ffffff',
              fontSize: '14px',
              outline: 'none'
            }}
          />
          <button
            onClick={() => handleSend()}
            style={{
              background: '#2563eb',
              color: '#ffffff',
              border: 'none',
              padding: '12px 24px',
              borderRadius: '10px',
              fontWeight: 600,
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Send
          </button>
        </div>
      </div>

      {/* RIGHT SIDEBAR: Live Rules & Telemetry Overview */}
      <div style={{
        width: '320px',
        background: '#111827',
        borderLeft: '1px solid #1f2937',
        padding: '20px',
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px'
      }}>
        <div>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: 700, color: '#f3f4f6' }}>
            📜 Active Tacit Rule Registry
          </h3>
          <div style={{
            background: '#1f2937',
            padding: '12px',
            borderRadius: '10px',
            borderLeft: '4px solid #3b82f6',
            fontSize: '12px'
          }}>
            <div style={{ fontWeight: 700, color: '#60a5fa', marginBottom: '4px' }}>RULE_BEARING_001</div>
            <div style={{ color: '#d1d5db' }}>IF Vibration &gt; 4.5 mm/s AND Temp &gt; 90°C THEN Shutdown</div>
            <div style={{ marginTop: '8px', color: '#10b981', fontWeight: 600 }}>Status: Grounded & Validated</div>
          </div>
        </div>

        <div>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: 700, color: '#f3f4f6' }}>
            🗄️ Neon PostgreSQL Status
          </h3>
          <div style={{
            background: '#1f2937',
            padding: '12px',
            borderRadius: '10px',
            fontSize: '12px',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#9ca3af' }}>Table:</span>
              <span style={{ fontFamily: 'monospace' }}>sensor_readings</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#9ca3af' }}>Machine:</span>
              <span style={{ fontWeight: 600, color: '#3b82f6' }}>MACHINE-B</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#9ca3af' }}>Max Recorded Vibration:</span>
              <span style={{ color: '#f59e0b', fontWeight: 600 }}>3.32 mm/s</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#9ca3af' }}>Max Recorded Temp:</span>
              <span style={{ color: '#f59e0b', fontWeight: 600 }}>83.69°C</span>
            </div>
          </div>
        </div>

        <div>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: 700, color: '#f3f4f6' }}>
            ⚡ Express / NitroStack Services
          </h3>
          <div style={{
            background: '#1f2937',
            padding: '12px',
            borderRadius: '10px',
            fontSize: '12px',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px'
          }}>
            <div><strong>Streamable MCP:</strong> <code>http://localhost:3000/mcp</code></div>
            <div><strong>Legacy SSE:</strong> <code>http://localhost:3000/sse</code></div>
            <div><strong>Widgets Endpoint:</strong> <code>http://localhost:3000/widgets</code></div>
          </div>
        </div>
      </div>
    </div>
  );
}
