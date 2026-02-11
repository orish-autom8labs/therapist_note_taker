import React, { useState } from 'react';

function SessionSetup({ user, onStart, onBack }) {
  const [patientName, setPatientName] = useState('');
  const [includeTimestamps, setIncludeTimestamps] = useState(false);

  const handleStart = () => {
    if (!patientName.trim()) {
      alert('Please enter a patient name');
      return;
    }

    onStart({
      patientName: patientName.trim(),
      includeTimestamps,
      user,
    });
  };

  return (
    <div className="container">
      <div className="header">
        <a className="back-link" onClick={onBack}>← Logout</a>
        <h2>Note Taker</h2>
      </div>

      <h2>New Session</h2>

      <label>Patient Name:</label>
      <input
        type="text"
        value={patientName}
        onChange={(e) => setPatientName(e.target.value)}
        placeholder="הכנס שם מטופל..."
        autoFocus
      />

      <div style={{
        background: '#ECF0F1',
        padding: '15px',
        borderRadius: '8px',
        marginBottom: '20px',
        fontSize: '14px'
      }}>
        📁 Save to: <strong>Clinic/Transcripts/{patientName.trim() || 'PatientName'}</strong>
      </div>

      <label style={{
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        marginBottom: '20px',
        fontSize: '14px',
        cursor: 'pointer',
      }}>
        <input
          type="checkbox"
          checked={includeTimestamps}
          onChange={(e) => setIncludeTimestamps(e.target.checked)}
          style={{ width: '18px', height: '18px', cursor: 'pointer' }}
        />
        זמנים תכופים בתמלול (כל 1-2 דקות)
      </label>

      {/* Important Instructions for Screen Lock */}
      <div style={{
        background: '#fff3cd',
        border: '2px solid #ffc107',
        padding: '15px',
        borderRadius: '8px',
        marginBottom: '20px',
        fontSize: '14px',
        lineHeight: '1.6'
      }}>
        <div style={{ fontWeight: 'bold', marginBottom: '10px', color: '#856404' }}>
          📱 Important: Keep Your Screen On During Recording
        </div>
        <ul style={{ margin: '0', paddingLeft: '20px', color: '#856404' }}>
          <li>Do not lock your phone manually</li>
          <li>Do not switch to other apps</li>
          <li>Keep this screen visible during the entire session</li>
          <li>Your screen will stay on automatically</li>
        </ul>
      </div>

      <button
        className="btn-primary"
        onClick={handleStart}
        disabled={!patientName.trim()}
      >
        Start Session
      </button>
    </div>
  );
}

export default SessionSetup;




