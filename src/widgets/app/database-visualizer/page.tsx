'use client';

import { useTheme, useWidgetSDK } from '@nitrostack/widgets';

interface DatabaseVisualizerData {
  query: string;
  columns: string[];
  rows: any[];
}

export default function DatabaseVisualizer() {
  const theme = useTheme();
  const { getToolOutput } = useWidgetSDK();
  const data = getToolOutput<DatabaseVisualizerData>();

  if (!data) {
    return (
      <div style={{
        padding: '24px',
        textAlign: 'center',
        color: theme === 'dark' ? '#fff' : '#000',
      }}>
        Executing Query...
      </div>
    );
  }

  const isDark = theme === 'dark';
  const bgColor = isDark ? '#1a1a1a' : '#ffffff';
  const textColor = isDark ? '#ffffff' : '#000000';
  const headerBg = isDark ? '#2d3748' : '#e2e8f0';
  const borderColor = isDark ? '#4a5568' : '#cbd5e0';

  return (
    <div style={{
      padding: '24px',
      background: bgColor,
      color: textColor,
      borderRadius: '16px',
      boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      width: '100%',
      maxWidth: '100%',
      overflowX: 'hidden'
    }}>
      <div style={{ marginBottom: '16px' }}>
        <h3 style={{ margin: '0 0 8px 0', fontSize: '18px', color: '#3b82f6' }}>
          🗄️ Database Query Result
        </h3>
        <div style={{
          background: isDark ? '#2d3748' : '#edf2f7',
          padding: '12px',
          borderRadius: '8px',
          fontFamily: 'monospace',
          fontSize: '13px',
          color: isDark ? '#a0aec0' : '#4a5568',
          borderLeft: '4px solid #3b82f6'
        }}>
          {data.query}
        </div>
      </div>

      <div style={{
        overflowX: 'auto',
        borderRadius: '8px',
        border: `1px solid ${borderColor}`,
        maxHeight: '400px',
        overflowY: 'auto'
      }}>
        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '14px'
        }}>
          <thead style={{ position: 'sticky', top: 0, zIndex: 1 }}>
            <tr>
              {data.columns.map((col, i) => (
                <th key={i} style={{
                  background: headerBg,
                  padding: '12px 16px',
                  textAlign: 'left',
                  fontWeight: 600,
                  borderBottom: `2px solid ${borderColor}`,
                  color: isDark ? '#e2e8f0' : '#2d3748'
                }}>
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.rows.length === 0 ? (
              <tr>
                <td colSpan={data.columns.length} style={{ padding: '24px', textAlign: 'center', color: isDark ? '#a0aec0' : '#718096' }}>
                  No rows returned
                </td>
              </tr>
            ) : (
              data.rows.map((row, i) => (
                <tr key={i} style={{
                  borderBottom: `1px solid ${borderColor}`,
                  background: isDark 
                    ? (i % 2 === 0 ? '#1a202c' : '#2d3748') 
                    : (i % 2 === 0 ? '#ffffff' : '#f7fafc')
                }}>
                  {data.columns.map((col, j) => (
                    <td key={j} style={{
                      padding: '10px 16px',
                      whiteSpace: 'nowrap',
                      maxWidth: '300px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }}>
                      {String(row[col])}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      
      <div style={{
        marginTop: '12px',
        fontSize: '12px',
        textAlign: 'right',
        color: isDark ? '#a0aec0' : '#718096'
      }}>
        Showing {data.rows.length} rows
      </div>
    </div>
  );
}
