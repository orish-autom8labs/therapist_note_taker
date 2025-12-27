import React, { useState } from 'react';

function SessionSetup({ user, onStart, onBack }) {
  const [patientName, setPatientName] = useState('');

  const handleStart = () => {
    if (!patientName.trim()) {
      alert('Please enter a patient name');
      return;
    }

    onStart({
      patientName: patientName.trim(),
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
        📁 Save to: <strong>Clinic/Transcripts</strong>
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




