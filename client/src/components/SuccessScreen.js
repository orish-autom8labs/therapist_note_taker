import React from 'react';

function SuccessScreen({ fileInfo, onNewSession }) {
  const handleViewInDrive = () => {
    // Support both camelCase (from frontend) and snake_case (from backend)
    const webViewLink = fileInfo?.webViewLink || fileInfo?.web_view_link;
    if (webViewLink) {
      window.open(webViewLink, '_blank');
    } else {
      console.error('No webViewLink available:', fileInfo);
    }
  };
  
  // Check if View in Drive button should be enabled
  const hasDriveLink = !!(fileInfo?.webViewLink || fileInfo?.web_view_link);

  return (
    <div className="container">
      <div style={{
        textAlign: 'center',
        fontSize: '64px',
        color: '#27AE60',
        marginBottom: '20px'
      }}>
        ✓
      </div>
      <h2 style={{ textAlign: 'center' }}>Session Saved!</h2>
      
      <p style={{ textAlign: 'center', margin: '20px 0' }}>
        Transcript saved to Google Drive<br />
        Email notification sent
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
          <strong>File:</strong> {fileInfo.fileName}<br />
          <strong>Location:</strong> Clinic/Transcripts
        </div>
      )}

      <div className="button-group">
        <button className="btn-secondary" onClick={onNewSession}>
          New Session
        </button>
        <button 
          className="btn-primary" 
          onClick={handleViewInDrive}
          disabled={!hasDriveLink}
          style={{
            opacity: hasDriveLink ? 1 : 0.5,
            cursor: hasDriveLink ? 'pointer' : 'not-allowed'
          }}
        >
          View in Drive
        </button>
      </div>
    </div>
  );
}

export default SuccessScreen;

