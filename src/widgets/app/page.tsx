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
      text: '👋 Welcome to **Continuum Forge** — Tacit Knowledge Capture & Transfer Engine.\n\nI can help you codify expert rules of thumb into Structured JSON ASTs, validate them against your Neon PostgreSQL sensor telemetry, and provide instant coaching to junior operators.',
      timestamp: '10:00 AM'
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
          '✅ **Codification & Rule Generation**: Expert heuristic codified into Structured JSON AST.\n' +
          '📊 **Database Validation**: Evaluated 20 historical sensor readings on `MACHINE-B`. No prior incidents exceeded both thresholds simultaneously.\n\n' +
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
              scenario: 'Vibration: 5.0 mm/s (EXCEEDS 4.5) | Temp: 95°C (EXCEEDS 90°C)',
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
      background: 'linear-gradient(135deg, #090d16 0%, #0f172a 100%)',
      color: '#f8fafc',
      fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
      overflow: 'hidden'
    }}>
      {/* LEFT SIDEBAR: Pipeline & System Navigation */}
      <div style={{
        width: '300px',
        background: 'rgba(15, 23, 42, 0.75)',
        backdropFilter: 'blur(16px)',
        borderRight: '1px solid rgba(255, 255, 255, 0.08)',
        display: 'flex',
        flexDirection: 'column',
        padding: '24px',
        boxSizing: 'border-box'
      }}>
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '28px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
            display: 'flex',
            alignItems: 'center',
            justify: 'center',
            fontWeight: 800,
            fontSize: '22px',
            boxShadow: '0 8px 16px rgba(59, 130, 246, 0.3)'
          }}>
            ⚡
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: '17px', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.02em' }}>
              CONTINUUM FORGE
            </h1>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '2px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', display: 'inline-block', boxShadow: '0 0 8px #10b981' }}></span>
              <span style={{ fontSize: '11px', color: '#34d399', fontWeight: 600 }}>NitroStack MCP Live</span>
            </div>
          </div>
        </div>

        {/* Pipeline Steps Tracker */}
        <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '14px' }}>
          7-Step Knowledge Pipeline
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '24px' }}>
          {[
            { step: '1', title: 'Grounding Interview', status: 'ACTIVE' },
            { step: '2', title: 'Codification (JSON AST)', status: 'ACTIVE' },
            { step: '3', title: 'Parameter Extraction', status: 'ACTIVE' },
            { step: '4', title: 'Database Validation', status: 'ACTIVE' },
            { step: '5', title: 'Explainability Engine', status: 'ACTIVE' },
            { step: '6', title: 'Rule Codification', status: 'ACTIVE' },
            { step: '7', title: 'Mentor Coaching', status: 'ACTIVE' }
          ].map((item) => (
            <div key={item.step} style={{
              display: 'flex',
              alignItems: 'center',
              justify: 'space-between',
              padding: '10px 14px',
              borderRadius: '10px',
              background: 'rgba(30, 41, 59, 0.4)',
              border: '1px solid rgba(255, 255, 255, 0.05)',
              fontSize: '13px',
              transition: 'all 0.2s ease'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{
                  width: '22px',
                  height: '22px',
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #2563eb, #3b82f6)',
                  color: '#fff',
                  fontSize: '11px',
                  display: 'flex',
                  alignItems: 'center',
                  justify: 'center',
                  fontWeight: 700
                }}>{item.step}</span>
                <span style={{ color: '#e2e8f0', fontWeight: 500 }}>{item.title}</span>
              </div>
              <span style={{ fontSize: '10px', fontWeight: 700, color: '#34d399', background: 'rgba(16, 185, 129, 0.1)', padding: '2px 6px', borderRadius: '4px' }}>
                {item.status}
              </span>
            </div>
          ))}
        </div>

        {/* Observability Box */}
        <div style={{ marginTop: 'auto', paddingTop: '18px', borderTop: '1px solid rgba(255, 255, 255, 0.08)' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '10px' }}>
            Observability Telemetry
          </div>
          <a
            href="https://jp.cloud.langfuse.com"
            target="_blank"
            rel="noreferrer"
            style={{
              display: 'flex',
              alignItems: 'center',
              justify: 'space-between',
              color: '#93c5fd',
              textDecoration: 'none',
              fontSize: '13px',
              fontWeight: 600,
              padding: '12px 16px',
              background: 'rgba(30, 41, 59, 0.6)',
              borderRadius: '12px',
              border: '1px solid rgba(147, 197, 253, 0.2)',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)'
            }}
          >
            <span>📊 Langfuse Traces</span>
            <span style={{ fontSize: '14px' }}>↗</span>
          </a>
        </div>
      </div>

      {/* CENTER AREA: Main Chat Dashboard */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        background: 'rgba(11, 17, 32, 0.95)',
        position: 'relative'
      }}>
        {/* Top Navigation Bar */}
        <div style={{
          height: '70px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          alignItems: 'center',
          justify: 'space-between',
          padding: '0 28px',
          background: 'rgba(15, 23, 42, 0.8)',
          backdropFilter: 'blur(12px)'
        }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: '#ffffff' }}>
              Master Orchestrator Assistant
            </h2>
            <span style={{ fontSize: '12px', color: '#94a3b8' }}>
              Industrial Telemetry & Expert Rules Engine
            </span>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={() => runScenario("Run master orchestrator for Pump B burnout: Vibration > 4.5 mm/s, Temp > 90C. Current: 5.0 mm/s and 95C.")}
              style={{
                background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                color: '#ffffff',
                border: 'none',
                padding: '10px 18px',
                borderRadius: '10px',
                fontSize: '13px',
                fontWeight: 700,
                cursor: 'pointer',
                boxShadow: '0 4px 14px rgba(239, 68, 68, 0.4)',
                transition: 'transform 0.1s ease'
              }}
            >
              🚨 Trigger Pump B Scenario
            </button>
          </div>
        </div>

        {/* Chat History */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '28px',
          display: 'flex',
          flexDirection: 'column',
          gap: '24px'
        }}>
          {messages.map((msg) => (
            <div
              key={msg.id}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '82%',
                alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start'
              }}
            >
              <div style={{
                fontSize: '11px',
                color: '#64748b',
                marginBottom: '6px',
                padding: '0 4px',
                fontWeight: 600
              }}>
                {msg.sender === 'user' ? 'Operator' : 'Master Orchestrator AI'} • {msg.timestamp}
              </div>

              {/* Message Bubble */}
              <div style={{
                background: msg.sender === 'user'
                  ? 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)'
                  : 'rgba(30, 41, 59, 0.8)',
                color: '#ffffff',
                padding: '16px 20px',
                borderRadius: '18px',
                borderTopRightRadius: msg.sender === 'user' ? '4px' : '18px',
                borderTopLeftRadius: msg.sender === 'assistant' ? '4px' : '18px',
                fontSize: '14px',
                lineHeight: '1.65',
                whiteSpace: 'pre-wrap',
                border: msg.sender === 'assistant' ? '1px solid rgba(255, 255, 255, 0.08)' : 'none',
                boxShadow: msg.sender === 'user'
                  ? '0 6px 16px rgba(37, 99, 235, 0.3)'
                  : '0 6px 16px rgba(0, 0, 0, 0.2)'
              }}>
                {msg.text}
              </div>

              {/* Inline Rendered MCP Widgets */}
              {msg.widgets && (
                <div style={{
                  marginTop: '16px',
                  width: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '16px'
                }}>
                  {msg.widgets.map((w, idx) => (
                    <div key={idx} style={{
                      background: 'linear-gradient(145deg, #0f172a 0%, #1e1b4b 100%)',
                      borderRadius: '18px',
                      padding: '20px',
                      border: '1px solid rgba(99, 102, 241, 0.3)',
                      boxShadow: '0 12px 24px -6px rgba(0, 0, 0, 0.4)'
                    }}>
                      {w.type === 'ast' && (
                        <div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                            <div style={{ fontSize: '14px', fontWeight: 700, color: '#93c5fd' }}>
                              ⚡ Structured JSON AST Rule
                            </div>
                            <span style={{ background: '#ef4444', color: '#fff', fontSize: '11px', padding: '3px 10px', borderRadius: '12px', fontWeight: 800 }}>
                              {w.data.action}
                            </span>
                          </div>
                          <div style={{ background: 'rgba(15, 23, 42, 0.8)', padding: '14px', borderRadius: '12px', fontFamily: "'JetBrains Mono', monospace", fontSize: '13px' }}>
                            <div style={{ color: '#a5b4fc', marginBottom: '8px' }}>Operator: <strong>{w.data.operator}</strong></div>
                            {w.data.conditions.map((c: any, i: number) => (
                              <div key={i} style={{ color: '#fbbf24', margin: '4px 0' }}>
                                • {c.parameter} {c.operator} <strong>{c.threshold}</strong>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {w.type === 'mentor' && (
                        <div>
                          <div style={{ fontSize: '14px', fontWeight: 700, color: '#fca5a5', marginBottom: '10px' }}>
                            🚨 Critical Operational Guidance
                          </div>
                          <div style={{ background: 'linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%)', padding: '16px', borderRadius: '12px', fontSize: '13px', color: '#ffffff' }}>
                            <div style={{ fontSize: '12px', opacity: 0.9, marginBottom: '6px' }}>{w.data.scenario}</div>
                            <div style={{ fontWeight: 800, fontSize: '14px', marginTop: '8px' }}>
                              ACTION: EMERGENCY SHUTDOWN PUMP-B IMMEDIATELY
                            </div>
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
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#60a5fa', fontSize: '13px', fontWeight: 600 }}>
              <span style={{ animation: 'spin 1s linear infinite' }}>⚡</span>
              Master Orchestrator executing 7-step tacit knowledge pipeline...
            </div>
          )}
        </div>

        {/* Bottom Input Console */}
        <div style={{
          padding: '20px 28px',
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          background: 'rgba(15, 23, 42, 0.8)',
          backdropFilter: 'blur(12px)',
          display: 'flex',
          gap: '14px'
        }}>
          <input
            type="text"
            value={inputPrompt}
            onChange={(e) => setInputPrompt(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask Master Orchestrator or run pipeline..."
            style={{
              flex: 1,
              background: 'rgba(30, 41, 59, 0.6)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '12px',
              padding: '14px 20px',
              color: '#ffffff',
              fontSize: '14px',
              outline: 'none',
              fontFamily: 'inherit'
            }}
          />
          <button
            onClick={() => handleSend()}
            style={{
              background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
              color: '#ffffff',
              border: 'none',
              padding: '14px 28px',
              borderRadius: '12px',
              fontWeight: 700,
              cursor: 'pointer',
              fontSize: '14px',
              boxShadow: '0 4px 14px rgba(37, 99, 235, 0.4)'
            }}
          >
            Send Prompt
          </button>
        </div>
      </div>

      {/* RIGHT SIDEBAR: Tacit Rules & DB Metrics */}
      <div style={{
        width: '340px',
        background: 'rgba(15, 23, 42, 0.75)',
        backdropFilter: 'blur(16px)',
        borderLeft: '1px solid rgba(255, 255, 255, 0.08)',
        padding: '24px',
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        gap: '24px'
      }}>
        <div>
          <h3 style={{ margin: '0 0 14px 0', fontSize: '14px', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.01em' }}>
            📜 Active Tacit Rule Registry
          </h3>
          <div style={{
            background: 'rgba(30, 41, 59, 0.6)',
            padding: '14px',
            borderRadius: '14px',
            borderLeft: '4px solid #3b82f6',
            border: '1px solid rgba(255, 255, 255, 0.06)',
            fontSize: '12px'
          }}>
            <div style={{ fontWeight: 800, color: '#93c5fd', marginBottom: '4px' }}>RULE_BEARING_001</div>
            <div style={{ color: '#cbd5e1', lineHeight: '1.4' }}>IF Vibration &gt; 4.5 mm/s AND Temp &gt; 90°C THEN Shutdown</div>
            <div style={{ marginTop: '10px', color: '#34d399', fontWeight: 700 }}>● Grounded & Validated</div>
          </div>
        </div>

        <div>
          <h3 style={{ margin: '0 0 14px 0', fontSize: '14px', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.01em' }}>
            🗄️ Neon PostgreSQL Telemetry
          </h3>
          <div style={{
            background: 'rgba(30, 41, 59, 0.6)',
            padding: '16px',
            borderRadius: '14px',
            border: '1px solid rgba(255, 255, 255, 0.06)',
            fontSize: '12px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#94a3b8' }}>Target Table:</span>
              <span style={{ fontFamily: "'JetBrains Mono', monospace", color: '#e2e8f0' }}>sensor_readings</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#94a3b8' }}>Equipment ID:</span>
              <span style={{ fontWeight: 700, color: '#60a5fa' }}>MACHINE-B</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#94a3b8' }}>Max Recorded Vibration:</span>
              <span style={{ color: '#fbbf24', fontWeight: 700, fontFamily: "'JetBrains Mono', monospace" }}>3.32 mm/s</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#94a3b8' }}>Max Recorded Temp:</span>
              <span style={{ color: '#fbbf24', fontWeight: 700, fontFamily: "'JetBrains Mono', monospace" }}>83.69°C</span>
            </div>
          </div>
        </div>

        <div>
          <h3 style={{ margin: '0 0 14px 0', fontSize: '14px', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.01em' }}>
            ⚡ Server Transports
          </h3>
          <div style={{
            background: 'rgba(30, 41, 59, 0.6)',
            padding: '14px',
            borderRadius: '14px',
            border: '1px solid rgba(255, 255, 255, 0.06)',
            fontSize: '12px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px'
          }}>
            <div><strong style={{ color: '#a5b4fc' }}>Streamable MCP:</strong> <code style={{ color: '#38bdf8' }}>:3000/mcp</code></div>
            <div><strong style={{ color: '#a5b4fc' }}>Widgets Bundle:</strong> <code style={{ color: '#38bdf8' }}>:3001</code></div>
          </div>
        </div>
      </div>
    </div>
  );
}
