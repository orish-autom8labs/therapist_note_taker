import React from 'react';
import { clearRecoveryData } from '../services/recoveryService';

function RecoveryDialog({ data, onRecover, onDiscard }) {
  const handleRecover = () => {
    onRecover(data);
    clearRecoveryData();
  };

  const handleDiscard = () => {
    onDiscard();
    clearRecoveryData();
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleString('he-IL');
  };

  const duration = data.timestamp ? 
    Math.round((Date.now() - data.timestamp) / 1000 / 60) : 0;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        background: 'white',
        borderRadius: '12px',
        padding: '30px',
        maxWidth: '500px',
        width: '90%',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)'
      }}>
        <h2 style={{ marginBottom: '20px' }}>⚠️ Unsaved Session Found</h2>
        
        <p style={{ marginBottom: '20px' }}>
          Found an unsaved session from {formatTime(data.timestamp)}.
        </p>

        <div style={{
          background: '#ECF0F1',
          padding: '15px',
          borderRadius: '8px',
          marginBottom: '20px',
          fontSize: '14px'
        }}>
          <strong>Patient:</strong> {data.patientName}<br />
          <strong>Duration:</strong> {duration} minutes<br />
          <strong>Transcript length:</strong> {data.transcript?.length || 0} segments
        </div>

        <div className="button-group">
          <button className="btn-secondary" onClick={handleDiscard}>
            Discard
          </button>
          <button className="btn-primary" onClick={handleRecover}>
            Recover Session
          </button>
        </div>
      </div>
    </div>
  );
}

export default RecoveryDialog;




