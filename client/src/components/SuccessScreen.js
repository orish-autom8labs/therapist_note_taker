import React from 'react';
import useSummaryPolling from '../hooks/useSummaryPolling';

function SuccessScreen({ fileInfo, sessionId, onNewSession }) {
  const { status, summary, error: pollError, isPolling } = useSummaryPolling(sessionId);

  const handleViewTranscript = () => {
    // Support both camelCase (from frontend) and snake_case (from backend)
    const webViewLink = fileInfo?.webViewLink || fileInfo?.web_view_link;
    if (webViewLink) {
      window.open(webViewLink, '_blank');
    } else {
      console.error('No webViewLink available:', fileInfo);
    }
  };

  const handleViewSummary = () => {
    if (summary?.webViewLink) {
      window.open(summary.webViewLink, '_blank');
    }
  };

  // Check if View Transcript button should be enabled
  const hasTranscriptLink = !!(fileInfo?.webViewLink || fileInfo?.web_view_link);
  const hasSummaryLink = !!(summary?.webViewLink);

  // Determine summary status display
  const isSummarizing = status === 'summarizing' || status === 'transcript_saved' || isPolling && !hasSummaryLink && !pollError;
  const summaryFailed = status === 'summarization_failed';
  const summaryReady = status === 'completed' && hasSummaryLink;
  const summaryTimeout = status === 'timeout';

  return (
    <div className="container">
      <div style={{
        textAlign: 'center',
        fontSize: '64px',
        color: '#27AE60',
        marginBottom: '20px'
      }}>
        &#10003;
      </div>
      <h2 style={{ textAlign: 'center' }}>Session Saved!</h2>

      <p style={{ textAlign: 'center', margin: '20px 0' }}>
        Transcript saved to Google Drive
      </p>

      {fileInfo && (
        <div style={{
          background: '#ECF0F1',
          padding: '15px',
          borderRadius: '8px',
          margin: '20px 0',
          fontFamily: 'monospace',
          fontSize: '14px'
        }}>
          <strong>File:</strong> {fileInfo.fileName || fileInfo.name}<br />
          <strong>Location:</strong> Clinic/Transcripts
        </div>
      )}

      {/* Summary Status */}
      {sessionId && (
        <div style={{
          padding: '15px',
          borderRadius: '8px',
          margin: '20px 0',
          background: summaryReady ? '#D5F5E3' : summaryFailed ? '#FADBD8' : '#D6EAF8',
          textAlign: 'center',
        }}>
          {isSummarizing && (
            <div style={{ color: '#2980B9' }}>
              <div style={{
                display: 'inline-block',
                width: '16px',
                height: '16px',
                border: '3px solid #2980B9',
                borderTop: '3px solid transparent',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite',
                marginRight: '10px',
                verticalAlign: 'middle',
              }} />
              Generating summary...
            </div>
          )}
          {summaryReady && (
            <div style={{ color: '#27AE60', fontWeight: '600' }}>
              Summary ready!
            </div>
          )}
          {summaryFailed && (
            <div style={{ color: '#C0392B' }}>
              Summary generation failed. Check Drive folder later.
              {pollError && <div style={{ fontSize: '12px', marginTop: '5px', opacity: 0.8 }}>{pollError}</div>}
            </div>
          )}
          {summaryTimeout && (
            <div style={{ color: '#7F8C8D' }}>
              Summary is taking longer than expected. Check your Drive folder later.
            </div>
          )}
        </div>
      )}

      <div className="button-group" style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
        <button className="btn-secondary" onClick={onNewSession}>
          New Session
        </button>
        <button
          className="btn-primary"
          onClick={handleViewTranscript}
          disabled={!hasTranscriptLink}
          style={{
            opacity: hasTranscriptLink ? 1 : 0.5,
            cursor: hasTranscriptLink ? 'pointer' : 'not-allowed'
          }}
        >
          View Transcript
        </button>
        <button
          className="btn-primary"
          onClick={handleViewSummary}
          disabled={!hasSummaryLink}
          style={{
            opacity: hasSummaryLink ? 1 : 0.5,
            cursor: hasSummaryLink ? 'pointer' : 'not-allowed',
            background: hasSummaryLink ? '#8E44AD' : undefined,
          }}
        >
          View Summary
        </button>
      </div>

      {/* CSS for spinner animation */}
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default SuccessScreen;
